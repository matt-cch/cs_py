#!/usr/bin/env python3
"""
screenshot_verifier.py — URL 截图验证工具
标签：py-tools
职责：使用已保存的 Chrome session 对指定 URL 截图，保存为 PNG。

用法（CLI）：
    python screenshot_verifier.py --url "https://github.com/matt-cch/cs_py/issues/1" --output issue1.png
    python screenshot_verifier.py --url "https://github.com/matt-cch/cs_py/issues/1" --full-page --wait 5

用法（通过 py_lib 加载）：
    import sys
    sys.path.insert(0, r"...\\scripts")
    from py_lib import load_plugins
    registry = load_plugins(devroot="...", profile="core")
    bs = registry.browser_session
    # 或直接用 screenshot_verifier 的 take_screenshot 函数
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 优先通过 py_lib 入口加载；fallback 直接 import 插件
HAS_PY_LIB = False
try:
    _scripts_dir = Path(__file__).parent.parent.resolve()
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from py_lib import load_plugins
    HAS_PY_LIB = True
except Exception:
    pass

if not HAS_PY_LIB:
    _plugins_dir = Path(__file__).parent.parent / "py-plugins"
    if str(_plugins_dir) not in sys.path:
        sys.path.insert(0, str(_plugins_dir))
    from browser_session import BrowserSession
else:
    from browser_session import BrowserSession


async def take_screenshot(
    url: str,
    output_path: str,
    devroot: str = None,
    headless: bool = True,
    full_page: bool = False,
    wait_seconds: float = 3.0,
    scroll_bottom: bool = False,
):
    """对指定 URL 截图并保存"""
    if HAS_PY_LIB and devroot:
        registry = load_plugins(devroot=devroot, profile="core")
        bs = registry.browser_session
    else:
        bs = BrowserSession(devroot=devroot)

    context, playwright = await bs.create_context(headless=headless)
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="load", timeout=60000)
    except Exception as e:
        print(f"[warn] goto 异常（忽略，继续截图）: {e}")

    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    if scroll_bottom:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)

    await page.screenshot(path=output_path, full_page=full_page)
    print(f"截图已保存: {output_path}")

    await context.close()
    await playwright.stop()


def main():
    parser = argparse.ArgumentParser(description="URL 截图验证工具")
    parser.add_argument("--url", required=True, help="要截图的 URL")
    parser.add_argument("--output", required=True, help="截图保存路径（.png）")
    parser.add_argument("--devroot", default=None, help="devroot 路径（默认自动探测）")
    parser.add_argument("--headed", action="store_true", help=" headed 模式（显示浏览器窗口）")
    parser.add_argument("--full-page", action="store_true", help="截取整页")
    parser.add_argument("--wait", type=float, default=3.0, help="页面加载后等待秒数（默认 3）")
    parser.add_argument("--scroll-bottom", action="store_true", help="截图前滚动到页面底部")
    args = parser.parse_args()

    asyncio.run(take_screenshot(
        url=args.url,
        output_path=args.output,
        devroot=args.devroot,
        headless=not args.headed,
        full_page=args.full_page,
        wait_seconds=args.wait,
        scroll_bottom=args.scroll_bottom,
    ))


if __name__ == "__main__":
    main()
