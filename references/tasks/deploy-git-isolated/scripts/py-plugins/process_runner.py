#!/usr/bin/env python3
"""
插件：Process Runner（进程执行器）v3
标签：core
依赖：encoding

职责：封装 subprocess 流式执行能力，提供两种模式：
  1. run_streaming: stdout=None 直接透传（适合短输出）
  2. run_streaming_limited: 逐行读取，最多显示前 N 行（适合长输出防折叠）

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["core"])
    registry.process_runner.run_streaming_limited(["git", "status"], label="git status")

用法（直接 import）：
    from process_runner import run_streaming_limited
    for line in run_streaming_limited(["git", "status"], max_lines=10):
        print(line, end="")
"""
import atexit
import subprocess
import sys
import time
from typing import List, Optional

# =============================================================================
# 编码设置闭环：保存原始值 → 切换 UTF-8 → 注册退出恢复
# =============================================================================
_ORIGINAL_STDOUT_ENCODING = sys.stdout.encoding
_ORIGINAL_STDERR_ENCODING = sys.stderr.encoding


def _restore_encoding():
    """恢复 stdout/stderr 到原始编码。供 atexit 注册，也可显式调用。"""
    try:
        if sys.stdout.encoding != _ORIGINAL_STDOUT_ENCODING:
            sys.stdout.reconfigure(encoding=_ORIGINAL_STDOUT_ENCODING)
    except Exception:
        pass
    try:
        if sys.stderr.encoding != _ORIGINAL_STDERR_ENCODING:
            sys.stderr.reconfigure(encoding=_ORIGINAL_STDERR_ENCODING)
    except Exception:
        pass


atexit.register(_restore_encoding)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def run_streaming(
    cmd: List[str],
    label: str = "",
    cwd: Optional[str] = None,
    timeout: int = 300,
) -> None:
    """
    流式执行命令，stdout=None + stderr=STDOUT 直接透传。
    
    关键点：子进程直接写到父进程 stdout，bufsize=1 行缓冲确保实时可见，
    不经过 Python 层的 for line in stdout 循环。
    
    参数:
        cmd: 命令列表，如 ["git", "-C", "/path", "status"]
        label: 标签，用于日志标识
        cwd: 工作目录
        timeout: 超时秒数，默认 300
    
    异常:
        subprocess.TimeoutExpired: 超时
        subprocess.CalledProcessError: 进程返回非 0
    """
    start = time.time()
    
    if label:
        print(f"[ProcessRunner] 启动: {label}")
    print(f"[ProcessRunner] 命令: {' '.join(cmd)}")
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=None,  # 透传：子进程直接写到父进程 stdout
            stderr=subprocess.STDOUT,  # stderr 合并到 stdout
            bufsize=1,  # 行缓冲
            cwd=cwd,
        )
        
        proc.wait(timeout=timeout)
        elapsed = time.time() - start
        
        if proc.returncode != 0:
            print(f"[ProcessRunner] [FAIL] {label} 退出码 {proc.returncode} (耗时 {elapsed:.2f}s)")
            raise subprocess.CalledProcessError(proc.returncode, cmd)
        
        print(f"[ProcessRunner] [OK] {label} 完成 (耗时 {elapsed:.2f}s)")
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"[ProcessRunner] [FAIL] {label} 超时 ({timeout}s)")
        raise
    except Exception as e:
        elapsed = time.time() - start
        print(f"[ProcessRunner] [FAIL] {label} 异常: {e} (耗时 {elapsed:.2f}s)")
        raise


def run_streaming_limited(
    cmd: List[str],
    label: str = "",
    cwd: Optional[str] = None,
        max_lines: int = 8,
    timeout: int = 300,
):
    """
    流式执行命令，逐行读取 stdout，最多显示前 max_lines 行。
    
    关键点：
    - stdout=PIPE，逐行读取（不用 communicate，避免缓存全部输出）
    - 超过 max_lines 后继续读取但不显示，防止 PIPE 满导致死锁
    - 进程退出后立即检查返回码，异常即时响应
    - 适用于长输出命令（如 git status），避免触发 Cursor 折叠
    
    参数:
        cmd: 命令列表
        label: 标签
        cwd: 工作目录
        max_lines: 最多显示的行数，默认 10
        timeout: 超时秒数
    
    返回:
        Iterator[str]: 逐行输出（最多 max_lines 行）
    
    异常:
        subprocess.TimeoutExpired: 超时
        subprocess.CalledProcessError: 进程返回非 0
    """
    start = time.time()
    
    if label:
        yield f"[ProcessRunner] 启动: {label}\n"
    yield f"[ProcessRunner] 命令: {' '.join(cmd)}\n"
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=cwd,
        )
        
        line_count = 0
        for line in proc.stdout:
            line_count += 1
            if line_count <= max_lines:
                yield line
            # 超过 max_lines 后继续读取但不 yield，防止 PIPE 满
        
        proc.wait(timeout=timeout)
        elapsed = time.time() - start
        
        if line_count > max_lines:
            yield f"[ProcessRunner] ... （还有 {line_count - max_lines} 行未显示）\n"
        
        if proc.returncode != 0:
            yield f"[ProcessRunner] [FAIL] {label} 退出码 {proc.returncode} (耗时 {elapsed:.2f}s)\n"
            raise subprocess.CalledProcessError(proc.returncode, cmd)
        
        yield f"[ProcessRunner] [OK] {label} 完成 (耗时 {elapsed:.2f}s)\n"
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        yield f"[ProcessRunner] [FAIL] {label} 超时 ({timeout}s)\n"
        raise
    except Exception as e:
        elapsed = time.time() - start
        yield f"[ProcessRunner] [FAIL] {label} 异常: {e} (耗时 {elapsed:.2f}s)\n"
        raise


def run_simple(
    cmd: List[str],
    label: str = "",
    cwd: Optional[str] = None,
    timeout: int = 300,
    encoding: str = "utf-8",
) -> subprocess.CompletedProcess:
    """
    简单执行命令，返回 CompletedProcess（非流式，用于不需要实时输出的场景）。
    """
    if label:
        print(f"[ProcessRunner] 启动: {label}", file=sys.stderr)
    
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding=encoding,
        errors="replace",
        cwd=cwd,
        timeout=timeout,
    )
