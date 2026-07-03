#!/usr/bin/env python3
r"""
download-runtime/wf-download-runtime.py — 运行时下载 Workflow（v2.0.0）
标签：wf, runtime
职责：编排检测 → 查询 → 对比 → 路由 → 下载 → 解压 → 备份替换 → 清理

用法：
    python wf-download-runtime.py --tool-name node
    python wf-download-runtime.py --tool-name node --force
"""
import argparse
import json
import os
import subprocess
import sys
import atexit
from pathlib import Path

# 编码处理闭环：保存原始编码 → 切换 UTF-8 → 退出时恢复
_original_stdout_encoding = sys.stdout.encoding
_original_stderr_encoding = sys.stderr.encoding

def _restore_encoding():
    try:
        if sys.stdout.encoding != _original_stdout_encoding:
            sys.stdout.reconfigure(encoding=_original_stdout_encoding)
    except Exception:
        pass
    try:
        if sys.stderr.encoding != _original_stderr_encoding:
            sys.stderr.reconfigure(encoding=_original_stderr_encoding)
    except Exception:
        pass

atexit.register(_restore_encoding)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


# =============================================================================
# devroot 探测（复用本地插件）
# =============================================================================
_PLUGIN_DIR = str(Path(__file__).resolve().parents[2] / "py-plugins")
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

# py_lib 统一入口在 scripts/ 目录，需额外加入 sys.path
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[2])
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from detect_devroot import get_devroot
from py_lib import load_plugins


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


def _parse_version(v: str) -> tuple:
    """语义版本号解析，支持 '3.13.14'、'v26.4.0' 等格式。"""
    import re
    clean = re.sub(r'^[vV]', '', v)
    parts = clean.split('.')
    nums = []
    for p in parts:
        m = re.match(r'(\d+)', p)
        nums.append(int(m.group(1)) if m else 0)
    while len(nums) < 4:
        nums.append(0)
    return tuple(nums)


def _version_gte(a: str, b: str) -> bool:
    """a >= b（语义版本比较）"""
    return _parse_version(a) >= _parse_version(b)


def _version_gt(a: str, b: str) -> bool:
    """a > b（语义版本比较）"""
    return _parse_version(a) > _parse_version(b)


