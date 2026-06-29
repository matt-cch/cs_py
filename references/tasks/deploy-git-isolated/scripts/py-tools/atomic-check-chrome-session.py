#!/usr/bin/env python3
"""
atomic-check-chrome-session.py — Chrome Session 状态检测 CLI

职责：通过 py_lib 统一入口加载 chrome_session 插件，
检测 Chrome Profile 中指定域名的登录态并输出格式化报告。

返回码：
  0 — Session 正常（存在登录态标志）
  1 — Session 缺失/异常/DB 不存在

用法：
  # 默认检测 devroot 下的 data-chrome（头条系）
  python atomic-check-chrome-session.py

  # 指定 Chrome Profile 路径
  python atomic-check-chrome-session.py --user-data-dir "D:\\custom\\chrome-profile"

  # 检测其他域名
  python atomic-check-chrome-session.py --domain-patterns "%github%" --key-cookies "session_id,auth_token"
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _default_user_data_dir() -> str:
    """推断默认 Chrome Profile 路径（devroot 下的 data-chrome）"""
    devroot = Path(__file__).parent.parent.parent.parent.parent.parent.resolve()
    return str(devroot / "venv" / "data-chrome")


def _devroot() -> str:
    """推断 devroot"""
    return str(Path(__file__).parent.parent.parent.parent.parent.parent.resolve())


def _parse_list(text: str) -> list[str]:
    """解析逗号或空格分隔的列表"""
    return [x.strip() for x in text.replace(",", " ").split() if x.strip()]


def main():
    parser = argparse.ArgumentParser(description="Chrome Session 状态检测")
    parser.add_argument(
        "--user-data-dir",
        default=_default_user_data_dir(),
        help="Chrome Profile 路径（默认: devroot/venv/data-chrome）",
    )
    parser.add_argument(
        "--domain-patterns",
        default=None,
        help="SQL LIKE 模式，逗号或空格分隔（默认头条系）",
    )
    parser.add_argument(
        "--key-cookies",
        default=None,
        help="登录态标志 cookie 名，逗号或空格分隔（默认头条系）",
    )
    args = parser.parse_args()

    from py_lib import load_plugins

    registry = load_plugins(devroot=_devroot(), tags=["browser", "session"])
    cs = registry.chrome_session

    domain_patterns = _parse_list(args.domain_patterns) if args.domain_patterns else None
    key_cookies = set(_parse_list(args.key_cookies)) if args.key_cookies else None

    user_data_dir = args.user_data_dir

    print(f"[Chrome Session] 检测目录: {user_data_dir}")

    # 1. 登录态检测
    state = cs.check_login_state(user_data_dir, domain_patterns, key_cookies)

    if not state["ok"]:
        print(f"[Chrome Session] ❌ 检测失败: {state['reason']}")
        sys.exit(1)

    print(f"[Chrome Session] 共发现 {state['total']} 条匹配 cookie")
    print(f"[Chrome Session] 当前 UTC 时间: {state['now_utc']}")

    flags = [name for name, val in state["has_flags"].items() if val]
    if flags:
        print(f"[Chrome Session] ✅ 发现登录态标志 cookie: {', '.join(flags)}")
    else:
        print("[Chrome Session] ⚠️ 未发现登录态标志 cookie")

    fresh = state["fresh_cookies"]
    if fresh:
        print(f"[Chrome Session] ✅ 最近 10 分钟内活跃/新增的 cookie 共 {len(fresh)} 条")
    else:
        print("[Chrome Session] ⚠️ 未发现最近 10 分钟内活跃的 cookie")

    # 2. TTL 分析
    ttl = cs.analyze_ttl(user_data_dir, domain_patterns, key_cookies)

    if ttl["ok"] and ttl["conservative_ttl"]:
        c = ttl["conservative_ttl"]
        print(f"[Chrome Session] 📌 保守有效期: {c['cookie']} 剩余 {c['remaining_days']} 天 ({c['expires'][:10]})")
    elif ttl["ok"]:
        print("[Chrome Session] 📌 未检测到有效登录态 cookie")
    else:
        print(f"[Chrome Session] ⚠️ TTL 分析失败: {ttl['reason']}")

    # 综合判定
    print(f"[Chrome Session] 📌 综合判定: {ttl.get('summary', state['summary'])}")

    # 返回码
    if flags and ttl.get("conservative_ttl"):
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
