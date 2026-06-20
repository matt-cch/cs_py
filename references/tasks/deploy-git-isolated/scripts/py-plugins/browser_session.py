#!/usr/bin/env python3
"""
插件：Browser Session 管理器（v1.0.0）
标签：core
依赖：无（可选依赖 __plugin_registry__ 提供 devroot）

职责：
1. 启动交互式 Chrome 浏览器，让用户手动登录网站（session 持久化到 user-data-dir）
2. 使用已保存的 session 创建 headless/headed 上下文，执行自动化操作（截图、验证等）
3. 所有路径从 verified-runtime-index.json 读取，不硬编码

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["core"])
    bs = registry.browser_session
    bs.interactive_login("https://github.com/login")   # 用户登录后导航到 example.com 结束
    ctx = bs.create_context(headless=False)
    page = ctx.new_page()
    page.goto("https://github.com/matt-cch/cs_py/issues/1")

用法（直接 CLI）：
    python browser_session.py --mode interactive --url https://github.com/login
"""
import asyncio
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

__plugin_registry__ = None


def _get_devroot() -> str:
    """从 registry 或向上探测获取 devroot"""
    if __plugin_registry__ and hasattr(__plugin_registry__, "devroot"):
        return str(__plugin_registry__.devroot)
    # 向上探测：找到包含 references/runtime/verified-runtime-index.json 的目录
    current = Path(__file__).resolve()
    while current.parent != current:
        candidate = current.parent
        if (candidate / "references" / "runtime" / "verified-runtime-index.json").exists():
            return str(candidate)
        current = candidate
    raise RuntimeError("无法自动探测 devroot：未找到 references/runtime/verified-runtime-index.json")


def _load_runtime_index(devroot: str) -> dict:
    """读取 verified-runtime-index.json 获取 Chromium 路径"""
    index_path = Path(devroot) / "references" / "runtime" / "verified-runtime-index.json"
    with open(index_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _get_chrome_paths(devroot: str = None):
    """返回 (chrome_exe, user_data_dir)"""
    if devroot is None:
        devroot = _get_devroot()
    index = _load_runtime_index(devroot)
    chromium = index.get("toolchain", {}).get("chromium", {})
    exe = chromium.get("executable")
    udd = chromium.get("user_data_dir")
    if not exe or not udd:
        raise RuntimeError("verified-runtime-index.json 中未找到 chromium.executable 或 user_data_dir")
    return exe, udd


class BrowserSession:
    """Chrome 持久化上下文管理器"""

    def __init__(self, devroot: str = None):
        self.chrome_exe, self.user_data_dir = _get_chrome_paths(devroot)

    def interactive_login(self, url: str = "https://github.com/login", timeout: int = 300):
        """
        启动交互式浏览器让用户登录。
        用户完成操作后，将地址栏导航到 https://example.com 以结束等待并保留 session。
        """
        asyncio.run(self._interactive(url, timeout))

    async def _interactive(self, url: str, timeout: int):
        from playwright.async_api import async_playwright

        print(f"[browser_session] 启动交互式 Chrome，打开: {url}")
        print(f"[browser_session] user-data-dir: {self.user_data_dir}")
        print("[browser_session] 请在浏览器中完成登录/操作。")
        print("[browser_session] 操作完成后，请将地址栏导航到 https://example.com 以结束等待并保留 session...")

        stop_event = asyncio.Event()

        def check_stop(page):
            try:
                if "example.com" in page.url and not stop_event.is_set():
                    stop_event.set()
            except Exception:
                pass

        def bind_page(pg):
            pg.on("load", lambda _: check_stop(pg))
            check_stop(pg)

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=self.chrome_exe,
                headless=False,
                ignore_default_args=["--disable-extensions"],
                args=["--no-first-run", "--no-default-browser-check"],
            )
            for pg in context.pages:
                bind_page(pg)
            context.on("page", bind_page)

            page = await context.new_page()
            try:
                await page.goto(url, wait_until="networkidle")
            except Exception as e:
                print(f"[browser_session] 页面导航异常（忽略）: {e}")

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=timeout)
                print("[browser_session] 检测到 example.com，正在关闭浏览器...")
            except asyncio.TimeoutError:
                print("[browser_session] 等待超时，正在关闭浏览器...")

            await context.close()

        print("[browser_session] 浏览器已关闭，session / cookies 已保留在 user-data-dir")

    def create_context(self, headless: bool = True):
        """
        使用已保存的 session 创建持久化上下文。
        返回 Playwright BrowserContext（非异步，调用方自行处理 async）。
        """
        # 注意：此函数返回的是协程对象，需要在 async 环境中 await
        return self._create_context_async(headless)

    async def _create_context_async(self, headless: bool = True):
        from playwright.async_api import async_playwright
        p = await async_playwright().start()
        context = await p.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            executable_path=self.chrome_exe,
            headless=headless,
            ignore_default_args=["--disable-extensions"],
            args=["--no-first-run", "--no-default-browser-check"],
        )
        # 返回 context 和 playwright 实例，便于关闭
        return context, p


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Browser Session 管理器")
    parser.add_argument("--mode", choices=["interactive", "check"], default="interactive")
    parser.add_argument("--url", default="https://github.com/login")
    parser.add_argument("--devroot", default=None)
    args = parser.parse_args()

    bs = BrowserSession(devroot=args.devroot)

    if args.mode == "interactive":
        bs.interactive_login(url=args.url)
    elif args.mode == "check":
        print(f"chrome_exe: {bs.chrome_exe}")
        print(f"user_data_dir: {bs.user_data_dir}")


if __name__ == "__main__":
    main()
