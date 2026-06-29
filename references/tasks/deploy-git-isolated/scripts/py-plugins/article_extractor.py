import re
from datetime import datetime, timezone
from pathlib import Path

__plugin_registry__ = None


def _get_js_loader():
    if __plugin_registry__ and hasattr(__plugin_registry__, "js_loader"):
        return __plugin_registry__.js_loader
    from js_loader import resolve_script_tags, validate as js_validate
    class _Fallback:
        @staticmethod
        def resolve_script_tags(tool_names=None):
            return resolve_script_tags(tool_names)
        @staticmethod
        def validate():
            return js_validate()
    return _Fallback()


def _get_js_paths(tool_names=None):
    loader = _get_js_loader()
    paths = loader.resolve_script_tags(tool_names=tool_names)
    if not paths:
        raise RuntimeError(f"js_loader.resolve_script_tags({tool_names}) 返回空列表")
    return paths


def _slugify(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[-\s]+", "-", text).strip("-").lower()
    return text[:max_len]


def _guess_ext(url: str) -> str:
    path = url.split("?")[0]
    ext = Path(path).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"):
        return ext
    return ".jpg"


def validate() -> dict:
    loader = _get_js_loader()
    return loader.validate()


async def extract_article(
    url: str,
    tags: list[str] | None = None,
    output_dir: str | None = None,
    headless: bool = True,
) -> Path | None:
    from playwright.async_api import async_playwright

    js_paths = _get_js_paths(tool_names=["extract-article"])

    devroot = None
    if __plugin_registry__ and hasattr(__plugin_registry__, "devroot"):
        devroot = str(__plugin_registry__.devroot)
    if not devroot:
        # 向上探测 devroot（与 browser_session._get_devroot 一致）
        current = Path(__file__).resolve()
        while current.parent != current:
            candidate = current.parent
            if (candidate / "references" / "runtime" / "verified-runtime-index.json").exists():
                devroot = str(candidate)
                break
            current = candidate

    if output_dir is None:
        if devroot:
            output_dir = str(Path(devroot) / "out" / "articles")
        else:
            output_dir = str(Path.cwd() / "out" / "articles")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if devroot:
        from browser_session import _get_chrome_paths as get_paths
        chrome_exe, user_data_dir = get_paths(devroot)
    else:
        chrome_exe, user_data_dir = None, None

    async with async_playwright() as p:
        if chrome_exe:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                executable_path=chrome_exe,
                headless=headless,
                args=["--no-first-run", "--no-default-browser-check"],
            )
        else:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=Path.cwd() / "venv" / "data-chrome",
                headless=headless,
                args=["--no-first-run", "--no-default-browser-check"],
            )

        page = await context.new_page()

        print("[article_extractor] 合并 JS 文件并通过 add_init_script 注入（绕过 CSP）...")
        combined_js = "\n".join(
            Path(p).read_text(encoding="utf-8") for p in js_paths
        )
        await context.add_init_script(combined_js)

        await page.goto(url, wait_until="networkidle", timeout=60000)

        print("[article_extractor] 滚动页面触发懒加载...")
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)
        await page.wait_for_load_state("networkidle")

        result = await page.evaluate("window.__extractArticle()")

        if not result.get("ok"):
            await context.close()
            print(f"[article_extractor] ❌ 提取失败: {result.get('error', 'unknown')}")
            return None

        title = result.get("title", "untitled").strip()
        md_body = result.get("markdown", "").strip()
        final_url = result.get("url", url)

        if not md_body:
            await context.close()
            print("[article_extractor] ❌ Markdown 正文为空")
            return None

        slug = _slugify(title, max_len=40)
        img_urls = re.findall(r"!\[.*?\]\((https?://[^)]+)\)", md_body)
        if img_urls:
            assets_dir = out_dir / f"{slug}_files"
            assets_dir.mkdir(parents=True, exist_ok=True)
            print(f"[article_extractor] 开始下载 {len(img_urls)} 张图片...")

            for i, img_url in enumerate(img_urls):
                ext = _guess_ext(img_url)
                img_name = f"img-{i+1:03d}{ext}"
                img_path = assets_dir / img_name
                rel_path = f"./{slug}_files/{img_name}"

                try:
                    resp = await page.request.get(img_url)
                    if resp.status == 200:
                        body = await resp.body()
                        img_path.write_bytes(body)
                        print(f"[article_extractor] 下载图片: {img_name} ({len(body)} bytes)")
                        md_body = md_body.replace(img_url, rel_path, 1)
                    else:
                        print(f"[article_extractor] ⚠️ HTTP {resp.status}，保留外链: {img_name}")
                except Exception as e:
                    print(f"[article_extractor] ⚠️ 下载失败，保留外链: {img_name} | {e}")

        await context.close()

    now = datetime.now(timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    now_date = now.strftime("%Y-%m-%d")
    tags_str = ", ".join(f'"{t}"' for t in tags) if tags else ""
    excerpt = result.get('excerpt', '从网页提取的文章') or ''
    excerpt = excerpt.replace('\n', ' ').strip()
    if len(excerpt) > 120:
        excerpt = excerpt[:117] + "..."

    md_content = f"""---
title: {title}
description: {excerpt}
date: {now_date}
source: {final_url}
tags: [{tags_str}]
---

# {title}

> 来源: [{final_url}]({final_url})
> 提取时间: {now_iso}

{md_body}
"""

    out_path = out_dir / f"{slug}.md"
    if out_path.exists():
        out_path = out_dir / f"{slug}-{now.strftime('%H%M%S')}.md"

    out_path.write_text(md_content, encoding="utf-8")
    print(f"[article_extractor] ✅ 已保存: {out_path}")
    return out_path
