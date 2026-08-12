#!/usr/bin/env python3
r"""
atomic-npm-update.py — npm 隔离更新原子 CLI
标签：py-tools
版本：v1.0.0

【设计意图】
  在已有 Local 安装结构的隔离目录中，安全更新指定 npm 包（或全部包）。
  与 atomic-npm-isolated-install.py 成对使用：install 负责首次落盘，update 负责后续升级。

  核心场景：OpenCode CLI 升级后，同步更新 venv/.opencode/ 下的 @opencode-ai/plugin SDK。

  核心谨慎原则：
    1. 目标目录必须已有 package.json，否则拒绝执行（update 只能在 Local 结构上操作）。
    2. 若指定 --package，读取 package.json 确认该依赖存在；若不存在则提示并退出。
    3. 若指定 --to-version，使用 npm install <pkg>@<version> 精确锁定版本；
       否则使用 npm update <pkg>，让 npm 按 semver 范围解析最新版。
    4. 更新前记录旧版本号，更新后对比，输出升级摘要（旧版 → 新版）。
    5. 安装前验证 node.exe 身份（process.execPath 必须等于传入路径）。
    6. 更新后验证 node_modules/<pkg>/package.json 存在性，并提取新版本号。
    7. show-progress 模式下 npm 输出直通终端；静默模式下捕获 stdout/stderr。
    8. 所有 stdout 输出强制 flush，确保脚本框架输出与 npm 子进程输出的时序正确。

【职责】
  - 单包更新：cd target-dir → npm update <pkg>（或 npm install <pkg>@<version>）
  - 全量更新：cd target-dir → npm update
  - 产物：更新后的 package.json + package-lock.json + node_modules/

【依赖】
  底层能力：无（纯 Python 标准库 + subprocess，零外部依赖）
  外部工具：node.exe、npm.cmd（路径推导或显式传入）

【预检】
  - --target-dir 必须提供且为绝对路径
  - 目标目录必须存在且包含 package.json
  - node.exe 必须可执行且 process.execPath 匹配
  - npm.cmd 必须与 node.exe 同级

【调用参数】
  --target-dir      <str, 必填>  目标隔离目录绝对路径（必须已有 package.json）
  --package         <str, 可选>  npm 包名（如 @opencode-ai/plugin）。不指定时更新全部
  --to-version      <str, 可选>  目标版本号，如 "1.18.14" 或 "latest"。提供时走 npm install
  --node-path       <str, 可选>  node.exe 绝对路径（默认从 devroot 推导）
  --devroot         <str, 可选>  devroot 路径（默认从脚本位置向上推导）
  --show-progress   <flag, 可选> 显示 npm 实时进度输出（默认静默，捕获 stdout/stderr）
  --output          <str, 可选>  manifest 输出路径（未传时自动生成到 venv/tmp/）

【用法示例】
  # 更新 @opencode-ai/plugin 到 latest（精确锁定）
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-npm-update.py" `
      --target-dir "${devroot}\venv\.opencode" `
      --package "@opencode-ai/plugin" `
      --to-version "latest"

  # 按 semver 范围更新 @opencode-ai/plugin
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-npm-update.py" `
      --target-dir "${devroot}\venv\.opencode" `
      --package "@opencode-ai/plugin"

  # 全量更新（不指定 --package）
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-npm-update.py" `
      --target-dir "${devroot}\venv\.opencode"

【返回码】
  0 — 更新成功且版本号有变化（或版本号未变但无错误）
  1 — 前置检查失败 / node 身份验证失败 / npm 更新失败 / 验证失败
  50 — 目标目录缺少 package.json（update 只能在 Local 结构上操作）
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
# 工具函数（与 atomic-npm-isolated-install.py 保持一致）
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
# 路径推导（与 install 版保持一致）
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
# 验证（与 install 版保持一致）
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
# npm 命令统一执行器（与 install 版保持一致）
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

    show_progress=True  : stdout/stderr 直通终端
    show_progress=False : stdout/stderr 被捕获

    返回 (exit_code, stderr_or_None, step_record)
    """
    cmd = [str(npm_path)] + args
    cmd_str = _fmt_cmd(cmd, cwd)
    step = {"label": label, "cmd": cmd_str}
    t0 = time.perf_counter()

    if show_progress:
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
# 版本号读取
# =============================================================================
def _read_pkg_version(target_dir: Path, pkg_name: str) -> str | None:
    """读取 node_modules/<pkg>/package.json 中的 version 字段。"""
    pkg_json = target_dir / "node_modules" / pkg_name / "package.json"
    if not pkg_json.exists():
        return None
    try:
        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        return data.get("version")
    except Exception:
        return None


