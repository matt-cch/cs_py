#!/usr/bin/env python3
r"""
atomic-npm-isolated-install.py — npm 隔离安装原子 CLI
标签：py-tools
版本：v1.2.0

【设计意图】
  将 npm 包安全安装到隔离目录，作为独立工具链使用。
  改造自 PowerShell 版 install-isolated.ps1，迁移到 Python 原子脚本体系，
  统一走 py-tools/ 层标准：参数化、可编排、manifest 可追溯、show-progress 可观测。

  核心谨慎原则：
    1. Local 模式下必须物理 cd 进目标目录执行 npm init/install，cd 后立即验证 CWD。
    2. Local 模式下若目标目录已有 node_modules 但无 package.json，必须阻止执行——
       否则 npm 会重组删除所有不属于新依赖树的包（包括 npm 自身）。
    3. Global 模式完全无状态，不生成 package.json/lock，也不触发重组风险，因此
       不执行 npm init，也不做重组安全检查。
    4. 安装前验证 node.exe 身份（process.execPath 必须等于传入路径），防止 shim/
       wrapper 导致调用链错位。
    5. 安装后验证 node_modules/<pkg>/package.json 存在性，若提供 --bin-name 则
       额外验证 .bin 入口并输出实测路径。
    6. show-progress 模式下 npm 输出直通终端，用户实时观测下载进度；静默模式下
       stdout/stderr 被捕获，供 pipeline 或日志系统消费。
    7. 所有 stdout 输出强制 flush，确保脚本框架输出与 npm 子进程输出的时序正确
       （避免 npm 实时输出抢先出现在脚本标题之前）。

【职责】
  - Local 模式（默认）：cd → npm init -y → npm install <pkg>
    产物：package.json + package-lock.json + node_modules/
  - Global 模式：npm --prefix <dir> -g install <pkg>
    产物：node_modules/（无 package.json/lock）

【依赖】
  底层能力：无（纯 Python 标准库 + subprocess，零外部依赖）
  外部工具：node.exe、npm.cmd（路径推导或显式传入）

【预检】
  - --target-dir 必须提供且为绝对路径
  - --package 必须提供
  - node.exe 必须可执行且 process.execPath 匹配
  - npm.cmd 必须与 node.exe 同级

【调用参数】
  --target-dir      <str, 必填>  目标隔离目录绝对路径
  --package         <str, 必填>  npm 包名（如 scriptc、uipro-cli）
  --mode            <str, 可选>  安装模式: local（默认）| global
  --version         <str, 可选>  指定版本号，如 "2.2.3"
  --bin-name        <str, 可选>  期望的 bin 命令名（如 scriptc），用于安装后验证
  --node-path       <str, 可选>  node.exe 绝对路径（默认从 devroot 推导）
  --devroot         <str, 可选>  devroot 路径（默认从脚本位置向上推导）
  --show-progress   <flag, 可选> 显示 npm 实时进度输出（默认静默，捕获 stdout/stderr）
  --output          <str, 可选>  manifest 输出路径（未传时自动生成到 venv/tmp/）

【用法示例】
  # Local 模式（默认）—— 产物含 package.json + package-lock.json
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-npm-isolated-install.py" `
      --target-dir "${devroot}\venv\scriptc" `
      --package "scriptc" `
      --bin-name "scriptc"

  # Global 模式 + 显示进度
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-npm-isolated-install.py" `
      --target-dir "${devroot}\venv\scriptc" `
      --package "scriptc" `
      --mode global `
      --bin-name "scriptc" `
      --show-progress

【返回码】
  0 — 安装成功且验证通过
  1 — 前置检查失败 / node 身份验证失败 / npm 安装失败 / 验证失败
  50 — Local 模式安全阻止：目标目录已有 node_modules 但无 package.json（重组风险）
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# =============================================================================
# 工具函数
# =============================================================================
def _ts() -> str:
    """返回当前本地时间戳字符串，用于步骤输出。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _fmt_cmd(cmd: list[str], cwd: str | None = None) -> str:
    """将命令列表格式化为人类可读的命令行字符串。"""
    parts = [f'"{c}"' if " " in c else c for c in cmd]
    s = " ".join(parts)
    if cwd:
        s += f"  (CWD: {cwd})"
    return s


