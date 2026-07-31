#!/usr/bin/env python3
r"""
workflow-download-article-to-vault.py — 文章下载到 Vault Workflow  (v1.0.0)

设计意图
  编排「文章下载 → 产物验证 → Vault 目录整理 → 导航更新」完整链条，
  将 Agent 的临场后处理固化为确定性 Workflow。

核心原则
  - 不手动 preflight：download-article.py 内部已自检，Agent 直接调用
  - 单文章子目录：raw/clippings/{slug}/ 下收束 .md + _files/
  - 导航表自动维护：检测并追加/初始化 clippings/README.md 导航表

  命令行示例
    python workflow-download-article-to-vault.py \
        --devroot "{devroot}" \
        --vault-dir "{devroot}\vaults\vault-demo" \
        --url "https://www.toutiao.com/article/7667463102308286991/" \
        --tags "知识库,Tolaria" \
        --show-progress

  参数
    完整参数列表及默认值请运行: python workflow-download-article-to-vault.py --help

    | 参数            | 必填 | 默认值/说明                                              |
    |-----------------|------|----------------------------------------------------------|
    | --devroot       | 是   | 无。polyrepo 场景下必须显式传入，禁止自动推导。          |
    | --vault-dir     | 是   | {devroot}/vaults/vault-demo。未指定时命令行必须带入此值。 |
    | --url           | 是   | 无。                                                     |
    | --tags          | 否   | 无。                                                     |
    | --headed        | 否   | 无。（调试用）                                           |
    | --slug          | 否   | 无。默认从文章文件名提取。                               |
    | --dry-run       | 否   | 无。                                                     |
    | --show-progress | 否   | 无。                                                     |

    --vault-dir 强制规则
      命令行中必须出现 --vault-dir。
      若任务未提供明确 vault 路径，其值必须固定为：
        {devroot}/vaults/vault-demo
      禁止根据记忆、经验或猜测填写其他路径。

输出
  - 文章归档到 vault-dir/raw/clippings/{slug}/
  - 更新 vault-dir/raw/clippings/README.md 导航表
  - stdout 进度报告 + manifest JSON 到系统 TMP 目录（由 TMP/TEMP 环境变量决定）
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def _resolve_devroot(devroot: str | None) -> Path:
    """解析 devroot 路径。"""
    if devroot:
        return Path(devroot).resolve()
    # 默认：从脚本位置向上推导
    script_dir = Path(__file__).resolve().parent
    # scripts/py-tools/ -> references/tasks/deploy-git-isolated/scripts/py-tools/
    # 向上 4 层到 devroot
    return script_dir.parents[3]


def _progress(msg: str, show: bool = True):
    if show:
        print(msg, flush=True)


def step1_validate(devroot: Path, vault_dir: Path, show_progress: bool) -> tuple[bool, str, Path]:
    """参数与路径验证。"""
    _progress("[Step 1/8] 参数与路径验证...", show_progress)

    if not vault_dir.exists():
        return False, f"vault-dir 不存在: {vault_dir}", Path()
    _progress(f"  [OK] vault-dir: {vault_dir}", show_progress)

    clippings_dir = vault_dir / "raw" / "clippings"
    if not clippings_dir.exists():
        return False, f"raw/clippings/ 不存在: {clippings_dir}", Path()
    _progress(f"  [OK] clippings/: {clippings_dir}", show_progress)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    temp_dir = devroot / "venv" / "tmp" / f"article-download-{ts}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    _progress(f"  [OK] 临时目录: {temp_dir}", show_progress)

    return True, "", temp_dir


def step2_download(
    devroot: Path,
    url: str,
    temp_dir: Path,
    tags: list[str] | None,
    headed: bool,
    show_progress: bool,
) -> tuple[bool, str, Path]:
    """调用 download-article.py。"""
    _progress("[Step 2/8] 调用 download-article.py...", show_progress)

    cmd = [
        str(devroot / "venv" / "py" / "python.exe"),
        str(devroot / "references" / "tasks" / "deploy-git-isolated" / "scripts" / "py-tools" / "download-article.py"),
        "--devroot", str(devroot),
        "--url", url,
        "--output-dir", str(temp_dir),
    ]
    if tags:
        cmd.extend(["--tags", ",".join(tags)])
    if headed:
        cmd.append("--headed")

    _progress(f"  命令: {' '.join(cmd[:6])} ...", show_progress)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        _progress(result.stdout, show_progress)
        if result.returncode != 0:
            return False, f"download-article.py 失败: {result.stderr}", Path()
    except subprocess.TimeoutExpired:
        return False, "download-article.py 超时（120s）", Path()
    except Exception as e:
        return False, f"调用 download-article.py 异常: {e}", Path()

    # 查找生成的 .md 文件
    md_files = list(temp_dir.glob("*.md"))
    if not md_files:
        return False, "临时目录中未找到 .md 文件", Path()

    return True, "", md_files[0]


def step3_verify(temp_dir: Path, md_file: Path, show_progress: bool) -> tuple[bool, str, Path, int]:
    """产物验证。"""
    _progress("[Step 3/8] 产物验证...", show_progress)

    if not md_file.exists():
        return False, ".md 文件不存在", Path(), 0
    _progress(f"  [OK] .md 文件: {md_file.name}", show_progress)

    # 查找 _files/ 目录
    img_dirs = list(temp_dir.glob("*_files"))
    if not img_dirs:
        # 可能没有图片
        img_dir = None
        img_count = 0
    else:
        img_dir = img_dirs[0]
        img_count = len(list(img_dir.glob("*")))
        _progress(f"  [OK] _files/ 目录: {img_dir.name} ({img_count} 张图片)", show_progress)

    # 验证 Markdown 内图片引用
    content = md_file.read_text(encoding="utf-8")
    img_refs = len(re.findall(r"!\[.*?\]\(.*?\)", content))

    if img_dir and img_count != img_refs:
        return False, f"图片数量不匹配: {img_count} vs {img_refs}", Path(), 0

    if img_refs > 0:
        _progress(f"  [OK] 图片引用: {img_refs} 处，全部有效", show_progress)
    else:
        _progress("  [OK] 无图片", show_progress)

    return True, "", img_dir, img_count


def step4_extract_id(md_file: Path, show_progress: bool) -> tuple[bool, str, str, str]:
    """提取文章标识。"""
    _progress("[Step 4/8] 提取文章标识...", show_progress)

    content = md_file.read_text(encoding="utf-8")

    # 提取 frontmatter title
    title = md_file.stem  # fallback
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        t_match = re.search(r"^title:\s*(.+)$", fm, re.MULTILINE)
        if t_match:
            title = t_match.group(1).strip().strip('"\'')

    # source
    source = ""
    if fm_match:
        fm = fm_match.group(1)
        s_match = re.search(r"^source:\s*(.+)$", fm, re.MULTILINE)
        if s_match:
            source = s_match.group(1).strip().strip('"\'')

    slug = md_file.stem  # 默认从文件名提取

    _progress(f"  [OK] title: {title}", show_progress)
    _progress(f"  [OK] slug: {slug}", show_progress)
    if source:
        _progress(f"  [OK] source: {source}", show_progress)

    return True, "", title, slug


def step5_create_dir(clippings_dir: Path, slug: str, show_progress: bool, dry_run: bool) -> tuple[bool, str, Path]:
    """创建 Vault 子目录。"""
    _progress("[Step 5/8] 创建 Vault 子目录...", show_progress)

    target_dir = clippings_dir / slug
    if target_dir.exists():
        return False, f"子目录已存在: {target_dir}", Path()

    if dry_run:
        _progress(f"  [DRY-RUN] 将创建: {target_dir}", show_progress)
        return True, "", target_dir

    target_dir.mkdir(parents=True, exist_ok=False)
    _progress(f"  [OK] 新建: {target_dir}", show_progress)
    return True, "", target_dir


def step6_move(
    md_file: Path,
    img_dir: Path | None,
    target_dir: Path,
    show_progress: bool,
    dry_run: bool,
) -> tuple[bool, str]:
    """整目录移入。"""
    _progress("[Step 6/8] 整目录移入...", show_progress)

    if dry_run:
        _progress(f"  [DRY-RUN] 将移动: {md_file.name} -> {target_dir}", show_progress)
        if img_dir:
            _progress(f"  [DRY-RUN] 将移动: {img_dir.name} -> {target_dir}", show_progress)
        return True, ""

    shutil.move(str(md_file), str(target_dir))
    _progress(f"  [OK] 移动: {md_file.name}", show_progress)

    if img_dir and img_dir.exists():
        shutil.move(str(img_dir), str(target_dir))
        _progress(f"  [OK] 移动: {img_dir.name}", show_progress)

    # 移入后验证
    moved_md = list(target_dir.glob("*.md"))
    if not moved_md:
        return False, "移入后 .md 文件丢失"

    content = moved_md[0].read_text(encoding="utf-8")
    img_refs_after = len(re.findall(r"!\[.*?\]\(.*?\)", content))
    if img_refs_after > 0:
        # 检查图片文件是否存在
        img_dirs_after = list(target_dir.glob("*_files"))
        if img_dirs_after:
            for ref in re.findall(r"!\[.*?\]\(.*?\)", content):
                img_path_match = re.search(r"\(\.?/?(.+?)\)", ref)
                if img_path_match:
                    rel_path = img_path_match.group(1)
                    actual = target_dir / rel_path.replace("/", "\\")
                    if not actual.exists():
                        return False, f"移入后图片路径失效: {rel_path}"

    _progress("  [OK] 移入后路径验证通过", show_progress)
    return True, ""


def step7_update_nav(clippings_dir: Path, slug: str, title: str, date_str: str, source: str, show_progress: bool, dry_run: bool) -> tuple[bool, str]:
    """更新导航表。"""
    _progress("[Step 7/8] 更新导航表...", show_progress)

    readme_path = clippings_dir / "README.md"
    nav_line = f"| `{slug}/` | {title} | {date_str} | {source} |\n"

    if dry_run:
        _progress(f"  [DRY-RUN] 将追加到: {readme_path}", show_progress)
        _progress(f"  [DRY-RUN] 内容: {nav_line.strip()}", show_progress)
        return True, ""

    if not readme_path.exists():
        _progress("  [WARN] README.md 不存在，创建新文件", show_progress)
        readme_content = f"""---
