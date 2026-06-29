#!/usr/bin/env python3
r"""
runtime-common/wf-runtime-full.py — 运行时检测+下载整体 Workflow（v1.0.0）
标签：wf, runtime
职责：检测工具链状态 → 对 outdated 工具自动下载，全程带进度条

用法：
    python wf-runtime-full.py --devroot "D:\\pjt\\vscode\\vsc_py" --tools node,opencode_cli
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log(msg: str):
    print(f"[{ts()}] {msg}", flush=True)


def run_atomic_capture_json(script_path: str, args: list, timeout: int = 120) -> dict:
    """调用原子脚本，捕获 stdout 最后一行 JSON，stderr 透传"""
    python_exe = sys.executable
    cmd = [python_exe, script_path] + args
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=timeout)
    lines = result.stdout.strip().splitlines()
    if not lines:
        return {"error": "无输出"}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"error": f"输出不是 JSON: {lines[-1][:100]}"}


def download_with_progress(url: str, out_file: str, proxy: str, timeout: int = 600) -> dict:
    """调用下载原子，stderr 透传以显示进度条"""
    python_exe = sys.executable
    script = Path(__file__).parent.parent / "download-runtime" / "atomic-02-download-file.py"
    args = [python_exe, str(script), "--url", url, "--out-file", out_file, "--proxy", proxy, "--show-progress"]
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=None,
                            text=True, encoding="utf-8", errors="replace", timeout=timeout)
    lines = result.stdout.strip().splitlines()
    if not lines:
        return {"success": False, "error": "无输出"}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"success": False, "error": f"输出不是 JSON: {lines[-1][:100]}"}


def get_paths(devroot: str) -> dict:
    root = Path(devroot)
    return {
        "devroot": str(root),
        "tools_config": str(root / "references" / "runtime" / "runtime_config" / "tools_config.json"),
        "index_path": str(root / "references" / "runtime" / "verified-runtime-index.json"),
        "get_version_script": str(root / "schema" / "tool" / "get-runtime-version.py"),
        "common_dir": str(Path(__file__).parent),
        "download_dir": "D:\\download",
    }


def load_tools(config_path: str, names: list) -> list:
    with open(config_path, "r", encoding="utf-8") as f:
        tools = json.load(f).get("tools", [])
    if names:
        return [t for t in tools if t["name"] in names]
    return tools


def detect_tool(paths: dict, tool: dict) -> dict:
    local_cfg = tool.get("local", {})
    return run_atomic_capture_json(
        os.path.join(paths["common_dir"], "atomic-detect-local.py"),
        ["--config-json", json.dumps(local_cfg, ensure_ascii=False),
         "--devroot", paths["devroot"],
         "--tool-name", tool["name"],
         "--index-path", paths["index_path"],
         "--get-version-script", paths["get_version_script"]]
    )


def query_upstream(tool: dict) -> dict:
    upstream_cfg = tool.get("upstream", {})
    if not upstream_cfg.get("enabled", True):
        return {"disabled": True, "reason": upstream_cfg.get("reason", "上游查询已禁用")}
    return run_atomic_capture_json(
        os.path.join(Path(__file__).parent, "atomic-query-upstream.py"),
        ["--tool-name", tool["name"],
         "--query-param", upstream_cfg.get("query_param", tool["name"]),
         "--target-version", upstream_cfg.get("target_version", "")]
    )


def compare_versions(local_ver: str, upstream_ver: str) -> dict:
    return run_atomic_capture_json(
        os.path.join(Path(__file__).parent, "atomic-compare-version.py"),
        ["--local-ver", local_ver or "", "--upstream-ver", upstream_ver or ""]
    )


def probe_route(url: str, proxy: str = "") -> dict:
    return run_atomic_capture_json(
        os.path.join(Path(__file__).parent.parent, "download-runtime", "atomic-01-route-probe.py"),
        ["--url", url, "--proxy", proxy]
    )


def extract_verify(zip_file: str, tool_name: str, config_json: str, devroot: str, get_version_script: str) -> dict:
    return run_atomic_capture_json(
        os.path.join(Path(__file__).parent.parent, "download-runtime", "atomic-03-extract-verify.py"),
        ["--zip-file", zip_file, "--tool-name", tool_name,
         "--config-json", config_json, "--devroot", devroot,
         "--get-version-script", get_version_script]
    )


def main():
    parser = argparse.ArgumentParser(description="运行时检测+下载整体 Workflow")
    parser.add_argument("--devroot", required=True, help="devroot 绝对路径")
    parser.add_argument("--tools", default="", help="逗号分隔的工具名，如 node,opencode_cli")
    parser.add_argument("--force", "-f", action="store_true", help="强制下载（忽略版本对比）")
    args = parser.parse_args()

    paths = get_paths(args.devroot)
    tool_names = [n.strip() for n in args.tools.split(",") if n.strip()] if args.tools else []
    tools = load_tools(paths["tools_config"], tool_names)

    if not tools:
        log("[ERROR] 未发现需要检测的工具")
        sys.exit(1)

    log("=" * 60)
    log("[wf-runtime-full] 检测+下载 Workflow")
    log(f"工具列表: {[t['name'] for t in tools]}")
    log("=" * 60)

    need_download = []

    # ===== Phase 1: 检测 =====
    for tool in tools:
        name = tool["name"]
        log(f"\n--- [{name}] 检测 ---")

        local = detect_tool(paths, tool)
        local_ver = local.get("local_version") or local.get("fallback_version")
        exe_exists = local.get("exe_exists", False)
        log(f"  本地: exe_exists={exe_exists}, version={local_ver or 'N/A'}")

        upstream = query_upstream(tool)
        if upstream.get("disabled"):
            log(f"  上游: 已跳过 ({upstream.get('reason')})")
            continue
        upstream_ver = upstream.get("upstream_version")
        asset_url = upstream.get("asset_url", "")
        log(f"  上游: version={upstream_ver or 'N/A'}, source={upstream.get('upstream_source', 'N/A')}")

        compare = compare_versions(local_ver, upstream_ver)
        status = compare.get("status")
        need = compare.get("need_update", False)
        log(f"  对比: {compare.get('message')}, need_update={need}")

        if need or args.force:
            need_download.append({
                "tool": tool,
                "local_ver": local_ver,
                "upstream_ver": upstream_ver,
                "asset_url": asset_url,
                "asset_name": upstream.get("asset_name", f"{name}-{upstream_ver}.zip"),
            })

    # ===== Phase 2: 下载 =====
    if not need_download:
        log("\n所有工具已是最新版，无需下载")
        sys.exit(0)

    log(f"\n{'=' * 60}")
    log(f"需要下载 {len(need_download)} 个工具")
    log(f"{'=' * 60}")

    for item in need_download:
        tool = item["tool"]
        name = tool["name"]
        upstream_ver = item["upstream_ver"]
        asset_url = item["asset_url"]
        asset_name = item["asset_name"]
        zip_file = os.path.join(paths["download_dir"], asset_name)

        log(f"\n--- [{name}] 下载 ({upstream_ver}) ---")

        # 路由探测
        log(f"  [probe] 探测路由 ...")
        route = probe_route(asset_url)
        log(f"  [probe] {route.get('reason')}")
        if route.get("route") == "none":
            log(f"  [FAIL] 无可用路由，跳过")
            continue
        proxy = route.get("proxy", "")

        # 下载（stderr 透传，显示进度条）
        log(f"  [download] 开始下载 -> {zip_file}")
        dl = download_with_progress(asset_url, zip_file, proxy)
        if not dl.get("success"):
            log(f"  [FAIL] 下载失败: {dl.get('error')}")
            continue
        log(f"  [download] 完成: {dl.get('size_mb')} MB, {dl.get('elapsed_sec')}s")

        # 解压验证
        log(f"  [extract] 解压验证 ...")
        cfg = {**tool.get("local", {}), "upstream_version": upstream_ver, "package_type": tool.get("package_type", "")}
        ev = extract_verify(zip_file, name, json.dumps(cfg, ensure_ascii=False), paths["devroot"], paths["get_version_script"])
        if ev.get("error"):
            log(f"  [FAIL] 解压验证失败: {ev.get('error')}")
            continue
        log(f"  [extract] 解压目录: {ev.get('extract_dir')}")
        log(f"  [extract] exe: {ev.get('found_exe')}")
        log(f"  [extract] 版本验证: {ev.get('downloaded_version')}")

    log(f"\n{'=' * 60}")
    log("[wf-runtime-full] 全部完成")
    log(f"{'=' * 60}")
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
