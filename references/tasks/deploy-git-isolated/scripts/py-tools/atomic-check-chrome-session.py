#!/usr/bin/env python3
r"""
atomic-check-chrome-session.py — Chrome Session 状态检测原子 CLI
标签：py-tools
版本：v1.0.0

设计意图：
  1. 通过 py_lib 统一入口加载 chrome_session 插件，读取 Chrome Cookies DB，
     检测指定域名的登录态标志 cookie 与有效期 TTL。
  2. 输出人类可读的 stdout 报告，同时落盘结构化 JSON manifest，
     供下游工具（download-article.py、screenshot_verifier.py、外部 pipeline）复用。
  3. manifest 文件名由调用者通过 --output 显式指定（pipeline 场景），
     不传则自动生成时间戳文件名到 venv/tmp/。

外部依赖：
  - py_lib.py（Layer 2 统一入口，拓扑排序加载插件）
  - chrome_session.py（Layer 1 插件，tags: browser, session）
  - verified-runtime-index.json（真源索引，用于读取 chromium 可执行文件路径）

命令行示例：

  # 默认检测 devroot 下的 data-chrome（头条系域名与登录态标志）
  python atomic-check-chrome-session.py

  # 指定 Chrome Profile 路径
  python atomic-check-chrome-session.py --user-data-dir "D:\custom\chrome-profile"

  # 检测其他域名（如 GitHub）
  python atomic-check-chrome-session.py --domain-patterns "%github%" --key-cookies "session_id,auth_token"

  # 指定 manifest 输出路径（pipeline 中上级调度复用）
  python atomic-check-chrome-session.py --output "venv\tmp\pipeline-manifest.json"

  # 不传 --output 时，自动生成 venv/tmp/chrome-session-manifest-{timestamp}.json

返回码：
  0 — Session 正常（存在登录态标志且 TTL 有效）
  1 — Session 缺失/异常/DB 不存在
"""
import argparse
import json
import sys
from datetime import datetime, timezone
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


def _get_chrome_exe(devroot: str) -> str | None:
    """从 verified-runtime-index.json 读取 Chromium 可执行文件路径。"""
    try:
        index_path = Path(devroot) / "references" / "runtime" / "verified-runtime-index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        return data.get("toolchain", {}).get("chromium", {}).get("executable")
    except Exception:
        return None


def _build_conclusion(state: dict, ttl: dict) -> str:
    """综合 session 与 TTL 结果生成明确、无歧义的人类可读结论。

    结论分级（严格，不允许模棱两可）：
      A. 有效   — 登录态标志齐全 + 近期活跃（fresh_cookies 非空）
      B. 残留   — 登录态标志齐全 + 无近期活跃（历史 session，大概率可用但风控风险高）
      C. 残缺   — 部分登录态标志缺失（如只有 sessionid 无 passport_auth_status）
      D. 失效   — 无登录态标志 或 TTL 已过期

    注意：chrome_session.check_login_state() 返回的登录态标志在 has_flags 嵌套字典中。
    """
    has_flags = state.get("has_flags", {})
    fresh = bool(state.get("fresh_cookies"))
    ttl_ok = ttl.get("ok") and ttl.get("conservative_ttl")
    remaining_days = ttl["conservative_ttl"]["remaining_days"] if ttl_ok else None

    # 判定核心标志是否齐全
    core_ok = (
        has_flags.get("sessionid")
        and has_flags.get("sessionid_ss")
        and has_flags.get("passport_auth_status")
    )
    has_any = has_flags.get("sessionid") or has_flags.get("passport_auth_status")

    if core_ok and fresh:
        status = "有效"
        detail = "登录态完整且近期活跃，可正常使用"
    elif core_ok and not fresh:
        status = "残留"
        detail = "登录态完整但无近期活跃，为历史 session，大概率可用但可能触发风控"
    elif has_any and not core_ok:
        status = "残缺"
        detail = "登录态标志部分缺失，session 不完整"
    else:
        status = "失效"
        detail = "未检测到有效登录态 cookie"

    ttl_info = f"，有效期 {remaining_days} 天" if remaining_days is not None else ""
    return f"Session {status}{ttl_info}。{detail}"


def _build_manifest(
    mode: str,
    user_data_dir: str,
    chrome_exe: str | None,
    state: dict,
    ttl: dict,
) -> dict:
    """构造与 debug/playwright/agent-verify 对齐的结构化 manifest。"""
    now = datetime.now(timezone.utc)
    return {
        "meta": {
            "generated_at": now.isoformat(),
            "mode": mode,
            "tool": "atomic-check-chrome-session",
            "version": "1.0.0",
        },
        "environment": {
            "chrome_exe": chrome_exe,
            "user_data_dir": user_data_dir,
        },
        "session": state,
        "session_ttl": ttl,
        "conclusion": _build_conclusion(state, ttl),
    }


def _write_manifest(manifest: dict, output_path: Path) -> Path:
    """将 manifest 写入磁盘，父目录自动创建。写入后立即回读验证并打印关键字段摘要。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # 回读验证：确认写入成功且 JSON 可解析
    data = json.loads(output_path.read_text(encoding="utf-8"))
    print(f"[Chrome Session] 📄 Manifest 已保存: {output_path}")
    print(f"[Chrome Session] 📄 Manifest 结论: {data['conclusion']}")
    print(f"[Chrome Session] 📄 Manifest 工具: {data['meta']['tool']} v{data['meta']['version']}")
    return output_path


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
    parser.add_argument(
        "--output",
        default=None,
        help="Manifest 输出路径（默认: devroot/venv/tmp/chrome-session-manifest-{timestamp}.json）",
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

    # 登录态标志逐项明示
    has_flags = state["has_flags"]
    flags = [name for name, val in has_flags.items() if val]
    print("[Chrome Session] ── 登录态标志逐项检测 ──")
    for name, val in sorted(has_flags.items()):
        mark = "✅" if val else "❌"
        print(f"  {mark} {name}")

    fresh = state["fresh_cookies"]
    if fresh:
        print(f"[Chrome Session] ✅ 新鲜度: 最近 10 分钟内活跃/新增 {len(fresh)} 条 cookie")
    else:
        print("[Chrome Session] ❌ 新鲜度: 无近期活跃 cookie（历史残留）")

    # 2. TTL 分析
    ttl = cs.analyze_ttl(user_data_dir, domain_patterns, key_cookies)

    if ttl["ok"] and ttl["conservative_ttl"]:
        c = ttl["conservative_ttl"]
        print(f"[Chrome Session] 📌 保守有效期: {c['cookie']} 剩余 {c['remaining_days']} 天 ({c['expires'][:10]})")
    elif ttl["ok"]:
        print("[Chrome Session] 📌 未检测到有效登录态 cookie")
    else:
        print(f"[Chrome Session] ⚠️ TTL 分析失败: {ttl['reason']}")

    # 综合判定（A/B/C/D 分级，明确无歧义）
    conclusion = _build_conclusion(state, ttl)
    print(f"[Chrome Session] ── 综合判定 ──")
    print(f"  → {conclusion}")

    # 3. Manifest 生成与落盘
    chrome_exe = _get_chrome_exe(_devroot())
    manifest = _build_manifest(
        mode="check",
        user_data_dir=user_data_dir,
        chrome_exe=chrome_exe,
        state=state,
        ttl=ttl,
    )
    if args.output:
        manifest_path = Path(args.output)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        manifest_path = Path(_devroot()) / "venv" / "tmp" / f"chrome-session-manifest-{ts}.json"
    _write_manifest(manifest, manifest_path)

    # 返回码
    if flags and ttl.get("conservative_ttl"):
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