title: raw/clippings
---

## 剪藏列表

| slug | 标题 | 日期 | 来源 |
|------|------|------|------|
{nav_line}
"""
        readme_path.write_text(readme_content, encoding="utf-8")
        _progress("  [OK] 新建 README.md 并写入导航表", show_progress)
        return True, ""

    content = readme_path.read_text(encoding="utf-8")

    # 检查是否已有导航表
    if "## 剪藏列表" in content:
        # 在表格末尾追加
        # 找到最后一个 |...| 行，在其后追加
        lines = content.splitlines(keepends=True)
        insert_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith("|"):
                insert_idx = i + 1
                break
        lines.insert(insert_idx, nav_line)
        readme_path.write_text("".join(lines), encoding="utf-8")
        _progress("  [OK] 已追加到剪藏列表", show_progress)
    else:
        # 在文件末尾追加导航表
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write("\n## 剪藏列表\n\n")
            f.write("| slug | 标题 | 日期 | 来源 |\n")
            f.write("|------|------|------|------|\n")
            f.write(nav_line)
        _progress("  [OK] 新建剪藏列表并写入", show_progress)

    return True, ""


def step8_cleanup(devroot: Path, temp_dir: Path, target_dir: Path, manifest: dict, show_progress: bool, dry_run: bool) -> tuple[bool, str]:
    r"""清理临时目录并输出 manifest。

    设计意图
      - manifest 是运行侧审计产物，不耦合 vault 目录结构。
      - 落盘位置由 manifest_path 插件统一决定（TMP/TEMP 优先，
        fallback 到 devroot/venv/tmp/），脚本自身不硬编码路径。
      - 遵循 baseline-plugin-architecture.md §8.4.8 与
        baseline-workflow-deploy.md §8.9 的产物落盘规范。
    """
    _progress("[Step 8/8] 清理临时目录...", show_progress)

    if dry_run:
        _progress("  [DRY-RUN] 跳过清理", show_progress)
    else:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            _progress("  [OK] 已删除临时目录", show_progress)

    # manifest 落盘路径由 manifest_path 插件统一决定
    _scripts_dir = Path(__file__).parent.parent.resolve()
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from py_lib import load_plugins
    registry = load_plugins(devroot=str(devroot), tags=["utility"])
    manifest_path = registry.manifest_path
    manifest_file = manifest_path.build_manifest_path(
        devroot,
        tool_name="workflow-download-article",
        suffix="manifest",
        ext="json",
    )
    manifest_dir = manifest_file.parent
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    _progress("", show_progress)
    _progress("=" * 50, show_progress)
    _progress("[SUCCESS] 文章已归档到:", show_progress)
    _progress(f"  {target_dir}", show_progress)
    _progress("", show_progress)
    _progress("Manifest:", show_progress)
    _progress(json.dumps(manifest, ensure_ascii=False, indent=2), show_progress)

    return True, ""


def main():
    parser = argparse.ArgumentParser(description="文章下载到 Vault Workflow")
    parser.add_argument("--devroot", default=None, required=True, help="devroot 路径（必填）。polyrepo 场景下必须显式传入，禁止依赖脚本位置的自动推导。")
    parser.add_argument("--vault-dir", default=None, required=True, help="目标 vault 目录（必填）。默认值: {devroot}/vaults/vault-demo。未从外部获得明确路径时，必须使用此默认值，禁止自行推断其他路径。")
    parser.add_argument("--url", required=True, help="文章 URL（必填）")
    parser.add_argument("--tags", default=None, help="标签列表，逗号分隔（可选）")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口（调试用，可选）")
    parser.add_argument("--slug", default=None, help="自定义子目录 slug（默认从文章文件名提取，可选）")
    parser.add_argument("--dry-run", action="store_true", help="只检测和输出计划，不实际移动文件（可选）")
    parser.add_argument("--show-progress", action="store_true", help="实时输出每步进度（可选）")
    args = parser.parse_args()

    devroot = _resolve_devroot(args.devroot)
    vault_dir = Path(args.vault_dir).resolve() if args.vault_dir else devroot / "vaults" / "vault-demo"
    clippings_dir = vault_dir / "raw" / "clippings"
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
    show_progress = args.show_progress
    dry_run = args.dry_run

    if show_progress:
        print(f"devroot: {devroot}")
        print(f"vault-dir: {vault_dir}")
        print(f"url: {args.url}")
        if dry_run:
            print("[DRY-RUN] 模式：不实际移动文件")
        print("")

    # Step 1
    (_t0 := time.perf_counter())
    ok, reason, temp_dir = step1_validate(devroot, vault_dir, show_progress)
    _elapsed = time.perf_counter() - _t0
    if show_progress:
        print(f"  ⏱ {_elapsed:.1f}s")
    if not ok:
        print(f"[Step 1/8] ❌ {reason}")
        sys.exit(1)

    # Step 2
    (_t0 := time.perf_counter())
    ok, reason, md_file = step2_download(devroot, args.url, temp_dir, tags, args.headed, show_progress)
    _elapsed = time.perf_counter() - _t0
    if show_progress:
        print(f"  ⏱ {_elapsed:.1f}s")
    if not ok:
        print(f"[Step 2/8] ❌ {reason}")
        sys.exit(1)

    # Step 3
    (_t0 := time.perf_counter())
    ok, reason, img_dir, img_count = step3_verify(temp_dir, md_file, show_progress)
    _elapsed = time.perf_counter() - _t0
    if show_progress:
        print(f"  ⏱ {_elapsed:.1f}s")
    if not ok:
        print(f"[Step 3/8] ❌ {reason}")
        sys.exit(1)

    # Step 4
    (_t0 := time.perf_counter())
    ok, reason, title, slug = step4_extract_id(md_file, show_progress)
    _elapsed = time.perf_counter() - _t0
    if show_progress:
        print(f"  ⏱ {_elapsed:.1f}s")
    if not ok:
        print(f"[Step 4/8] ❌ {reason}")
        sys.exit(1)

    # 自定义 slug
    if args.slug:
        slug = args.slug
        if show_progress:
            print(f"  [OVERRIDE] 使用自定义 slug: {slug}")

    # Step 5
    (_t0 := time.perf_counter())
    ok, reason, target_dir = step5_create_dir(clippings_dir, slug, show_progress, dry_run)
    _elapsed = time.perf_counter() - _t0
    if show_progress:
        print(f"  ⏱ {_elapsed:.1f}s")
    if not ok:
        print(f"[Step 5/8] ❌ {reason}")
        sys.exit(1)

    # Step 6
    (_t0 := time.perf_counter())
    ok, reason = step6_move(md_file, img_dir, target_dir, show_progress, dry_run)
    _elapsed = time.perf_counter() - _t0
    if show_progress:
        print(f"  ⏱ {_elapsed:.1f}s")
    if not ok:
        print(f"[Step 6/8] ❌ {reason}")
        sys.exit(1)

    # Step 7
    (_t0 := time.perf_counter())
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    source = args.url
    ok, reason = step7_update_nav(clippings_dir, slug, title, date_str, source, show_progress, dry_run)
    _elapsed = time.perf_counter() - _t0
    if show_progress:
        print(f"  ⏱ {_elapsed:.1f}s")
    if not ok:
        print(f"[Step 7/8] ❌ {reason}")
        sys.exit(1)

    # Step 8
    (_t0 := time.perf_counter())
    manifest = {
        "url": args.url,
        "title": title,
        "slug": slug,
        "target_path": str(target_dir),
        "image_count": img_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
    }
    ok, reason = step8_cleanup(devroot, temp_dir, target_dir, manifest, show_progress, dry_run)
    _elapsed = time.perf_counter() - _t0
    if show_progress:
        print(f"  ⏱ {_elapsed:.1f}s")
    if not ok:
        print(f"[Step 8/8] ❌ {reason}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