def _read_dep_version_from_lock(target_dir: Path, pkg_name: str) -> str | None:
    """
    从 package-lock.json 读取指定包的已锁定版本号。
    作为更新前的"旧版本"真源（比 package.json 中的 semver 范围更精确）。
    """
    lock_file = target_dir / "package-lock.json"
    if not lock_file.exists():
        return None
    try:
        data = json.loads(lock_file.read_text(encoding="utf-8"))
        # lockfileVersion 2/3 结构
        packages = data.get("packages", {})
        # 先尝试根依赖
        root_deps = data.get("dependencies", {})
        if pkg_name in root_deps:
            return root_deps[pkg_name].get("version")
        # 再尝试 packages 字段（lockfileVersion 2/3）
        for key, info in packages.items():
            if key.endswith(f"/{pkg_name}") or key == pkg_name:
                return info.get("version")
        return None
    except Exception:
        return None


def _read_dep_version_from_pkg_json(target_dir: Path, pkg_name: str) -> str | None:
    """从 package.json 的 dependencies/devDependencies 读取声明版本。"""
    pkg_json = target_dir / "package.json"
    if not pkg_json.exists():
        return None
    try:
        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        for section in ("dependencies", "devDependencies"):
            if section in data and pkg_name in data[section]:
                return data[section][pkg_name]
        return None
    except Exception:
        return None


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
        manifest_path = manifest_dir / f"npm-update-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 步骤输出格式化（与 install 版保持一致）
# =============================================================================
def _print_step_header(step_num: int | None, description: str):
    print("")
    if step_num is not None:
        print(f"[{_ts()}] [Step {step_num}] {description}")
    else:
        print(f"[{_ts()}] {description}")


def _print_step_footer(step: dict):
    """打印步骤 footer：退出码、耗时。"""
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


