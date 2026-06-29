#!/usr/bin/env python3
"""
插件：Chrome Session 检测器（chrome_session）
标签：browser, session, chrome

职责：读取 Chrome Cookies DB，检测指定域名的登录态标志 cookie，分析有效期 TTL。
与 debug/playwright/agent-verify/lib/session_checker.py 的关系：
  - 本插件是标准化、通用化版本，通过 py_lib 统一入口加载
  - 原 session_checker 保持自包含，不重构引入本插件依赖

设计原则：
  - 不硬编码路径：user_data_dir 由调用方传入
  - 不硬编码域名：domain_patterns 参数化，默认头条系但不写死
  - 不直接打印：返回结构化 dict，由上层 tool/workflow 负责格式化输出
"""
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

CHROME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)

# 默认头条系域名模式
default_domain_patterns = ["%toutiao%", "%byte%", "%snssdk%"]

# 默认头条系登录态标志 cookie
default_key_cookies = {
    "sessionid", "sessionid_ss", "passport_auth_status",
    "passport_auth_status_ss", "passport_csrf_token",
    "passport_csrf_token_default", "odin_tt", "tt_scid",
}


def _chrome_time_to_dt(chrome_us: int) -> datetime | None:
    if not chrome_us or chrome_us == 0:
        return None
    return CHROME_EPOCH + timedelta(microseconds=chrome_us)


def _build_cookie_db_path(user_data_dir: str) -> Path:
    return Path(user_data_dir) / "Default" / "Network" / "Cookies"


def check_login_state(
    user_data_dir: str,
    domain_patterns: list[str] | None = None,
    key_cookies: set[str] | None = None,
) -> dict:
    """
    检测 Chrome Cookies DB 中指定域名的登录态标志 cookie。

    Args:
        user_data_dir: Chrome Profile 路径（含 Cookies DB）
        domain_patterns: SQL LIKE 模式列表，默认头条系
        key_cookies: 登录态标志 cookie 名集合，默认头条系

    Returns:
        {
            "ok": bool,
            "reason": str | None,
            "total": int,
            "now_utc": str,
            "has_flags": {name: bool, ...},
            "fresh_cookies": [...],
            "cookies": [...],
            "summary": str,
        }
    """
    if domain_patterns is None:
        domain_patterns = default_domain_patterns
    if key_cookies is None:
        key_cookies = default_key_cookies

    cookie_db = _build_cookie_db_path(user_data_dir)
    if not cookie_db.exists():
        return {
            "ok": False,
            "reason": f"Cookies DB 不存在: {cookie_db}",
            "summary": "Cookies DB 不存在",
        }

    try:
        conn = sqlite3.connect(str(cookie_db))
        c = conn.cursor()
        where_clause = " OR ".join("host_key LIKE ?" for _ in domain_patterns)
        c.execute(
            f"""
            SELECT host_key, name, length(encrypted_value) as val_len,
                   creation_utc, last_access_utc, expires_utc
            FROM cookies
            WHERE {where_clause}
            """,
            domain_patterns,
        )
        rows = c.fetchall()
        conn.close()
    except Exception as e:
        return {
            "ok": False,
            "reason": f"读取 Cookies DB 失败: {e}",
            "summary": f"读取 DB 失败: {e}",
        }

    now = datetime.now(timezone.utc)
    report = {
        "ok": True,
        "reason": None,
        "total": len(rows),
        "now_utc": now.isoformat(),
        "has_flags": {name: False for name in key_cookies},
        "fresh_cookies": [],
        "cookies": [],
        "summary": "",
    }

    for row in rows:
        host, name, val_len, created, accessed, expires = row
        created_dt = _chrome_time_to_dt(created)
        accessed_dt = _chrome_time_to_dt(accessed)

        if name in key_cookies:
            report["has_flags"][name] = True

        if created_dt and accessed_dt:
            if (now - accessed_dt).total_seconds() < 600 or (now - created_dt).total_seconds() < 600:
                report["fresh_cookies"].append({
                    "host": host,
                    "name": name,
                    "val_len": val_len,
                    "created": created_dt.isoformat(),
                    "accessed": accessed_dt.isoformat(),
                })

        report["cookies"].append({
            "host": host,
            "name": name,
            "val_len": val_len,
            "created": created_dt.isoformat() if created_dt else None,
            "accessed": accessed_dt.isoformat() if accessed_dt else None,
        })

    flags_found = [name for name, val in report["has_flags"].items() if val]
    fresh = report["fresh_cookies"]

    if flags_found and fresh:
        report["summary"] = f"登录态 cookie 完整且近期活跃: {', '.join(flags_found)}"
    elif flags_found:
        report["summary"] = f"存在登录态 cookie 但非近期活跃: {', '.join(flags_found)}"
    else:
        report["summary"] = "未检测到有效登录态 cookie"

    return report


