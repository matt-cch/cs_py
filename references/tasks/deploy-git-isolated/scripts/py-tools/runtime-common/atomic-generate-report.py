#!/usr/bin/env python3
r"""
runtime-common/atomic-generate-report.py — 报告生成原子（v1.0.0）
标签：atomic, runtime
职责：接收检测结果数组，输出 stdout 表格 + 保存 JSON 报告

用法：
    python atomic-generate-report.py --results-json '[...]' --output-dir ".../runtime_reports"

输入 JSON 格式：
    [{"name":"node","category":"toolchain","exe_exists":true,"local_version":"26.4.0",
      "upstream_version":"26.4.0","status":"up_to_date","message":"已是最新版",...}, ...]
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")


# =============================================================================
# 报告生成
# =============================================================================

def generate_report(results: list, output_dir: str, script_version: str = "2.0.0") -> dict:
    summary = {
        "total": 0, "pass": 0, "fail": 0,
        "up_to_date": 0, "outdated": 0, "skipped": 0, "unknown": 0
    }
    for r in results:
        summary["total"] += 1
        if r.get("local_error") or r.get("upstream_error"):
            if r.get("status") != "skipped":
                summary["fail"] += 1
        elif r.get("status") == "outdated":
            summary["outdated"] += 1
        elif r.get("status") == "up_to_date":
            summary["up_to_date"] += 1
        elif r.get("status") == "skipped":
            summary["skipped"] += 1
        else:
            summary["unknown"] += 1

    # stdout 输出
    print("\n" + "=" * 60)
    print("真源检测 + 上游版本对比报告")
    print("=" * 60)
    print(f"总计: {summary['total']} | 最新: {summary['up_to_date']} | 可更新: {summary['outdated']} | 已跳过: {summary['skipped']} | 未知: {summary['unknown']} | 失败: {summary['fail']}")

    outdated = [r for r in results if r.get("status") == "outdated"]
    if outdated:
        print("\n[⚠️ 可更新项]")
        for item in outdated:
            print(f"  {item['name']:20s} {item.get('local_version','N/A'):15s} → {item.get('upstream_version','N/A'):15s}")

    failed = [r for r in results if (r.get("local_error") or r.get("upstream_error")) and r.get("status") != "skipped"]
    if failed:
        print("\n[❌ 失败项]")
        for item in failed:
            print(f"  {item['name']:20s} ERROR: {item.get('local_error') or item.get('upstream_error')}")

    skipped = [r for r in results if r.get("status") == "skipped"]
    if skipped:
        print("\n[⏭️ 已跳过]")
        for item in skipped:
            print(f"  {item['name']:20s} {item.get('message','')}")

    uptodate = [r for r in results if r.get("status") == "up_to_date"]
    if uptodate:
        print("\n[✅ 已是最新]")
        for item in uptodate:
            print(f"  {item['name']:20s} {item.get('local_version','N/A')}")

    gh = [r for r in results if r.get("category") == "github_connectivity"]
    if gh:
        print("\n[🌐 GitHub 连通性]")
        for item in gh:
            icon = "✅" if item.get("status") == "PASS" else "❌"
            print(f"  {icon} {item['name']:20s} {item.get('latency_ms','N/A')}ms {item.get('message','')}")

    # JSON 落盘
    report = {
        "meta": {
            "script_version": script_version,
            "executed_at": datetime.now().isoformat(),
            "summary": summary
        },
        "results": results
    }
    os.makedirs(output_dir, exist_ok=True)
    filename = f"verify-runtime-report-{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 报告已保存: {filepath}")

    return {"summary": summary, "filepath": filepath}


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="报告生成原子")
    parser.add_argument("--results-json", required=True, help="检测结果 JSON 字符串")
    parser.add_argument("--output-dir", required=True, help="报告输出目录")
    parser.add_argument("--script-version", default="2.0.0", help="脚本版本号")
    args = parser.parse_args()

    results = json.loads(args.results_json)
    result = generate_report(results, args.output_dir, args.script_version)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
