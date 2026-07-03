#!/usr/bin/env python3
r"""
verify-runtime/wf-verify-runtime.py — 真源检测 Workflow（v2.0.0）
标签：wf, runtime
职责：编排本地检测 → 上游查询 → 版本对比 → 报告生成

用法：
    python wf-verify-runtime.py
    python wf-verify-runtime.py --tool node

改进点（相较 runtime/verify-runtime.py）：
1. 走 atomic 原子脚本体系，每个步骤独立可测
2. 通过 subprocess 调用 atomic 脚本，步骤间解耦
3. 支持 --tool 单工具检测
"""
import argparse
import json
import os
import subprocess
import sys
import atexit
import time
import urllib.request
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

from detect_devroot import get_devroot


# =============================================================================
# 路径与配置
# =============================================================================

def get_paths(devroot: str) -> dict:
    """返回 workflow 所需的各类路径"""
    root = Path(devroot)
    return {
        "devroot": str(root),
        "tools_config": str(root / "references" / "runtime" / "runtime_config" / "tools_config.json"),
        "index_path": str(root / "references" / "runtime" / "verified-runtime-index.json"),
        "report_dir": str(root / "references" / "runtime" / "runtime_reports"),
        "common_dir": str(Path(__file__).parent.parent / "runtime-common"),
    }


def load_tools_config(config_path: str) -> list:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f).get("tools", [])


# =============================================================================
# 原子脚本调用封装
# =============================================================================

def run_atomic(script_path: str, args: list) -> dict:
    """调用原子脚本，返回解析后的 JSON 结果"""
    python_exe = sys.executable
    cmd = [python_exe, script_path] + args
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    # 最后一行是 JSON 输出
    lines = result.stdout.strip().splitlines()
    if not lines:
        return {"error": "无输出"}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"error": f"输出不是 JSON: {lines[-1][:100]}"}


# =============================================================================
# GitHub 连通性检测
# =============================================================================

def check_github_connectivity(urls: dict) -> list:
    results = []
    for name, url in urls.items():
        t0 = time.time()
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "wf-verify-runtime/2.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                elapsed = int((time.time() - t0) * 1000)
                results.append({"name": name, "category": "github_connectivity", "status": "PASS", "latency_ms": elapsed, "message": "连通正常"})
        except Exception as e:
            elapsed = int((time.time() - t0) * 1000)
            results.append({"name": name, "category": "github_connectivity", "status": "FAIL", "latency_ms": elapsed, "message": str(e)[:100]})
    return results


