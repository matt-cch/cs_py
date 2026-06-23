#!/usr/bin/env python3
"""
workflow-security-audit.py — 安全审计编排入口（Workflow）
标签：py-tools

职责：组装 security_audit 插件的五 Phase 审计流程，输出人类可读报告与 JSON 报告。
      符合 task-canonical-baseline.md 第 8.4.7 节 Workflow 定义。

用法：
    # 完整审计（默认 HEAD~10..HEAD）
    python workflow-security-audit.py --devroot "D:/pjt/cursor/cs_py"

    # 指定 commit 范围
    python workflow-security-audit.py --devroot "D:/pjt/cursor/cs_py" --commit-range "HEAD~5..HEAD"

    # 仅执行特定 phase
    python workflow-security-audit.py --devroot "D:/pjt/cursor/cs_py" --phases pattern_scan git_tracking

    # 输出 JSON 报告
    python workflow-security-audit.py --devroot "D:/pjt/cursor/cs_py" --output audit-report.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def _print_phase_result(phase: dict) -> None:
    """打印单个 phase 结果"""
    status_icon = "✅" if phase["status"] == "pass" else ("⚠️" if phase["status"] == "warn" else "❌")
    print(f"\n{status_icon} Phase: {phase['phase_name']} ({phase['elapsed_seconds']}s)")
    print(f"   结论: {phase['summary']}")

    details = phase.get("details", [])
    if details:
        print(f"   详情 ({len(details)} 项):")
        for item in details[:10]:  # 最多显示 10 条
            if "file" in item:
                sev = item.get("severity", "info")
                icon = "🔴" if sev == "critical" else ("🟠" if sev == "high" else "🟡")
                print(f"      {icon} {item['file']}:{item.get('line_number', '?')} — {item.get('pattern_name', '')}")
                if "matched_text" in item:
                    print(f"         匹配: {item['matched_text']}")
        if len(details) > 10:
            print(f"      ... 还有 {len(details) - 10} 项")


def main() -> int:
    parser = argparse.ArgumentParser(description="安全审计 Workflow（部署前敏感内容巡检）")
    parser.add_argument("--devroot", default=r"D:\pjt\cursor\cs_py", help="Devroot 路径")
    parser.add_argument("--commit-range", default="HEAD~10..HEAD", help="Git diff 范围")
    parser.add_argument("--phases", nargs="+", default=None, help="指定执行的 phase 列表（默认全部）")
    parser.add_argument("--output", default=None, help="JSON 报告输出文件路径（默认自动落盘到 devroot/venv/tmp/）")
    parser.add_argument("--output-dir", default=None, help="报告输出目录（默认 devroot/venv/tmp）")
    parser.add_argument("--silent", action="store_true", help="静默模式，只输出 JSON")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}", file=sys.stderr)
        return 1

    # 加载 security_audit 插件
    try:
        registry = load_plugins(devroot=str(devroot), tags=["validation"])
        audit = registry.security_audit
    except Exception as e:
        print(f"[ERROR] 加载 security_audit 插件失败: {e}", file=sys.stderr)
        return 1

    if not args.silent:
        print("=" * 50)
        print("🔒 安全审计 Workflow")
        print("=" * 50)
        print(f"devroot: {devroot}")
        print(f"commit_range: {args.commit_range}")
        print(f"phases: {args.phases or '全部'}")
        print("-" * 50)

    # 执行审计
    result = audit.run_audit(
        devroot=devroot,
        commit_range=args.commit_range,
        phases=args.phases,
    )

    # 输出人类可读报告
    if not args.silent:
        for phase in result["phases"]:
            _print_phase_result(phase)

        overall_icon = "✅" if result["overall_status"] == "pass" else ("⚠️" if result["overall_status"] == "warn" else "❌")
        print(f"\n{'=' * 50}")
        print(f"{overall_icon} 总体结论: {result['overall_status'].upper()}")
        print(f"   {result['overall_summary']}")
        print(f"   耗时: {result['total_elapsed_seconds']}s")

        recommendations = result.get("recommendations", [])
        if recommendations:
            print("\n   建议:")
            for rec in recommendations:
                print(f"      - {rec}")

        print(f"{'=' * 50}")

    # 输出 JSON 报告（默认落盘到 venv/tmp/，除非显式指定 --no-output）
    output_dir = Path(args.output_dir) if args.output_dir else devroot / "venv" / "tmp"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        # 自动生成文件名：security-audit-report-{timestamp}.json
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        output_path = output_dir / f"security-audit-report-{ts}.json"

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.silent:
        print(f"\n[Report] JSON 报告已落盘: {output_path}")

    # 静默模式下输出 JSON 到 stdout
    if args.silent:
        print(json.dumps(result, ensure_ascii=False))

    return 0 if result["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