def get_paths(devroot: str) -> dict:
    root = Path(devroot)
    return {
        "devroot": str(root),
        "tools_config": str(root / "references" / "runtime" / "runtime_config" / "tools_config.json"),
        "index_path": str(root / "references" / "runtime" / "verified-runtime-index.json"),
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


def _load_download_url_from_index(index_path: str, tool_name: str) -> str:
    """
    从 verified-runtime-index.json 读取上次真源检测时记录的实测下载链接。
    读取优先级：upstream_sources.*.latest_checked.direct_url → download_url_template
    这是实测不可用时的快照兜底（P1 级真源）。
    """
    if not os.path.exists(index_path):
        return ""
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            idx = json.load(f)
        tool_cfg = idx.get("toolchain", {}).get(tool_name, {})
        # 优先读取上次实测记录的 direct_url
        for src_name, src in tool_cfg.get("upstream_sources", {}).items():
            if isinstance(src, dict) and "latest_checked" in src:
                checked = src["latest_checked"]
                if isinstance(checked, dict) and checked.get("direct_url"):
                    return checked["direct_url"]
                # Google Chrome for Testing 特殊结构：stable.win64_url
                if isinstance(checked, dict) and "stable" in checked:
                    stable = checked["stable"]
                    if isinstance(stable, dict) and stable.get("win64_url"):
                        return stable["win64_url"]
        # 兜底：模板（但不推荐，因为模板是拼接的，不是实测链接）
        return tool_cfg.get("download_url_template", "")
    except Exception:
        return ""


def _preflight_cleanup(download_dir: str, zip_file: str, extract_dir: str) -> dict:
    """
    下载前精确清理：仅删除本次将要重新生成的目标产物（ZIP + 解压目录）。
    不波及同工具的其他版本产物。
    """
    removed = {"zip": False, "extract_dir": False}

    if os.path.exists(zip_file):
        try:
            os.remove(zip_file)
            removed["zip"] = True
        except Exception:
            pass

    if os.path.exists(extract_dir):
        try:
            import shutil
            shutil.rmtree(extract_dir)
            removed["extract_dir"] = True
        except Exception:
            pass

    return removed


def main():
    parser = argparse.ArgumentParser(description="运行时下载 Workflow")
    parser.add_argument("--devroot", default="", help="devroot 绝对路径（默认自动探测）")
    parser.add_argument("--tool-name", "-t", required=True, help="工具名")
    parser.add_argument("--force", "-f", action="store_true", help="强制下载并替换")
    parser.add_argument("--show-progress", "-p", action="store_true", help="显示下载进度")
    parser.add_argument("--target-version", default="", help="指定目标版本")
    parser.add_argument("--proxy", default="", help="强制指定代理")
    args = parser.parse_args()

    devroot = str(get_devroot(args.devroot or None))
    paths = get_paths(devroot)
    tool = load_tool_config(paths["tools_config"], args.tool_name)
    if not tool:
        print(f"[ERROR] 未找到工具配置: {args.tool_name}")
        sys.exit(1)

    # 加载 runtime_naming 命名真源插件（三层架构：py_lib → py-sort-rules.json → runtime_naming）
    registry = load_plugins(devroot=devroot, tags=["naming"])
    naming = registry.runtime_naming

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
         "--index-path", paths["index_path"]]
    )
    local_version = local_result.get("local_version") or local_result.get("fallback_version")
    print(f"  本地版本: {local_version or 'N/A'}, exe_exists={local_result.get('exe_exists')}")

    # Step 2: 上游查询（总是调用 atomic，支持 target_version 验证 + 约束过滤）
    print("\n[Step 2] 上游查询")
    target_version = args.target_version
    if upstream_cfg.get("enabled", True):
        query_param = upstream_cfg.get("query_param", args.tool_name)
        query_args = [
            "--tool-name", args.tool_name,
            "--query-param", query_param,
            "--target-version", target_version
        ]
        constraint = upstream_cfg.get("version_constraint")
        if constraint:
            query_args.extend(["--constraint-json", json.dumps(constraint, ensure_ascii=False)])
        if upstream_cfg.get("stable_only"):
            query_args.append("--stable-only")
        upstream_result = run_atomic(
            os.path.join(paths["common_dir"], "atomic-query-upstream.py"),
            query_args
        )
        if upstream_result.get("error"):
            print(f"  [FAIL] {upstream_result['error']}")
            if "available_top10" in upstream_result:
                print(f"  可用版本前 10: {upstream_result['available_top10']}")
            sys.exit(1)
        target_version = upstream_result.get("upstream_version")
        constraint_info = ""
        if upstream_result.get("constrained"):
            constraint_info = f" (已约束: {upstream_result.get('constraint_msg')})"
        print(f"  上游版本: {target_version}, source={upstream_result.get('upstream_source')}{constraint_info}")
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

    # Step 3.5: 实测版本约束强制检查
    constraint = upstream_cfg.get("version_constraint")
    if constraint:
        ctype = constraint.get("type", "")
        cvalue = constraint.get("value", "")
        creason = constraint.get("reason", "")
        if ctype == "pin" and target_version != cvalue:
            print(f"\n[FAIL] 版本约束违反")
            print(f"  请求版本: {target_version}")
            print(f"  锁定版本: {cvalue} ({ctype})")
            print(f"  原因: {creason}")
            sys.exit(1)
        elif ctype == "max" and _version_gt(target_version, cvalue):
            print(f"\n[FAIL] 版本约束违反")
            print(f"  请求版本: {target_version}")
            print(f"  最大允许: {cvalue} ({ctype})")
            print(f"  原因: {creason}")
            sys.exit(1)
        print(f"\n[OK] 版本约束检查通过 ({ctype}: {cvalue})")

    # Step 4: 路由探测
    print("\n[Step 4] 路由探测")
    asset_url = upstream_result.get("asset_url", "")
    if not asset_url:
        # P1 兜底：实测不可用，尝试从快照 JSON 读取上次验证通过的 direct_url
        print("  [WARN] 上游查询未返回实测下载链接，尝试从快照 JSON 兜底...")
        snapshot_url = _load_download_url_from_index(paths["index_path"], args.tool_name)
        if snapshot_url:
            asset_url = snapshot_url
            print(f"  [INFO] 使用快照 JSON 兜底链接")
        else:
            print("  [FAIL] 快照 JSON 中也无可用下载链接")
            sys.exit(1)
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
    # 命名唯一真源：集中由 runtime_naming 插件生成
    naming_paths = naming.get_download_paths(
        download_dir=paths["download_dir"],
        tool_name=args.tool_name,
        target_version=target_version,
        asset_name=upstream_result.get("asset_name", ""),
        url_template=tool.get("download_url_template", ""),
        package_type=tool.get("package_type", "zip"),
    )
    asset_name = naming_paths["asset_name"]
    zip_file = naming_paths["asset_path"]
    extract_dir = naming_paths["extract_dir_path"]

    # Step 4.5: Preflight 清理（仅删除本次将要重新生成的目标产物）
    cleanup_result = _preflight_cleanup(paths["download_dir"], zip_file, extract_dir)
    if cleanup_result["zip"] or cleanup_result["extract_dir"]:
        print(f"  [Preflight] 清理旧产物: zip={cleanup_result['zip']}, extract={cleanup_result['extract_dir']}")

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
    # 下载详情已由 atomic-02-download-file.py 输出到 stderr

    # Step 6: 解压验证
    print("\n[Step 6] 解压与验证")
    extract_result = run_atomic(
        os.path.join(paths["atomic_dir"], "atomic-03-extract-verify.py"),
        ["--zip-file", zip_file,
         "--tool-name", args.tool_name,
         "--config-json", json.dumps({**local_cfg, "upstream_version": target_version, "package_type": tool.get("package_type", "")}, ensure_ascii=False),
         "--devroot", paths["devroot"],
         "--target-version", target_version,
         "--extract-dir", extract_dir]
    )
    print(f"  解压目录: {extract_result.get('extract_dir')}")
    if extract_result.get("found_exe"):
        print(f"  找到 exe: {extract_result.get('found_exe')}")
    print(f"  版本验证: {extract_result.get('downloaded_version')}")

    # Step 7: 默认不替换，清理后完成
    tool_dir = os.path.dirname(os.path.join(paths["devroot"], local_cfg.get("exe_path", "").replace("${devroot}", paths["devroot"])))
    print(f"\n[结果] 下载完成，未替换")

    # Step 8: 保留产物（解压目录 + ZIP 均保留，供手工升级）
    print("\n[Step 8] 产物保留")
    print(f"  ZIP 文件: {zip_file}")
    print(f"  解压目录: {extract_result.get('extract_dir')}")
    print(f"  提示: 如需替换，执行 atomic-04-backup-replace.py")

    print("\n[完成]")
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
