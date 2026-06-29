#!/usr/bin/env python3
"""
download-article.py — 文章正文下载 CLI

职责：通过 py_lib 统一入口加载 article_extractor 插件执行提取，
并在提取前执行 preflight 检查（Chrome 路径、Profile 占用、Session 状态）。

用法：
  python download-article.py --url "<文章URL>" [--tags "AI,编程"] [--headless]
"""
import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# py_lib 统一入口
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _is_toutiao_url(url: str) -> bool:
    return "toutiao.com" in url or "toutiao.cn" in url


def _is_chrome_profile_locked(user_data_dir: str) -> tuple[bool, str]:
    """检测是否有 Chrome 进程正在占用指定 Profile 目录。
    返回 (是否被占用, 说明信息)
    """
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or "chrome.exe" not in result.stdout:
            return False, "无 Chrome 进程运行"

        # 粗略判断：有 chrome.exe 进程且 user-data-dir 目录存在 Lock 文件
        lock_file = Path(user_data_dir) / "Default" / "lockfile"
        if lock_file.exists():
            return True, f"Profile 被锁定（{lock_file} 存在）"

        return True, "有 Chrome 进程运行（但未确认具体 Profile）"
    except Exception as e:
        return False, f"进程检测失败: {e}"


def _preflight(url: str, devroot: str | None = None) -> tuple[bool, str]:
    """提取前预检。返回 (通过?, 说明信息)。"""
    print("[Preflight] 执行前置检查...")

    # 1. 加载底层插件
    try:
        from py_lib import load_plugins
        registry = load_plugins(devroot=devroot, tags=["core", "browser", "session"])
        bs = registry.browser_session
        cs = registry.chrome_session
    except Exception as e:
        return False, f"插件加载失败: {e}"

    # 2. Chrome 路径验证
    try:
        chrome_exe, user_data_dir = bs._get_chrome_paths(devroot)
    except Exception as e:
        return False, f"Chrome 路径获取失败: {e}"

    if not Path(chrome_exe).exists():
        return False, f"Chrome 可执行文件不存在: {chrome_exe}"
    print(f"[Preflight] [OK] Chrome: {chrome_exe}")

    if not Path(user_data_dir).exists():
        return False, f"Chrome Profile 目录不存在: {user_data_dir}"
    print(f"[Preflight] [OK] Profile: {user_data_dir}")

    # 3. Profile 占用检测
    locked, lock_reason = _is_chrome_profile_locked(user_data_dir)
    if locked:
        return False, f"Chrome Profile 被占用 — {lock_reason}。请先关闭其他 Chrome 实例后重试。"
    print(f"[Preflight] [OK] Profile 未被占用")

    # 4. 头条 Session 检测
    if _is_toutiao_url(url):
        print("[Preflight] 检测到头条 URL，执行 Session 检测...")
        state = cs.check_login_state(user_data_dir)
        if not state["ok"]:
            return False, f"Session 检测失败: {state.get('reason', 'unknown')}"

        flags = [name for name, val in state["has_flags"].items() if val]
        if not flags:
            return (
                False,
                "头条 Session 未检测到登录态标志 cookie。"
                "请先执行交互式登录: run.py --mode interactive --url https://www.toutiao.com"
            )

        ttl = cs.analyze_ttl(user_data_dir)
        if ttl["ok"] and ttl.get("conservative_ttl"):
            days = ttl["conservative_ttl"]["remaining_days"]
            print(f"[Preflight] [OK] 头条 Session 标志: {', '.join(flags)}")
            print(f"[Preflight] [OK] Session 有效期: {days} 天")
            if days <= 1:
                return False, f"头条 Session 即将过期（{days} 天），建议立即重新登录"
            if days <= 7:
                print(f"[Preflight] [WARN] Session 有效期紧张（{days} 天），建议本周内续期")
        else:
            print(f"[Preflight] [OK] 头条 Session 标志: {', '.join(flags)}")
            print(f"[Preflight] [WARN] 无法计算 Session 有效期")
    else:
        print("[Preflight] [SKIP] 非头条 URL，跳过 Session 检测")

    print("[Preflight] ✅ 全部通过\n")
    return True, ""


def main():
    parser = argparse.ArgumentParser(description="文章正文下载工具")
    parser.add_argument("--url", required=True, help="文章 URL")
    parser.add_argument("--tags", default=None, help="逗号分隔的标签，如 AI,编程")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认 devroot/out/articles/）")
    parser.add_argument("--headless", action="store_true", default=True, help="无头模式（默认开启）")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--devroot", default=None, help="devroot 路径（默认自动探测）")
    parser.add_argument("--skip-preflight", action="store_true", help="跳过前置检查（调试用）")
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
    headless = not args.headed if args.headed else args.headless

    # Preflight
    if not args.skip_preflight:
        ok, reason = _preflight(args.url, devroot=args.devroot)
        if not ok:
            print(f"[Preflight] ❌ {reason}")
            sys.exit(1)

    # 加载提取插件
    try:
        from py_lib import load_plugins
        registry = load_plugins(devroot=args.devroot, tags=["extraction"])
        extract_article_func = registry.article_extractor.extract_article
    except Exception as e:
        print(f"[ERROR] 插件加载失败: {e}")
        sys.exit(1)

    # 执行提取
    out_path = asyncio.run(extract_article_func(
        url=args.url,
        tags=tags,
        output_dir=args.output_dir,
        headless=headless,
    ))

    if out_path:
        print(f"\n✅ 文章已保存: {out_path}")
        sys.exit(0)
    else:
        print("\n❌ 提取失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