# =============================================================================
# 主逻辑
# =============================================================================
def main():
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
    parser = argparse.ArgumentParser(description="npm 隔离更新原子工具")
    parser.add_argument("--target-dir", required=True, help="目标隔离目录绝对路径（必须已有 package.json）")
    parser.add_argument("--package", default=None, help="npm 包名（如 @opencode-ai/plugin）。不指定时更新全部")
    parser.add_argument("--to-version", default=None, help='目标版本号，如 "1.18.14" 或 "latest"。提供时走 npm install')
    parser.add_argument("--node-path", default=None, help="node.exe 绝对路径（默认推导）")
    parser.add_argument("--devroot", default=None, help="devroot 路径（默认推导）")
    parser.add_argument("--show-progress", action="store_true", help="显示 npm 实时进度输出")
    parser.add_argument("--output", default=None, help="manifest 输出路径（未传时自动生成）")
    args = parser.parse_args()

    target_dir = Path(args.target_dir).resolve()
    pkg_name = args.package
    to_version = args.to_version
    show_progress = args.show_progress
    steps: list[dict] = []

    manifest = {
        "atomic_tool": "atomic-npm-update",
        "version": "1.0.0",
        "target_dir": str(target_dir),
        "package": pkg_name,
        "to_version": to_version,
        "show_progress": show_progress,
        "node_path": None,
        "npm_path": None,
        "old_version": None,
        "new_version": None,
        "version_changed": False,
        "steps": steps,
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    print("=" * 60)
    print("[npm Update] 原子更新工具 v1.0.0")
    print("=" * 60)
    print(f"  TargetDir     : {target_dir}")
    print(f"  Package       : {pkg_name or '(全部)'}")
    print(f"  ToVersion     : {to_version or '(按 semver 解析)'}")
    print(f"  ShowProgress  : {show_progress}")

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
    # 4. 目标目录安全检查：必须存在且包含 package.json
    # -------------------------------------------------------------------------
    _print_step_header(3, "目标目录结构检查")
    t0 = time.perf_counter()
    if not target_dir.exists():
        manifest["errors"].append(f"目标目录不存在: {target_dir}")
        manifest["exit_code"] = 50
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"  [FAIL] 目标目录不存在: {target_dir}")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(50)

    pkg_json_path = target_dir / "package.json"
    if not pkg_json_path.exists():
        manifest["errors"].append(
            f"目标目录缺少 package.json: {target_dir}\n"
            "update 只能在已有 Local 安装结构的目录上操作。"
            "若需首次安装，请使用 atomic-npm-isolated-install.py。"
        )
        manifest["exit_code"] = 50
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"  [FAIL] 目标目录缺少 package.json")
        print(f"    提示: update 只能在已有 Local 安装结构的目录上操作。")
        print(f"    若需首次安装，请使用 atomic-npm-isolated-install.py。")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(50)

    print(f"  [OK] 目标目录存在: {target_dir}")
    print(f"  [OK] package.json 存在: {pkg_json_path}")

    # 若指定了包名，确认该依赖存在于 package.json 中
    if pkg_name:
        declared_ver = _read_dep_version_from_pkg_json(target_dir, pkg_name)
        if declared_ver is None:
            manifest["errors"].append(
                f"package.json 中未找到依赖 '{pkg_name}'。"
                "请确认包名拼写，或使用 atomic-npm-isolated-install.py 首次安装。"
            )
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"  [FAIL] package.json 中未找到依赖 '{pkg_name}'")
            print(f"    提示: 请确认包名拼写，或使用 atomic-npm-isolated-install.py 首次安装。")
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
        print(f"  [OK] package.json 中声明版本: {pkg_name}@{declared_ver}")
    elapsed = time.perf_counter() - t0
    step = {"label": "目标目录结构检查", "status": "OK", "elapsed_sec": round(elapsed, 2)}
    steps.append(step)
    _print_step_footer(step)

    # -------------------------------------------------------------------------
    # 5. 记录更新前版本号
    # -------------------------------------------------------------------------
    _print_step_header(4, "记录更新前版本号")
    old_version = None
    if pkg_name:
        # 优先从 lock 读取精确版本，fallback 到 package.json 声明版本
        old_version = _read_dep_version_from_lock(target_dir, pkg_name)
        if old_version:
            print(f"  [OK] 从 package-lock.json 读取旧版本: {pkg_name}@{old_version}")
        else:
            old_version = _read_dep_version_from_pkg_json(target_dir, pkg_name)
            if old_version:
                print(f"  [OK] 从 package.json 读取声明版本: {pkg_name}@{old_version}")
            else:
                print(f"  [WARN] 无法读取旧版本号（包可能尚未安装到 node_modules）")
    else:
        print(f"  [SKIP] 全量更新模式，不读取单包旧版本号")
    manifest["old_version"] = old_version
    step = {"label": "记录更新前版本号", "status": "OK", "detail": f"旧版本: {old_version or 'N/A'}"}
    steps.append(step)
    _print_step_footer(step)

    # -------------------------------------------------------------------------
    # 6. 切换工作目录
    # -------------------------------------------------------------------------
    _print_step_header(5, "切换工作目录")
    original_cwd = Path.cwd()
    print(f"  [安全检查] 记录原始 CWD: {original_cwd}")
    os.chdir(str(target_dir))
    actual_cwd = Path.cwd().resolve()
    expected_cwd = target_dir.resolve()
    if actual_cwd == expected_cwd:
        print(f"  [OK] CWD 已切换: {actual_cwd}")
        step = {"label": "切换工作目录", "status": "OK", "detail": f"CWD: {actual_cwd}"}
    else:
        os.chdir(str(original_cwd))
        manifest["errors"].append(f"CWD 切换失败: 预期 {expected_cwd}, 实际 {actual_cwd}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"  [FAIL] CWD 切换失败: 预期 {expected_cwd}, 实际 {actual_cwd}")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)
    steps.append(step)
    _print_step_footer(step)

    # -------------------------------------------------------------------------
    # 7. 执行更新
    # -------------------------------------------------------------------------
    if pkg_name and to_version:
        # 精确版本：npm install <pkg>@<version>
        _print_step_header(6, f"npm install {pkg_name}@{to_version}")
        exit_code, stderr, step = _run_npm_cmd(
            npm_path, ["install", f"{pkg_name}@{to_version}"],
            str(target_dir), show_progress,
            label=f"npm install {pkg_name}@{to_version}", timeout=300,
        )
    elif pkg_name:
        # 单包 semver 更新：npm update <pkg>
        _print_step_header(6, f"npm update {pkg_name}")
        exit_code, stderr, step = _run_npm_cmd(
            npm_path, ["update", pkg_name],
            str(target_dir), show_progress,
            label=f"npm update {pkg_name}", timeout=300,
        )
    else:
        # 全量更新：npm update
        _print_step_header(6, "npm update")
        exit_code, stderr, step = _run_npm_cmd(
            npm_path, ["update"],
            str(target_dir), show_progress,
            label="npm update", timeout=300,
        )
    steps.append(step)
    print(f"  命令: {step['cmd']}")
    _print_step_footer(step)

    if exit_code != 0:
        manifest["errors"].append(f"npm 更新失败 (exit {exit_code}): {stderr or '未知错误'}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        os.chdir(str(original_cwd))
        print(f"\n[FAIL] npm 更新失败: {stderr}")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 8. 记录更新后版本号
    # -------------------------------------------------------------------------
    _print_step_header(7, "记录更新后版本号")
    new_version = None
    if pkg_name:
        new_version = _read_pkg_version(target_dir, pkg_name)
        if new_version:
            print(f"  [OK] 从 node_modules 读取新版本: {pkg_name}@{new_version}")
        else:
            print(f"  [WARN] 无法从 node_modules 读取新版本号")
    else:
        print(f"  [SKIP] 全量更新模式，不读取单包新版本号")
    manifest["new_version"] = new_version
    manifest["version_changed"] = (old_version is not None and new_version is not None and old_version != new_version)
    step = {
        "label": "记录更新后版本号",
        "status": "OK",
        "detail": f"{old_version or 'N/A'} → {new_version or 'N/A'}",
    }
    steps.append(step)
    _print_step_footer(step)

    # -------------------------------------------------------------------------
    # 9. 恢复 CWD
    # -------------------------------------------------------------------------
    print(f"\n[安全检查] 恢复原始 CWD: {original_cwd}")
    os.chdir(str(original_cwd))
    print(f"  [OK] CWD 已恢复: {Path.cwd()}")

    # -------------------------------------------------------------------------
    # 10. 最终状态
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest, args.output)

    if pkg_name and old_version and new_version:
        if old_version == new_version:
            print(f"Status        : [SUCCESS] 版本未变化")
            print(f"Version       : {old_version} → {new_version} (无变化)")
        else:
            print(f"Status        : [SUCCESS] 版本已更新")
            print(f"Version       : {old_version} → {new_version}")
    elif pkg_name:
        print(f"Status        : [SUCCESS]")
        print(f"Version       : {old_version or 'N/A'} → {new_version or 'N/A'}")
    else:
        print(f"Status        : [SUCCESS] 全量更新完成")

    print(f"TargetDir     : {target_dir}")
    print(f"Package       : {pkg_name or '(全部)'}")
    print(f"NodePath      : {node_path}")
    print(f"Manifest      : {mp}")
    print("\n[SUCCESS] 更新完成。")
    sys.exit(0)


if __name__ == "__main__":
    main()