def analyze_ttl(
    user_data_dir: str,
    domain_patterns: list[str] | None = None,
    key_cookies: set[str] | None = None,
) -> dict:
    """
    分析 Chrome Cookies DB 中指定域名的关键 cookie 剩余有效期。

    Args:
        user_data_dir: Chrome Profile 路径
        domain_patterns: SQL LIKE 模式列表
        key_cookies: 关键 cookie 名集合

    Returns:
        {
            "ok": bool,
            "reason": str | None,
            "analyzed_at": str,
            "total_cookies": int,
            "key_cookies_found": [...],
            "conservative_ttl": {"cookie": str, "remaining_days": float, "expires": str} | None,
            "longest_ttl": {"cookie": str, "remaining_days": float, "expires": str} | None,
            "summary": str,
        }
    """
    if domain_patterns is None:
        domain_patterns = default_domain_patterns
    if key_cookies is None:
        key_cookies = default_key_cookies

    cookie_db = _build_cookie_db_path(user_data_dir)
    if not cookie_db.exists():
        return {
            "ok": False,
            "reason": f"Cookies DB 不存在: {cookie_db}",
            "summary": "Cookies DB 不存在",
        }

    try:
        conn = sqlite3.connect(str(cookie_db))
        c = conn.cursor()
        where_clause = " OR ".join("host_key LIKE ?" for _ in domain_patterns)
        c.execute(
            f"""
            SELECT host_key, name, expires_utc, last_access_utc
            FROM cookies
            WHERE {where_clause}
            ORDER BY host_key, name
            """,
            domain_patterns,
        )
        rows = c.fetchall()
        conn.close()
    except Exception as e:
        return {
            "ok": False,
            "reason": str(e),
            "summary": f"读取 DB 失败: {e}",
        }

    now = datetime.now(timezone.utc)
    cookie_list = []
    min_remaining = None
    max_remaining = None
    min_cookie = None
    max_cookie = None

    for host, name, expires_utc, last_access_utc in rows:
        expires = _chrome_time_to_dt(expires_utc)
        remaining = expires - now if expires else None
        days = round(remaining.total_seconds() / 86400, 1) if remaining else None
        is_key = name in key_cookies

        entry = {
            "host": host,
            "name": name,
            "expires": expires.isoformat() if expires else None,
            "remaining_days": days,
            "is_key": is_key,
        }
        cookie_list.append(entry)

        if is_key and remaining is not None and remaining.total_seconds() > 0:
            if min_remaining is None or remaining < min_remaining:
                min_remaining = remaining
                min_cookie = entry
            if max_remaining is None or remaining > max_remaining:
                max_remaining = remaining
                max_cookie = entry

    conservative = None
    if min_cookie:
        conservative = {
            "cookie": min_cookie["name"],
            "remaining_days": min_cookie["remaining_days"],
            "expires": min_cookie["expires"],
            "note": "保守有效期：该 cookie 过期后服务端可能拒绝登录态",
        }

    report = {
        "ok": True,
        "reason": None,
        "analyzed_at": now.isoformat(),
        "total_cookies": len(rows),
        "key_cookies_found": [c for c in cookie_list if c["is_key"]],
        "conservative_ttl": conservative,
        "longest_ttl": {
            "cookie": max_cookie["name"],
            "remaining_days": max_cookie["remaining_days"],
            "expires": max_cookie["expires"],
        } if max_cookie else None,
        "summary": "",
    }

    if conservative:
        d = conservative["remaining_days"]
        if d is None:
            report["summary"] = "存在关键 cookie 但无法计算有效期"
        elif d <= 1:
            report["summary"] = f"Session 即将过期（{d} 天），建议立即重新登录"
        elif d <= 7:
            report["summary"] = f"Session 有效期紧张（{d} 天），建议本周内续期"
        elif d <= 30:
            report["summary"] = f"Session 正常（约 {int(d)} 天），续期窗口: {conservative['expires'][:10]}"
        else:
            report["summary"] = f"Session 长期有效（{int(d)} 天+），无需近期关注"
    else:
        report["summary"] = "未检测到有效登录态 cookie"

    return report


# py_lib 注册用元信息
name = "chrome_session"
description = "Chrome Session 检测器：读取 Cookies DB，检测登录态标志与分析 TTL"