def _sep_line(char: str = "─", length: int = 50) -> str:
    return char * length


# =============================================================================
# 路径推导
# =============================================================================
def _resolve_devroot(cli_devroot: str | None) -> Path:
    """推断 devroot：优先 CLI 参数，其次脚本位置向上回溯。"""
    if cli_devroot:
        p = Path(cli_devroot).resolve()
        if p.exists():
            return p
    current = Path(__file__).resolve()
    for _ in range(6):
        if current.parent == current:
            break
        current = current.parent
    if (current / "venv").exists():
        return current
    raise RuntimeError("无法自动推断 devroot：未找到 venv/ 目录")


def _resolve_node_path(cli_node_path: str | None, devroot: Path) -> Path:
    """推断 node.exe 路径。"""
    if cli_node_path:
        p = Path(cli_node_path).resolve()
        if p.exists():
            return p
    candidate = devroot / "venv" / "node" / "node.exe"
    if candidate.exists():
        return candidate
    raise RuntimeError(f"未找到 node.exe: {candidate}")


def _resolve_npm_path(node_path: Path) -> Path:
    """npm.cmd 必须与 node.exe 同级。"""
    npm_cmd = node_path.parent / "npm.cmd"
    if npm_cmd.exists():
        return npm_cmd
    raise RuntimeError(f"未找到 npm.cmd: {npm_cmd}")


