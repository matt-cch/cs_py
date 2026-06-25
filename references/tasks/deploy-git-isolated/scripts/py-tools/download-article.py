import argparse
import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

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
    from article_extractor import extract_article
else:
    from article_extractor import extract_article


def main():
    parser = argparse.ArgumentParser(description="头条文章正文下载工具")
    parser.add_argument("--url", required=True, help="文章 URL")
    parser.add_argument("--tags", default=None, help="逗号分隔的标签，如 AI,编程")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认 devroot/out/articles/）")
    parser.add_argument("--headless", action="store_true", default=True, help="无头模式（默认开启）")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--devroot", default=None, help="devroot 路径（默认自动探测）")
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
    headless = not args.headed if args.headed else args.headless

    if HAS_PY_LIB and args.devroot:
        registry = load_plugins(devroot=args.devroot, tags=["extraction"])
        extract_article = registry.article_extractor.extract_article

    out_path = asyncio.run(extract_article(
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
