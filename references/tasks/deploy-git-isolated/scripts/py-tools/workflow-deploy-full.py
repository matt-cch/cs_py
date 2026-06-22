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


def _generate_ai_summary(devroot: Path, message: str) -> str:
    """
    调用 generate-ai-summary.py 生成 AI 语义摘要。
    返回摘要文本（失败时返回空字符串）。
    """
    import json

    script = Path(__file__).parent / "generate-ai-summary.py"
    cmd = [str(_PY_EXE), str(script), "--devroot", str(devroot), "--message", message]

    print("[AI Summary] 正在生成语义摘要...")
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=300)
        elapsed = time.time() - start
        if result.returncode != 0:
            print(f"[AI Summary] 生成失败 (耗时 {elapsed:.2f}s): {result.stderr}", file=sys.stderr)
            return ""

        # 从 stdout 提取落盘路径（最后一行 [Output] 已落盘: ...）
        summary_text = ""
        for line in result.stdout.splitlines():
            if line.startswith("[Output] 已落盘:"):
                output_path = Path(line.split("已落盘:", 1)[1].strip())
                if output_path.exists():
                    data = json.loads(output_path.read_text(encoding="utf-8"))
                    summary_text = data.get("ai_summary", "")
                break

        print(f"[AI Summary] 生成完成 (耗时 {elapsed:.2f}s), 长度: {len(summary_text)} 字符")
        return summary_text
    except Exception as e:
        elapsed = time.time() - start
        print(f"[AI Summary] 异常 (耗时 {elapsed:.2f}s): {e}", file=sys.stderr)
        return ""


def _generate_meta(devroot: Path, message: str) -> Path:
    """
    Step 5 之后自动生成实时 comment meta。
    读取 schema 模板，用 git diff 获取变更文件，按路径前缀自动分类，
    同时调用 AI 生成语义摘要，写入 venv/tmp/workflow-meta-{timestamp}.json。
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

    # 4. 生成 AI 语义摘要（带 fallback：agent 异常时回退到默认全自动模式）
    ai_summary = _generate_ai_summary(devroot, message)
    if ai_summary:
        print(f"[Mode] 🧠 AI 语义层就绪 — 将生成含语义摘要的 Issue comment")
    else:
        print(f"[Mode] ⚙️ 默认全自动模式 — Agent 摘要未生成或异常，Issue comment 仅含结构化摘要")

    # 5. 构造 meta
    meta = {
        "version": "1.1.0",
        "commit_message": message,
        "summary": message,
        "categories": categories,
        "ai_summary": ai_summary,
    }

    # 6. 写入 tmp
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
    if args.step in ("4", "all"):
        steps.append(("Step 4: git add", _PY_STEPS_DIR / "step-04-github-deploy-add.py", ["--devroot", str(devroot)]))
    if args.step in ("5", "all"):
        steps.append(("Step 5: git commit", _PY_STEPS_DIR / "step-05-github-commit.py", ["--devroot", str(devroot), "--message", args.message]))
    if args.step in ("6", "all"):
        steps.append(("Step 6: remote", _PY_STEPS_DIR / "step-06-github-remote.py", ["--devroot", str(devroot)]))
    if args.step in ("7", "all"):
        steps.append(("Step 7: push", _PY_STEPS_DIR / "step-07-github-push.py", ["--devroot", str(devroot)]))
    if args.step in ("8", "all"):
        steps.append(("Step 8: upstream", _PY_STEPS_DIR / "step-08-github-upstream.py", ["--devroot", str(devroot)]))
    if args.step in ("9", "all"):
        steps.append(("Step 9: issue sync", _PY_STEPS_DIR / "step-09-github-sync-issue.py", ["--devroot", str(devroot), "--issue", str(args.issue)]))

    all_ok = True
    meta_path = None
    for idx, (name, script, extra) in enumerate(steps):
        ok, elapsed = _run_py_step(name, script, extra)
        if not ok:
            all_ok = False
            break
        # Step 5 完成后生成 meta（必须在 commit 之后，供后续 Step 9 使用）
        if name.startswith("Step 5:"):
            has_step9 = any(s[0].startswith("Step 9:") for s in steps[idx+1:])
            if has_step9:
                meta_path = _generate_meta(devroot, args.message)
                # 动态更新 Step 9 的参数
                for j in range(idx+1, len(steps)):
                    if steps[j][0].startswith("Step 9:"):
                        new_extra = list(steps[j][2])
                        new_extra.extend(["--meta", str(meta_path)])
                        steps[j] = (steps[j][0], steps[j][1], new_extra)
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