# =============================================================================
# 验证
# =============================================================================
def _verify_node_identity(node_path: Path, show_progress: bool) -> tuple[bool, dict]:
    """验证 node.exe 身份：process.execPath 必须等于传入路径。返回 (通过?, 步骤记录)。"""
    step = {"label": "验证 node.exe 身份", "cmd": _fmt_cmd([str(node_path), "-e", "console.log(process.execPath)"])}
    t0 = time.perf_counter()
    try:
        result = subprocess.run(
            [str(node_path), "-e", "console.log(process.execPath)"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = time.perf_counter() - t0
        step["exit_code"] = result.returncode
        step["elapsed_sec"] = round(elapsed, 2)
        if result.returncode != 0:
            step["status"] = "FAIL"
            step["error"] = result.stderr.strip()
            return False, step
        actual = result.stdout.strip()
        if actual.lower() == str(node_path).lower():
            step["status"] = "OK"
            step["detail"] = f"process.execPath = {actual}"
            return True, step
        else:
            step["status"] = "FAIL"
            step["error"] = f"process.execPath 不匹配: 预期 {node_path}, 实际 {actual}"
            return False, step
    except Exception as e:
        elapsed = time.perf_counter() - t0
        step["exit_code"] = -1
        step["elapsed_sec"] = round(elapsed, 2)
        step["status"] = "FAIL"
        step["error"] = str(e)
        return False, step


def _verify_npm_available(npm_path: Path, show_progress: bool) -> tuple[bool, dict]:
    """验证 npm 可用性。返回 (通过?, 步骤记录)。"""
    step = {"label": "验证 npm 可用性", "cmd": _fmt_cmd([str(npm_path), "--version"])}
    t0 = time.perf_counter()
    try:
        result = subprocess.run(
            [str(npm_path), "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = time.perf_counter() - t0
        step["exit_code"] = result.returncode
        step["elapsed_sec"] = round(elapsed, 2)
        if result.returncode != 0:
            step["status"] = "FAIL"
            step["error"] = result.stderr.strip()
            return False, step
        version = result.stdout.strip()
        step["status"] = "OK"
        step["detail"] = f"npm v{version}"
        return True, step
    except Exception as e:
        elapsed = time.perf_counter() - t0
        step["exit_code"] = -1
        step["elapsed_sec"] = round(elapsed, 2)
        step["status"] = "FAIL"
        step["error"] = str(e)
        return False, step


# =============================================================================
# 安全检查
# =============================================================================
def _check_reorg_risk(target_dir: Path) -> tuple[bool, str, dict]:
    """
    Local 模式重组风险检查。
    逐条检查目标目录状态，若已有 node_modules 但无 package.json，npm install 会重组删除所有
    不属于新依赖树的包。返回 (安全?, 说明, 详细检查项)。
    """
    has_node_modules = (target_dir / "node_modules").exists()
    has_package_json = (target_dir / "package.json").exists()
    details = {
        "target_dir": str(target_dir),
        "node_modules_exists": has_node_modules,
        "package_json_exists": has_package_json,
        "risk_detected": False,
    }
    if has_node_modules and not has_package_json:
        details["risk_detected"] = True
        return (
            False,
            f"安全阻止: 目标目录已有 node_modules 但缺少 package.json。"
            f"直接执行 npm install 会触发重组，删除所有不属于新依赖树的包。"
            f"建议: 改用 Global 模式，或先手动清理目录后重试。",
            details,
        )
    return True, "安全检查通过", details


def _verify_cwd_switched(expected: Path) -> tuple[bool, dict]:
    """验证 cd 后 CWD 确实切换到了预期目录。返回 (通过?, 步骤记录)。"""
    step = {"label": "验证 CWD 切换", "cmd": f"os.chdir({expected})"}
    t0 = time.perf_counter()
    actual = Path.cwd().resolve()
    expected_resolved = expected.resolve()
    elapsed = time.perf_counter() - t0
    step["elapsed_sec"] = round(elapsed, 2)
    step["check_items"] = {
        "expected_cwd": str(expected_resolved),
        "actual_cwd": str(actual),
        "matched": actual == expected_resolved,
    }
    if actual == expected_resolved:
        step["status"] = "OK"
        step["detail"] = f"CWD 已正确切换: {actual}"
        return True, step
    else:
        step["status"] = "FAIL"
        step["error"] = f"CWD 切换失败: 预期 {expected_resolved}, 实际 {actual}"
        return False, step


# =============================================================================
# npm 命令统一执行器
# =============================================================================
def _run_npm_cmd(
    npm_path: Path,
    args: list[str],
    cwd: str | None,
    show_progress: bool,
    label: str,
    timeout: int = 300,
) -> tuple[int, str | None, dict]:
    """
    统一执行 npm 命令。

    show_progress=True  : stdout/stderr 直通终端，用户实时观测 npm 进度条
    show_progress=False : stdout/stderr 被捕获，供 pipeline/日志消费

    返回 (exit_code, stderr_or_None, step_record)
    """
    cmd = [str(npm_path)] + args
    cmd_str = _fmt_cmd(cmd, cwd)
    step = {"label": label, "cmd": cmd_str}
    t0 = time.perf_counter()

    if show_progress:
        # 直通模式：用户看到 npm 自带进度条
        print(f"  {_sep_line()}")
        print(f"  [实时输出开始]")
        try:
            subprocess.run(
                cmd,
                cwd=cwd,
                stdout=None,
                stderr=None,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - t0
            step["elapsed_sec"] = round(elapsed, 2)
            step["status"] = "FAIL"
            step["error"] = f"命令超时 ({timeout}s)"
            print(f"  [实时输出结束 — 超时]")
            print(f"  {_sep_line()}")
            return -1, f"超时 ({timeout}s)", step

        # 重新静默执行一次以获取准确的 exit_code
        check_result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = time.perf_counter() - t0
        step["elapsed_sec"] = round(elapsed, 2)
        step["exit_code"] = check_result.returncode

        print(f"  [实时输出结束]")
        print(f"  {_sep_line()}")

        if check_result.returncode != 0:
            step["status"] = "FAIL"
            step["error"] = check_result.stderr.strip() if check_result.stderr else "未知错误"
            return check_result.returncode, check_result.stderr.strip() if check_result.stderr else None, step
        else:
            step["status"] = "OK"
            return 0, None, step
    else:
        # 静默模式：捕获 stdout/stderr
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - t0
            step["elapsed_sec"] = round(elapsed, 2)
            step["status"] = "FAIL"
            step["error"] = f"命令超时 ({timeout}s)"
            return -1, f"超时 ({timeout}s)", step

        elapsed = time.perf_counter() - t0
        step["elapsed_sec"] = round(elapsed, 2)
        step["exit_code"] = result.returncode
        if result.returncode != 0:
            step["status"] = "FAIL"
            step["error"] = result.stderr.strip() if result.stderr else "未知错误"
            return result.returncode, result.stderr.strip() if result.stderr else None, step
        else:
            step["status"] = "OK"
            return 0, None, step


# =============================================================================
# 安装后验证
# =============================================================================
def _verify_installation(target_dir: Path, pkg_name: str, bin_name: str | None, mode: str) -> dict:
    """验证安装结果。返回结构化验证报告（含 bin 实测路径）。"""
    report = {
        "pkg_dir_exists": False,
        "pkg_meta_exists": False,
        "pkg_entry_exists": False,
        "bin_exists": False,
        "bin_detail": None,
        "bin_paths": [],
        "pkg_version": None,
    }

    pkg_dir = target_dir / "node_modules" / pkg_name
    pkg_meta = pkg_dir / "package.json"

    report["pkg_dir_exists"] = pkg_dir.exists()
    if not report["pkg_dir_exists"]:
        return report

    report["pkg_meta_exists"] = pkg_meta.exists()
    if report["pkg_meta_exists"]:
        try:
            pkg_json = json.loads(pkg_meta.read_text(encoding="utf-8"))
            report["pkg_version"] = pkg_json.get("version")
        except Exception:
            pass

    if report["pkg_meta_exists"]:
        try:
            pkg_json = json.loads(pkg_meta.read_text(encoding="utf-8"))
            entry = None
            bin_field = pkg_json.get("bin")
            if isinstance(bin_field, str):
                entry = pkg_dir / bin_field.replace("/", os.sep)
            elif isinstance(bin_field, dict):
                first_val = next(iter(bin_field.values()), None)
                if first_val:
                    entry = pkg_dir / first_val.replace("/", os.sep)
            if not entry or not entry.exists():
                main_field = pkg_json.get("main")
                if main_field:
                    entry = pkg_dir / main_field.replace("/", os.sep)
            if not entry or not entry.exists():
                for cand in ("index.js", "index.mjs", "dist/index.js", "lib/index.js"):
                    c = pkg_dir / cand
                    if c.exists():
                        entry = c
                        break
            if entry and entry.exists():
                report["pkg_entry_exists"] = True
                report["pkg_entry_path"] = str(entry)
        except Exception:
            pass

    if bin_name:
        if mode == "local":
            bin_dir = target_dir / "node_modules" / ".bin"
            bin_win = bin_dir / f"{bin_name}.cmd"
            bin_posix = bin_dir / bin_name
            bw = bin_win.exists()
            bp = bin_posix.exists()
            report["bin_exists"] = bw or bp
            paths = []
            if bw:
                paths.append(str(bin_win))
            if bp:
                paths.append(str(bin_posix))
            report["bin_paths"] = paths
            if bw and bp:
                report["bin_detail"] = f"Win+POSIX 入口均存在: {', '.join(paths)}"
            elif bw:
                report["bin_detail"] = f"Win 入口存在: {bin_win}"
            elif bp:
                report["bin_detail"] = f"POSIX 入口存在: {bin_posix}"
            else:
                report["bin_detail"] = "入口缺失"
        else:
            if report.get("pkg_entry_exists"):
                report["bin_exists"] = True
                report["bin_paths"] = [report.get("pkg_entry_path", "")]
                report["bin_detail"] = f"bin 指向文件存在（Global 模式无 .bin 链接）: {report.get('pkg_entry_path', '')}"
            else:
                report["bin_exists"] = False
                report["bin_detail"] = "bin 指向文件缺失"

    return report


def _test_bin_executable(bin_path: str) -> dict:
    """
    验证 bin 文件是否可实际执行。
    优先尝试 --version，失败则尝试 --help。
    返回结构化测试结果（含命令、退出码、输出预览、耗时）。
    """
    result = {
        "bin_path": bin_path,
        "tested_cmd": None,
        "exit_code": None,
        "stdout_preview": None,
        "stderr_preview": None,
        "elapsed_sec": None,
        "status": "SKIP",
        "usable": False,
    }

    for flag in ("--version", "--help"):
        cmd = [bin_path, flag]
        cmd_str = _fmt_cmd(cmd)
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - t0
            result["elapsed_sec"] = round(elapsed, 2)
            result["tested_cmd"] = cmd_str
            result["exit_code"] = -1
            result["status"] = "TIMEOUT"
            return result
        except Exception as e:
            elapsed = time.perf_counter() - t0
            result["elapsed_sec"] = round(elapsed, 2)
            result["tested_cmd"] = cmd_str
            result["exit_code"] = -1
            result["stderr_preview"] = str(e)
            result["status"] = "ERROR"
            return result

        elapsed = time.perf_counter() - t0
        result["elapsed_sec"] = round(elapsed, 2)
        result["tested_cmd"] = cmd_str
        result["exit_code"] = proc.returncode

        # stdout/stderr 取前 3 行作为预览
        def _preview(text: str, max_lines: int = 3, max_len: int = 200) -> str | None:
            if not text:
                return None
            lines = text.strip().splitlines()[:max_lines]
            s = "\\n".join(lines)
            if len(s) > max_len:
                s = s[:max_len] + "..."
            return s

        result["stdout_preview"] = _preview(proc.stdout)
        result["stderr_preview"] = _preview(proc.stderr)

        if proc.returncode == 0:
            result["status"] = "OK"
            result["usable"] = True
            return result
        # --version 失败，继续尝试 --help

    # 两个命令都失败
    result["status"] = "FAIL"
    result["usable"] = False
    return result


def _collect_artifacts(target_dir: Path, pkg_name: str, mode: str) -> list[str]:
    """收集本步产生的产物路径列表。"""
    artifacts = []
    if mode == "local":
        for f in ("package.json", "package-lock.json"):
            p = target_dir / f
            if p.exists():
                artifacts.append(str(p))
    pkg_dir = target_dir / "node_modules" / pkg_name
    if pkg_dir.exists():
        artifacts.append(str(pkg_dir / "package.json"))
    bin_dir = target_dir / "node_modules" / ".bin"
    if bin_dir.exists():
        artifacts.append(str(bin_dir))
    return artifacts


# =============================================================================
# Manifest
# =============================================================================
def _save_manifest(devroot: Path, data: dict, output_path: str | None) -> Path:
    """落盘 manifest JSON 到 venv/tmp/ 或指定路径。"""
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"npm-isolated-install-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 步骤输出格式化
# =============================================================================
def _print_step_header(step_num: int | None, description: str):
    print("")
    if step_num is not None:
        print(f"[{_ts()}] [Step {step_num}] {description}")
    else:
        print(f"[{_ts()}] {description}")


def _print_step_footer(step: dict, artifacts: list[str] | None = None):
    """打印步骤footer：退出码、耗时、产物。"""
    exit_code = step.get("exit_code")
    elapsed = step.get("elapsed_sec")
    status = step.get("status", "?")
    parts = []
    if exit_code is not None:
        parts.append(f"退出码: {exit_code}")
    if elapsed is not None:
        parts.append(f"耗时: {elapsed:.2f}s")
    if parts:
        print(f"  {' | '.join(parts)}  [{status}]")
    if artifacts:
        print(f"  产物: {', '.join(artifacts)}")


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    """
    入口函数。内部替换 sys.stdout 为行缓冲模式（确保与 npm 子进程输出时序正确），
    并在 finally 中恢复，避免全局污染。
    """
    original_stdout = sys.stdout
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            errors="replace",
            line_buffering=True,
        )
        _main_core()
    finally:
        sys.stdout = original_stdout


def _main_core():
    parser = argparse.ArgumentParser(description="npm 隔离安装原子工具")
    parser.add_argument("--target-dir", required=True, help="目标隔离目录绝对路径")
    parser.add_argument("--package", required=True, help="npm 包名")
    parser.add_argument("--mode", choices=["local", "global"], default="local", help="安装模式: local（默认）| global")
    parser.add_argument("--version", default=None, help="指定版本号，如 2.2.3")
    parser.add_argument("--bin-name", default=None, help="期望的 bin 命令名，用于安装后验证")
    parser.add_argument("--node-path", default=None, help="node.exe 绝对路径（默认推导）")
    parser.add_argument("--devroot", default=None, help="devroot 路径（默认推导）")
    parser.add_argument("--show-progress", action="store_true", help="显示 npm 实时进度输出")
    parser.add_argument("--output", default=None, help="manifest 输出路径（未传时自动生成）")
    args = parser.parse_args()

    target_dir = Path(args.target_dir).resolve()
    pkg_name = args.package
    mode = args.mode
    pkg_version = args.version
    bin_name = args.bin_name
    show_progress = args.show_progress

    full_pkg = f"{pkg_name}@{pkg_version}" if pkg_version else pkg_name
    steps: list[dict] = []

    # 初始化 manifest
    manifest = {
        "atomic_tool": "atomic-npm-isolated-install",
        "version": "1.2.0",
        "target_dir": str(target_dir),
        "package": pkg_name,
        "full_package": full_pkg,
        "mode": mode,
        "bin_name": bin_name,
        "show_progress": show_progress,
        "node_path": None,
        "npm_path": None,
        "steps": steps,
        "verification": {},
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    print("=" * 60)
    print("[npm Isolated Install] 原子安装工具 v1.2.0")
    print("=" * 60)
    print(f"  Package       : {full_pkg}")
    print(f"  TargetDir     : {target_dir}")
    print(f"  Mode          : {mode}")
    print(f"  ShowProgress  : {show_progress}")
    print(f"  BinName       : {bin_name or '(未指定)'}")

    # -------------------------------------------------------------------------
    # 1. 路径推导
    # -------------------------------------------------------------------------
    _print_step_header(None, "路径推导")
    try:
        devroot = _resolve_devroot(args.devroot)
        node_path = _resolve_node_path(args.node_path, devroot)
        npm_path = _resolve_npm_path(node_path)
        manifest["node_path"] = str(node_path)
        manifest["npm_path"] = str(npm_path)
        print(f"  DevRoot       : {devroot}")
        print(f"  NodePath      : {node_path}")
        print(f"  NpmPath       : {npm_path}")
        print(f"  [{_ts()}] [OK] 路径推导完成")
    except Exception as e:
        manifest["errors"].append(f"路径推导失败: {e}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"\n[FAIL] {e}")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 2. 验证 node.exe 身份
    # -------------------------------------------------------------------------
    _print_step_header(1, "验证工具链身份 — node.exe")
    ok, step = _verify_node_identity(node_path, show_progress)
    steps.append(step)
    print(f"  命令: {step['cmd']}")
    if step.get("detail"):
        print(f"  {step['detail']}")
    _print_step_footer(step)
    if not ok:
        manifest["errors"].append(step.get("error", "node.exe 身份验证失败"))
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 3. 验证 npm 可用性
    # -------------------------------------------------------------------------
    _print_step_header(2, "验证工具链身份 — npm")
    ok, step = _verify_npm_available(npm_path, show_progress)
    steps.append(step)
    print(f"  命令: {step['cmd']}")
    if step.get("detail"):
        print(f"  {step['detail']}")
    _print_step_footer(step)
    if not ok:
        manifest["errors"].append(step.get("error", "npm 不可用"))
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 4. 创建目标目录
    # -------------------------------------------------------------------------
    _print_step_header(3, "准备目标目录")
    t0 = time.perf_counter()
    if not target_dir.exists():
        print(f"  命令: Path.mkdir(parents=True, exist_ok=True)  =>  {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] 目录已创建: {target_dir}")
    else:
        print(f"  命令: Path.mkdir(parents=True, exist_ok=True)  =>  {target_dir}")
        print(f"  [SKIP] 目录已存在，无需创建")
    elapsed = time.perf_counter() - t0
    step = {"label": "准备目标目录", "status": "OK", "elapsed_sec": round(elapsed, 2), "detail": f"目标目录就绪: {target_dir}"}
    steps.append(step)
    _print_step_footer(step)

    # -------------------------------------------------------------------------
    # 5. 模式分支：Local vs Global
    # -------------------------------------------------------------------------
    if mode == "local":
        # ---------------------------------------------------------------------
        # 5a. Local 模式：重组安全检查 → cd → npm init → npm install
        # ---------------------------------------------------------------------
        _print_step_header(4, "Local 模式 — 重组安全检查")
        t0 = time.perf_counter()
        safe, reason, details = _check_reorg_risk(target_dir)
        elapsed = time.perf_counter() - t0
        step = {"label": "重组安全检查", "status": "OK" if safe else "BLOCKED", "elapsed_sec": round(elapsed, 2), "detail": reason, "check_items": details}
        steps.append(step)
        print(f"  [安全检查] 扫描目标目录状态...")
        print(f"    - node_modules  存在? : {details['node_modules_exists']} {'(风险项)' if details['node_modules_exists'] and not details['package_json_exists'] else ''}")
        print(f"    - package.json  存在? : {details['package_json_exists']} {'(保护项)' if details['package_json_exists'] else '(缺失)' if details['node_modules_exists'] else ''}")
        print(f"    - 重组风险判定      : {'❌ 高风险 — 将阻止执行' if details['risk_detected'] else '✅ 无风险 — 继续执行'}")
        if not safe:
            print(f"  [BLOCKED] {reason}")
        _print_step_footer(step)
        if not safe:
            manifest["errors"].append(reason)
            manifest["exit_code"] = 50
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"\n[BLOCKED] {reason}")
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(50)

        # cd
        _print_step_header(5, "Local 模式 — 切换工作目录")
        original_cwd = Path.cwd()
        print(f"  [安全检查] 记录原始 CWD: {original_cwd}")
        os.chdir(str(target_dir))
        ok, step = _verify_cwd_switched(target_dir)
        steps.append(step)
        print(f"  命令: os.chdir({target_dir})")
        print(f"  [安全检查] CWD 切换验证...")
        ci = step.get("check_items", {})
        print(f"    - 预期 CWD: {ci.get('expected_cwd')}")
        print(f"    - 实际 CWD: {ci.get('actual_cwd')}")
        print(f"    - 匹配结果: {'✅ 一致' if ci.get('matched') else '❌ 不一致'}")
        if step.get("detail"):
            print(f"  {step['detail']}")
        _print_step_footer(step)
        if not ok:
            manifest["errors"].append(step.get("error", "CWD 切换失败"))
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            os.chdir(str(original_cwd))
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)

        # npm init -y
        _print_step_header(6, "Local 模式 — npm init -y")
        exit_code, stderr, step = _run_npm_cmd(
            npm_path, ["init", "-y"], str(target_dir), show_progress,
            label="npm init -y", timeout=30,
        )
        steps.append(step)
        print(f"  命令: {step['cmd']}")
        _print_step_footer(step, _collect_artifacts(target_dir, pkg_name, mode) if exit_code == 0 else None)
        if exit_code != 0:
            manifest["errors"].append(f"npm init -y 失败 (exit {exit_code}): {stderr or '未知错误'}")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            os.chdir(str(original_cwd))
            print(f"\n[FAIL] npm init -y 失败: {stderr}")
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)

        # npm install
        _print_step_header(7, f"Local 模式 — npm install {full_pkg}")
        exit_code, stderr, step = _run_npm_cmd(
            npm_path, ["install", full_pkg], str(target_dir), show_progress,
            label=f"npm install {full_pkg}", timeout=300,
        )
        steps.append(step)
        print(f"  命令: {step['cmd']}")
        _print_step_footer(step, _collect_artifacts(target_dir, pkg_name, mode) if exit_code == 0 else None)
        if exit_code != 0:
            manifest["errors"].append(f"npm install 失败 (exit {exit_code}): {stderr or '未知错误'}")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            os.chdir(str(original_cwd))
            print(f"\n[FAIL] npm install 失败: {stderr}")
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)

        # 恢复 CWD
        print(f"\n[安全检查] 恢复原始 CWD: {original_cwd}")
        os.chdir(str(original_cwd))
        print(f"  [OK] CWD 已恢复: {Path.cwd()}")

    else:
        # ---------------------------------------------------------------------
        # 5b. Global 模式：直接 npm --prefix -g install
        # ---------------------------------------------------------------------
        _print_step_header(4, f"Global 模式 — npm install {full_pkg}")
        exit_code, stderr, step = _run_npm_cmd(
            npm_path, ["--prefix", str(target_dir), "-g", "install", full_pkg],
            None, show_progress,
            label=f"npm --prefix {target_dir} -g install {full_pkg}", timeout=300,
        )
        steps.append(step)
        print(f"  命令: {step['cmd']}")
        _print_step_footer(step, _collect_artifacts(target_dir, pkg_name, mode) if exit_code == 0 else None)
        if exit_code != 0:
            manifest["errors"].append(f"npm install 失败 (exit {exit_code}): {stderr or '未知错误'}")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"\n[FAIL] npm install 失败: {stderr}")
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)

    # -------------------------------------------------------------------------
    # 6. 安装后验证
    # -------------------------------------------------------------------------
    _print_step_header(8 if mode == "local" else 5, "验证安装结果")
    t0 = time.perf_counter()
    verification = _verify_installation(target_dir, pkg_name, bin_name, mode)
    elapsed = time.perf_counter() - t0
    step = {"label": "安装后验证", "status": "OK", "elapsed_sec": round(elapsed, 2)}
    steps.append(step)

    print(f"  包目录存在    : {'[OK]' if verification['pkg_dir_exists'] else '[FAIL]'}")
    print(f"  包元数据完整  : {'[OK]' if verification['pkg_meta_exists'] else '[FAIL]'}")
    print(f"  包入口存在    : {'[OK]' if verification['pkg_entry_exists'] else '[WARN]'}  ({verification.get('pkg_entry_path', 'N/A')})")
    if bin_name:
        print(f"  bin 入口      : {'[OK]' if verification['bin_exists'] else '[WARN]'}  ({verification.get('bin_detail', '')})")
        if verification.get("bin_paths"):
            for bp in verification["bin_paths"]:
                print(f"    - {bp}")
    if verification.get("pkg_version"):
        print(f"  安装版本      : {verification['pkg_version']}")

    manifest["verification"] = verification
    _print_step_footer(step)

    # -------------------------------------------------------------------------
    # 6b. bin 可用性验证（新增）
    # -------------------------------------------------------------------------
    bin_usable_tests = []
    if verification.get("bin_paths"):
        _print_step_header(9 if mode == "local" else 6, "验证 bin 可执行性")
        for bp in verification["bin_paths"]:
            test_result = _test_bin_executable(bp)
            bin_usable_tests.append(test_result)
            status_emoji = "✅" if test_result["usable"] else "⚠️"
            print(f"  {status_emoji} 测试: {test_result['tested_cmd']}")
            print(f"     退出码: {test_result['exit_code']} | 耗时: {test_result['elapsed_sec']:.2f}s | 状态: [{test_result['status']}]")
            if test_result.get("stdout_preview"):
                print(f"     stdout: {test_result['stdout_preview']}")
            if test_result.get("stderr_preview"):
                print(f"     stderr: {test_result['stderr_preview']}")
        manifest["bin_usable_tests"] = bin_usable_tests
        # 若所有 bin 均不可用，标记为 WARN
        all_unusable = all(not t["usable"] for t in bin_usable_tests)
        if all_unusable:
            print(f"  [WARN] 所有 bin 入口执行测试均失败（--version / --help 均不可用）")
    else:
        manifest["bin_usable_tests"] = []

    has_fail = not verification["pkg_dir_exists"] or not verification["pkg_meta_exists"]
    has_warn = (bin_name and not verification["bin_exists"]) or (
        bin_name and verification["bin_exists"] and bin_usable_tests and all(not t["usable"] for t in bin_usable_tests)
    )

    # -------------------------------------------------------------------------
    # 7. 最终状态
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    if has_fail:
        overall = "[FAIL]"
        exit_code = 1
    elif has_warn:
        overall = "[WARN]"
        exit_code = 0
    else:
        overall = "[SUCCESS]"
        exit_code = 0

    manifest["exit_code"] = exit_code
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest, args.output)

    print(f"Status        : {overall}")
    print(f"Package       : {full_pkg}")
    print(f"TargetDir     : {target_dir}")
    print(f"Mode          : {mode}")
    print(f"NodePath      : {node_path}")
    print(f"Manifest      : {mp}")

    if overall == "[FAIL]":
        print("\n排查建议:")
        print("  1. 检查包名拼写是否正确（npm view <pkg>）")
        print("  2. 检查网络连接和 npm registry 可达性")
        print("  3. 尝试切换 Mode（local <-> global）后重试")
        print("  4. 检查目标目录是否有权限问题")
        sys.exit(1)
    elif overall == "[WARN]":
        print("\n[WARN] 安装完成，但部分验证项未通过。")
        sys.exit(0)
    else:
        print("\n[SUCCESS] 安装完成且验证通过。")
        sys.exit(0)


if __name__ == "__main__":
    main()
