#!/usr/bin/env python3
"""
插件：核心工具（Core）
标签：core

职责：提供通用工具函数——步骤头输出、日志格式化、异常包装等。

用法：
    from plugins.core import step_header, log_info, log_error
    
    step_header("Step 1", "初始化")
    log_info("开始执行...")
"""
import sys
import time
from datetime import datetime


def step_header(step_id: str, title: str):
    """输出步骤分隔线（对称于 PS 的 Write-StepHeader）"""
    print(f"\n{'=' * 50}")
    print(f"Step {step_id}: {title}")
    print(f"{'=' * 50}")


def log_info(msg: str):
    """信息日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [INFO] {msg}")


def log_error(msg: str):
    """错误日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [ERROR] {msg}", file=sys.stderr)


def log_warning(msg: str):
    """警告日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [WARN] {msg}")


def timer(func):
    """装饰器：计算函数执行时间"""
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.time() - start
            log_info(f"{func.__name__} 耗时: {elapsed:.2f}s")
    return wrapper


class StepContext:
    """
    步骤执行上下文（对称于 Ralph Loop 的 Audit Trail）。
    
    用法：
        with StepContext("1", "初始化") as ctx:
            # 执行步骤...
            ctx.set_status("completed")
    """

    def __init__(self, step_id: str, title: str):
        self.step_id = step_id
        self.title = title
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.artifacts = []

    def __enter__(self):
        self.start_time = time.time()
        self.status = "running"
        step_header(self.step_id, self.title)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if exc_type is None:
            self.status = "completed"
        else:
            self.status = "failed"
            log_error(f"Step {self.step_id} 失败: {exc_val}")
        elapsed = (self.end_time or time.time()) - self.start_time
        log_info(f"Step {self.step_id} 状态: {self.status}, 耗时: {elapsed:.2f}s")
        return False  # 不吞异常

    def add_artifact(self, name: str, path: str):
        """记录输出产物"""
        self.artifacts.append({"name": name, "path": path})

    def set_status(self, status: str):
        """手动设置状态"""
        self.status = status
