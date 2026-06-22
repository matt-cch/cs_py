#!/usr/bin/env python3
"""
workflow-deploy-full.py — deploy-git-isolated 全链条部署 workflow
标签：py-tools
版本：v1.1.2 (纯 py 版全链路验证通过)

职责：编排 Step 4-9，调用 Python step 脚本，分步输出并计时。
与 PS1 版对齐：按顺序执行 add → commit → remote → push → upstream → issue sync，
任何一步失败立即停止。

用法：
    python workflow-deploy-full.py --message "feat: xxx"
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 路径常量
_PY_STEPS_DIR = Path(__file__).parent.parent / "py-steps"
_PY_EXE = Path(__file__).parent.parent.parent.parent.parent.parent / "venv" / "py" / "python.exe"


def _generate_meta(devroot: Path, message: str) -> Path:
    """
    Step 5 之后自动生成实时 comment meta。
    读取 schema 模板，用 git diff 获取变更文件，按路径前缀自动分类，
    写入 venv/tmp/workflow-meta-{timestamp}.json，返回路径供 Step 9 使用。
    """
    import json
    from datetime import datetime, timezone

    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    # 1. 获取 commit hash
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, encoding="utf-8"
    )
    commit_hash = result.stdout.strip()

    # 2. 获取变更文件列表
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "diff", "--name-status", "HEAD~1..HEAD"],
        capture_output=True, text=True, encoding="utf-8"
    )
    changes = {"A": [], "M": [], "D": [], "R": []}
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0][0]
        path = parts[-1]
        if status in changes:
            changes[status].append(path)
        else:
            changes["M"].append(path)

    # 3. 自动分类
    cats = {
        "脚本改造": [],
        "规范与模板": [],
        "文档更新": [],
        "其他": [],
    }
    for status, paths in changes.items():
        for p in paths:
            if "scripts/" in p or "py-steps/" in p or "py-tools/" in p or "ps-steps/" in p or "ps-tools/" in p:
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["脚本改造"].append(f"{label}: {p}")
            elif "schema/" in p or "json/" in p:
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["规范与模板"].append(f"{label}: {p}")
            elif "docs/" in p or "README" in p or ".md" in p:
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["文档更新"].append(f"{label}: {p}")
            else:
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["其他"].append(f"{label}: {p}")

    categories = []
    for name, items in cats.items():
        if items:
            categories.append({"name": name, "items": items})

    # 4. 构造 meta
    meta = {
        "version": "1.0.0",
        "commit_message": message,
        "summary": message,
        "categories": categories,
    }

    # 5. 写入 tmp
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    meta_path = devroot / "venv" / "tmp" / f"workflow-meta-{ts}.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[Meta] 已生成实时配置: {meta_path}")
    print(f"[Meta] 变更文件: {sum(len(v) for v in changes.values())} 个, 分类: {len(categories)} 组")
    return meta_path


def _run_py_step(name: str, script_path: Path, extra_args: list = None) -> tuple[bool, float]:
    """
    执行 Python step 脚本，实时输出，返回 (成功?, 耗时秒)。
    """
    print(f"\n{'='*50}")
    print(f"[Step] {name}")
    print(f"{'='*50}")

    cmd = [str(_PY_EXE), str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    start = time.time()
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()

        proc.wait()
        elapsed = time.time() - start

        if proc.returncode != 0:
            print(f"[FAIL] {name} 失败 (耗时 {elapsed:.2f}s)")
            return False, elapsed

        print(f"[OK] {name} 完成 (耗时 {elapsed:.2f}s)")
        return True, elapsed

    except Exception as e:
        elapsed = time.time() - start
        print(f"[FAIL] {name} 异常: {e} (耗时 {elapsed:.2f}s)")
        return False, elapsed


def main():
    parser = argparse.ArgumentParser(description="deploy-git-isolated 全链条部署 workflow")
    parser.add_argument("--devroot", default=r"D:\pjt\cursor\cs_py", help="Devroot 路径")
    parser.add_argument("--message", default="init: empty scaffold with safety gitignore", help="Commit message")
    parser.add_argument(
        "--step",
        choices=["4", "5", "6", "7", "8", "9", "all"],
        default="all",
        help="执行单步或全部 (默认 all)"
    )
    parser.add_argument("--issue", type=int, default=1, help="Issue 编号 (Step 9 用, 默认 1)")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)

    total_start = time.time()
    print(f"\n{'#'*50}")
    print("# deploy-git-isolated 全链条部署")
    print(f"# devroot: {devroot}")
    print(f"# message: {args.message}")
    print(f"{'#'*50}")

    steps = []
    meta_path = None
    if args.step in ("4", "all"):
        steps.append(("Step 4: git add", _PY_STEPS_DIR / "step-04-github-deploy-add.py", ["--devroot", str(devroot)]))
    if args.step in ("5", "all"):
        steps.append(("Step 5: git commit", _PY_STEPS_DIR / "step-05-github-commit.py", ["--devroot", str(devroot), "--message", args.message]))
    if args.step in ("9", "all"):
        # Step 5 之后自动生成 meta，供 Step 9 使用
        meta_path = _generate_meta(devroot, args.message)
    if args.step in ("6", "all"):
        steps.append(("Step 6: remote", _PY_STEPS_DIR / "step-06-github-remote.py", ["--devroot", str(devroot)]))
    if args.step in ("7", "all"):
        steps.append(("Step 7: push", _PY_STEPS_DIR / "step-07-github-push.py", ["--devroot", str(devroot)]))
    if args.step in ("8", "all"):
        steps.append(("Step 8: upstream", _PY_STEPS_DIR / "step-08-github-upstream.py", ["--devroot", str(devroot)]))
    if args.step in ("9", "all"):
        issue_args = ["--devroot", str(devroot), "--issue", str(args.issue)]
        if meta_path:
            issue_args.extend(["--meta", str(meta_path)])
        steps.append(("Step 9: issue sync", _PY_STEPS_DIR / "step-09-github-sync-issue.py", issue_args))

    all_ok = True
    for name, script, extra in steps:
        ok, elapsed = _run_py_step(name, script, extra)
        if not ok:
            all_ok = False
            break

    total_elapsed = time.time() - total_start
    print(f"\n{'#'*50}")
    if all_ok:
        print(f"# [SUCCESS] 部署完成 (总耗时 {total_elapsed:.2f}s)")
    else:
        print(f"# [FAILURE] 部署中断 (总耗时 {total_elapsed:.2f}s)")
    print(f"{'#'*50}\n")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
