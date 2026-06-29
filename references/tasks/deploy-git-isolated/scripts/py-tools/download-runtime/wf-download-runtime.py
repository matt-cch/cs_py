#!/usr/bin/env python3
r"""
download-runtime/wf-download-runtime.py — 运行时下载 Workflow（v2.0.0）
标签：wf, runtime
职责：编排检测 → 查询 → 对比 → 路由 → 下载 → 解压 → 备份替换 → 清理

用法：
    python wf-download-runtime.py --devroot "D:\\pjt\\vscode\\vsc_py" --tool-name node
    echo "Y" | python wf-download-runtime.py --devroot "D:\\pjt\\vscode\\vsc_py" --tool-name node --force
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def run_atomic(script_path: str, args: list) -> dict:
    python_exe = sys.executable
    cmd = [python_exe, script_path] + args
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    lines = result.stdout.strip().splitlines()
    if not lines:
        return {"error": "无输出"}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"error": f"输出不是 JSON: {lines[-1][:100]}"}


def get_paths(devroot: str) -> dict:
    root = Path(devroot)
    return {
        "devroot": str(root),
        "tools_config": str(root / "references" / "runtime" / "runtime_config" / "tools_config.json"),
        "index_path": str(root / "references" / "runtime" / "verified-runtime-index.json"),
        "get_version_script": str(root / "schema" / "tool" / "get-runtime-version.py"),
        "common_dir": str(Path(__file__).parent.parent / "runtime-common"),
        "atomic_dir": str(Path(__file__).parent),
        "download_dir": "D:\\download",
    }


def load_tool_config(tools_config_path: str, tool_name: str) -> dict:
    with open(tools_config_path, "r", encoding="utf-8") as f:
        tools = json.load(f).get("tools", [])
    for t in tools:
        if t["name"] == tool_name:
            return t
    return None


def main():
    parser = argparse.ArgumentParser(description="运行时下载 Workflow")
    parser.add_argument("--devroot", required=True, help="devroot 绝对路径")
    parser.add_argument("--tool-name", "-t", required=True, help="工具名")
    parser.add_argument("--force", "-f", action="store_true", help="强制下载并替换")
    parser.add_argument("--show-progress", "-p", action="store_true", help="显示下载进度")
    parser.add_argument("--target-version", default="", help="指定目标版本")
    parser.add_argument("--proxy", default="", help="强制指定代理")
    args = parser.parse_args()

    paths = get_paths(args.devroot)
    tool = load_tool_config(paths["tools_config"], args.tool_name)
    if not tool:
        print(f"[ERROR] 未找到工具配置: {args.tool_name}")
        sys.exit(1)

    local_cfg = tool.get("local", {})
    upstream_cfg = tool.get("upstream", {})

    print("=" * 60)
    print(f"[wf-download-runtime] {args.tool_name}")
    print("=" * 60)

    # Step 1: 本地检测
    print("\n[Step 1] 本地检测")
    local_result = run_atomic(
        os.path.join(paths["common_dir"], "atomic-detect-local.py"),
        ["--config-json", json.dumps(local_cfg, ensure_ascii=False),
         "--devroot", paths["devroot"],
         "--tool-name", args.tool_name,
         "--index-path", paths["index_path"],
         "--get-version-script", paths["get_version_script"]]
    )
    local_version = local_result.get("local_version") or local_result.get("fallback_version")
    print(f"  本地版本: {local_version or 'N/A'}, exe_exists={local_result.get('exe_exists')}")

    # Step 2: 上游查询
    print("\n[Step 2] 上游查询")
    target_version = args.target_version
    if not target_version and upstream_cfg.get("enabled", True):
        query_param = upstream_cfg.get("query_param", args.tool_name)
        upstream_result = run_atomic(
            os.path.join(paths["common_dir"], "atomic-query-upstream.py"),
            ["--tool-name", args.tool_name,
             "--query-param", query_param,
             "--target-version", upstream_cfg.get("target_version", "")]
        )
        if upstream_result.get("error"):
            print(f"  [FAIL] {upstream_result['error']}")
            sys.exit(1)
        target_version = upstream_result.get("upstream_version")
        print(f"  上游版本: {target_version}, source={upstream_result.get('upstream_source')}")
    else:
        upstream_result = {"upstream_version": target_version, "upstream_source": "固定版本", "asset_url": "", "asset_name": ""}
        print(f"  固定版本: {target_version}")

    # Step 3: 版本对比
    print("\n[Step 3] 版本对比")
    compare_result = run_atomic(
        os.path.join(paths["common_dir"], "atomic-compare-version.py"),
        ["--local-ver", local_version or "",
         "--upstream-ver", target_version or ""]
    )
    print(f"  {compare_result.get('message')}, need_update={compare_result.get('need_update')}")

    if not args.force and not compare_result.get("need_update"):
        print("\n[结果] 无需更新")
        sys.exit(0)

    # Step 4: 路由探测
    print("\n[Step 4] 路由探测")
    asset_url = upstream_result.get("asset_url", "")
    if not asset_url:
        # 使用模板生成 URL
        template = tool.get("download_url_template", "")
        if template:
            asset_url = template.replace("{version}", target_version)
    if not asset_url:
        print("  [FAIL] 无下载链接")
        sys.exit(1)

    route_result = run_atomic(
        os.path.join(paths["atomic_dir"], "atomic-01-route-probe.py"),
        ["--url", asset_url, "--proxy", args.proxy]
    )
    print(f"  {route_result.get('reason')}")
    if route_result.get("route") == "none":
        print("  [FAIL] 无可用路由")
        sys.exit(1)

    # Step 5: 下载（stderr 透传以显示进度条）
    print("\n[Step 5] 下载")
    file_ext = "whl" if tool.get("package_type") == "python_wheel" else "zip"
    asset_name = upstream_result.get("asset_name", f"{args.tool_name}-{target_version}.{file_ext}")
    zip_file = os.path.join(paths["download_dir"], asset_name)

    download_args = ["--url", asset_url, "--out-file", zip_file, "--proxy", route_result.get("proxy", "")]
    if args.show_progress:
        download_args.append("--show-progress")
    python_exe = sys.executable
    cmd = [python_exe, os.path.join(paths["atomic_dir"], "atomic-02-download-file.py")] + download_args
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, text=True, encoding="utf-8", errors="replace", timeout=600)
    lines = result.stdout.strip().splitlines()
    if not lines:
        download_result = {"success": False, "error": "无输出"}
    else:
        try:
            download_result = json.loads(lines[-1])
        except json.JSONDecodeError:
            download_result = {"success": False, "error": f"输出不是 JSON: {lines[-1][:100]}"}
    if not download_result.get("success"):
        print(f"  [FAIL] {download_result.get('error')}")
        sys.exit(1)
    print(f"  下载完成: {download_result.get('size_mb')} MB, {download_result.get('elapsed_sec')}s")

    # Step 6: 解压验证
    print("\n[Step 6] 解压与验证")
    extract_result = run_atomic(
        os.path.join(paths["atomic_dir"], "atomic-03-extract-verify.py"),
        ["--zip-file", zip_file,
         "--tool-name", args.tool_name,
         "--config-json", json.dumps({**local_cfg, "upstream_version": target_version, "package_type": tool.get("package_type", "")}, ensure_ascii=False),
         "--devroot", paths["devroot"],
         "--get-version-script", paths["get_version_script"]]
    )
    print(f"  解压目录: {extract_result.get('extract_dir')}")
    if extract_result.get("found_exe"):
        print(f"  找到 exe: {extract_result.get('found_exe')}")
    print(f"  版本验证: {extract_result.get('downloaded_version')}")

    # Step 7: 默认不替换，清理后完成
    tool_dir = os.path.dirname(os.path.join(paths["devroot"], local_cfg.get("exe_path", "").replace("${devroot}", paths["devroot"])))
    print(f"\n[结果] 下载完成，未替换")

    # Step 8: 清理
    print("\n[Step 8] 清理")
    cleanup_result = run_atomic(
        os.path.join(paths["atomic_dir"], "atomic-05-cleanup-temp.py"),
        ["--extract-dir", extract_result.get("extract_dir", ""),
         "--zip-file", zip_file,
         "--keep-zip"]
    )
    print(f"  解压目录清理: {cleanup_result.get('extract_removed')}")
    print(f"  ZIP 保留: {not cleanup_result.get('zip_removed')}")

    print("\n[完成]")
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