# =============================================================================
# 主流程
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="真源检测 Workflow")
    parser.add_argument("--devroot", default="", help="devroot 绝对路径（默认自动探测）")
    parser.add_argument("--tool", default="", help="仅检测指定工具")
    args = parser.parse_args()

    devroot = str(get_devroot(args.devroot or None))
    paths = get_paths(devroot)
    tools = load_tools_config(paths["tools_config"])
    if args.tool:
        tools = [t for t in tools if t["name"] == args.tool]

    if not tools:
        print("[ERROR] 未发现需要检测的工具")
        sys.exit(1)

    print("=" * 60)
    print("[wf-verify-runtime] 真源检测 Workflow")
    print("=" * 60)
    print(f"检测工具数: {len(tools)}")

    all_results = []
    total_start = time.time()

    for i, tool in enumerate(tools, 1):
        name = tool["name"]
        print(f"\n[{i}/{len(tools)}] {name}")
        step_start = time.time()

        local_cfg = tool.get("local", {})
        upstream_cfg = tool.get("upstream", {})

        # Step 1: 本地检测
        local_result = run_atomic(
            os.path.join(paths["common_dir"], "atomic-detect-local.py"),
            ["--config-json", json.dumps(local_cfg, ensure_ascii=False),
             "--devroot", paths["devroot"],
             "--tool-name", name,
             "--index-path", paths["index_path"]]
        )
        print(f"  [detect] exe_exists={local_result.get('exe_exists')}, version={local_result.get('local_version') or 'N/A'}")

        # Step 2: 上游查询（仅本地存在时）
        upstream_result = {"upstream_version": None, "upstream_source": None, "error": None}
        if local_result.get("exe_exists") and upstream_cfg.get("enabled", True) and upstream_cfg.get("query_param"):
            constraint = upstream_cfg.get("version_constraint")
            query_args = [
                "--tool-name", name,
                "--query-param", upstream_cfg["query_param"],
                "--target-version", upstream_cfg.get("target_version", "")
            ]
            if constraint:
                query_args.extend(["--constraint-json", json.dumps(constraint, ensure_ascii=False)])
            if upstream_cfg.get("stable_only"):
                query_args.append("--stable-only")
            upstream_result = run_atomic(
                os.path.join(paths["common_dir"], "atomic-query-upstream.py"),
                query_args
            )
            constraint_info = ""
            if upstream_result.get("constrained"):
                constraint_info = f" (已约束: {upstream_result.get('constraint_msg')})"
            print(f"  [query] upstream={upstream_result.get('upstream_version') or 'N/A'}, source={upstream_result.get('upstream_source') or 'N/A'}{constraint_info}")
        elif not upstream_cfg.get("enabled", True):
            upstream_result = {"upstream_version": None, "upstream_source": None, "error": None, "disabled": True, "reason": upstream_cfg.get("reason", "上游查询已禁用")}
            print(f"  [query] 已跳过: {upstream_result['reason']}")

        # Step 3: 版本对比
        compare_result = {"status": "unknown", "message": "未执行对比"}
        if local_result.get("exe_exists"):
            compare_result = run_atomic(
                os.path.join(paths["common_dir"], "atomic-compare-version.py"),
                ["--local-ver", local_result.get("local_version") or "",
                 "--upstream-ver", upstream_result.get("upstream_version") or ""]
            )
            print(f"  [compare] {compare_result.get('message')}")
        elif upstream_result.get("disabled"):
            compare_result = {"status": "skipped", "message": f"上游查询已跳过: {upstream_result.get('reason','')}"}
        else:
            compare_result = {"status": "unknown", "message": "本地文件不存在"}

        # 聚合结果
        entry = {
            "name": name,
            "category": tool.get("category", "toolchain"),
            "exe_exists": local_result.get("exe_exists"),
            "exe_path": local_result.get("exe_path"),
            "resolved_path": local_result.get("resolved_path"),
            "local_version": local_result.get("local_version"),
            "fallback_version": local_result.get("fallback_version"),
            "upstream_version": upstream_result.get("upstream_version"),
            "upstream_source": upstream_result.get("upstream_source"),
            "upstream_disabled": upstream_result.get("disabled"),
            "upstream_reason": upstream_result.get("reason"),
            "status": compare_result.get("status"),
            "message": compare_result.get("message"),
            "need_update": compare_result.get("need_update", False),
            "local_error": local_result.get("error"),
            "upstream_error": upstream_result.get("error"),
        }
        all_results.append(entry)
        print(f"  耗时: {time.time() - step_start:.2f}s")

    # Step 4: GitHub 连通性
    print("\n[GitHub 连通性检测]")
    gh_urls = {
        "api_search": "https://api.github.com/search/issues?q=test",
        "api_issues": "https://api.github.com/repos/anomalyco/opencode/issues?q=test",
        "web_search_issues": "https://github.com/search?q=test&type=issues",
        "web_issues_list": "https://github.com/anomalyco/opencode/issues",
    }
    gh_results = check_github_connectivity(gh_urls)
    for r in gh_results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"  {icon} {r['name']:20s} {r['latency_ms']}ms {r['message']}")
    all_results.extend(gh_results)

    # Step 5: 报告生成
    print("\n[生成报告]")
    report_result = run_atomic(
        os.path.join(paths["common_dir"], "atomic-generate-report.py"),
        ["--results-json", json.dumps(all_results, ensure_ascii=False),
         "--output-dir", paths["report_dir"],
         "--script-version", "2.0.0"]
    )

    total_elapsed = time.time() - total_start
    print(f"\n[总耗时] {total_elapsed:.2f}s")

    # 有可更新项时返回非零
    outdated = [r for r in all_results if r.get("status") == "outdated"]
    sys.exit(1 if outdated else 0)


if __name__ == "__main__":
    sys.exit(main())
