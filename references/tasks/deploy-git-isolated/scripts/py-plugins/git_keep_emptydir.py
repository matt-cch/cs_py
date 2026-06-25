#!/usr/bin/env python3
"""
插件：Git 空目录保留器（git_keep_emptydir）
标签：git, core

职责：在 git stage 前扫描指定目录下的空子目录，自动创建 .gitkeep 占位文件，
      防止空目录因 Git 不跟踪目录而被忽略。

用法：
    registry = load_plugins(devroot=..., tags=["git"])
    result = registry.git_keep_emptydir.ensure_empty_dirs(devroot, ["references/env-migrations", "references/tasks/deploy-git-isolated"])
    # result["pass"] == True 表示全部处理完毕
"""
from pathlib import Path


def ensure_empty_dirs(devroot: Path, dirs: list[str]) -> dict:
    """
    扫描 dirs 下的空子目录，自动创建 .gitkeep。

    参数:
        devroot: devroot 绝对路径
        dirs: 相对 devroot 的目录列表（如 ["references/env-migrations"]）

    返回:
        dict: {
            "created": [创建 .gitkeep 的目录列表],
            "already_kept": [已有 .gitkeep 的目录列表],
            "pass": bool,
        }
    """
    created = []
    already_kept = []

    for rel_dir in dirs:
        base = devroot / rel_dir
        if not base.exists():
            continue

        for subdir in base.rglob("*"):
            if not subdir.is_dir():
                continue
            # 跳过 .git 目录
            if ".git" in subdir.parts:
                continue

            # 判断是否是空目录（无文件、无子目录，或只有空子目录）
            has_files = any(f.is_file() for f in subdir.iterdir())
            if has_files:
                continue

            # 空目录，检查是否已有 .gitkeep
            gitkeep = subdir / ".gitkeep"
            if gitkeep.exists():
                already_kept.append(str(subdir.relative_to(devroot)))
            else:
                gitkeep.write_text("", encoding="utf-8")
                created.append(str(subdir.relative_to(devroot)))

    if created:
        print(f"[git_keep_emptydir] 新建 .gitkeep: {len(created)} 个")
        for c in created:
            print(f"  + {c}")
    if already_kept:
        print(f"[git_keep_emptydir] 已有 .gitkeep: {len(already_kept)} 个")

    return {
        "created": created,
        "already_kept": already_kept,
        "pass": True,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("git_keep_emptydir 模块已加载")
    print("用法: from git_keep_emptydir import ensure_empty_dirs")
