#!/usr/bin/env python3
"""
插件：Devroot 探测与真源验证（Devroot Probe & Validation）
标签：core

职责：在 monorepo 多端多源结构中，探测并验证 devroot（开发根目录），
      作为所有路径计算的基准。支持显式指定、环境变量、自动探测三种来源。

探测策略（按优先级）：
1. 显式传入参数（最高优先级）
2. 环境变量 DEVROOT
3. 自动探测：
   - 首要特征：references/tasks/ 目录结构（task 必然位于 devroot/references/tasks/ 下）
   - Fallback：通用标记目录（如 .vscode/.cursor/apps/docs 等）

真源验证：
- 路径必须存在且为目录
- 路径下必须包含 references/tasks/ 结构，或至少一个 fallback 标记

用法：
    from detect_devroot import get_devroot, validate_devroot
    
    devroot = get_devroot()  # 自动探测并验证
    validate_devroot(devroot)  # 显式验证
"""
import os
from pathlib import Path

# Fallback 标记目录：用于非标准路径结构的兜底探测
# 注意：.git 和 venv 不列入，因为服务器部署时可能不存在
_FALLBACK_MARKERS = [".vscode", ".cursor", "apps", "docs", "out"]

# 最大回溯深度
_MAX_PROBE_DEPTH = 5

# 缓存：避免重复探测
_CACHED_DEVROOT = None


def validate_devroot(devroot_path: str) -> Path:
    """
    验证指定路径是否为有效的 devroot。

    验证逻辑：
    1. 路径必须存在且为目录
    2. 路径下包含 references/tasks/ 结构（task 的首要特征）
    3. 或路径下包含至少一个 fallback 标记

    参数:
        devroot_path: 待验证的路径字符串或 Path 对象

    返回:
        Path: 验证通过的绝对路径

    异常:
        ValueError: 路径无效、不是目录、或不包含预期结构/标记
    """
    path = Path(devroot_path).resolve()

    if not path.exists():
        raise ValueError(f"devroot 路径不存在: {path}")

    if not path.is_dir():
        raise ValueError(f"devroot 路径不是目录: {path}")

    # 首要特征：references/tasks/ 目录结构
    # 本 task 必然位于 devroot/references/tasks/ 下
    if (path / "references" / "tasks").exists():
        return path

    # Fallback：检查是否包含其他标记
    markers_found = [m for m in _FALLBACK_MARKERS if (path / m).exists()]
    if markers_found:
        return path

    raise ValueError(
        f"devroot 路径未包含预期结构或标记。"
        f"路径: {path}; "
        f"首要特征缺失: references/tasks/; "
        f"fallback 标记: {_FALLBACK_MARKERS}"
    )


def _probe_by_task_structure(start_path: Path) -> Path:
    """
    通过 references/tasks/ 目录结构探测 devroot。

    逻辑：从起始路径向上回溯，寻找当前目录的父目录是 tasks/ 且祖父目录是 references/ 的节点。
    若找到，devroot 为 references/ 的父目录。

    参数:
        start_path: 起始路径（通常为 __file__ 所在目录）

    返回:
        Path: 探测到的 devroot 绝对路径

    异常:
        RuntimeError: 未找到符合结构的 devroot
    """
    current = start_path if start_path.is_dir() else start_path.parent

    for _ in range(_MAX_PROBE_DEPTH):
        parent = current.parent
        grandparent = parent.parent if parent != current else None

        # 检查是否命中 references/tasks/ 结构
        # current 在 references/tasks/ 的某级子目录下
        if (parent.name == "tasks" and
            grandparent is not None and
            grandparent.name == "references"):
            # devroot 是 references/ 的父目录
            devroot = grandparent.parent
            return validate_devroot(devroot)

        if parent == current:
            # 已到盘符根
            break
        current = parent

    raise RuntimeError(
        f"未通过 references/tasks/ 结构找到 devroot。"
        f"起始路径: {start_path}"
    )


def _probe_by_fallback_markers(start_path: Path) -> Path:
    """
    通过 fallback 标记目录探测 devroot。

    参数:
        start_path: 起始路径

    返回:
        Path: 探测到的 devroot 绝对路径

    异常:
        RuntimeError: 未找到符合条件的 devroot
    """
    current = start_path if start_path.is_dir() else start_path.parent

    for _ in range(_MAX_PROBE_DEPTH):
        if any((current / m).exists() for m in _FALLBACK_MARKERS):
            return validate_devroot(current)

        parent = current.parent
        if parent == current:
            break
        current = parent

    raise RuntimeError(
        f"未通过 fallback 标记找到 devroot。"
        f"起始路径: {start_path}, "
        f"回溯深度: {_MAX_PROBE_DEPTH}, "
        f"查找标记: {_FALLBACK_MARKERS}"
    )


def probe_devroot(start_path: str = None) -> Path:
    """
    探测 devroot。

    策略：
    1. 优先通过 references/tasks/ 目录结构探测
    2. 失败时 fallback 到标记目录探测

    参数:
        start_path: 起始路径（默认：当前文件所在目录）

    返回:
        Path: 探测到的 devroot 绝对路径

    异常:
        RuntimeError: 所有探测策略均失败
    """
    start = Path(start_path or __file__).resolve()

    # 策略 1：references/tasks/ 结构（首要特征）
    try:
        return _probe_by_task_structure(start)
    except RuntimeError:
        pass

    # 策略 2：fallback 标记
    try:
        return _probe_by_fallback_markers(start)
    except RuntimeError:
        pass

    raise RuntimeError(
        f"所有探测策略均失败。"
        f"起始路径: {start}; "
        f"策略 1: references/tasks/ 结构; "
        f"策略 2: fallback 标记 {_FALLBACK_MARKERS}"
    )


def get_devroot(explicit_devroot: str = None, allow_probe: bool = True) -> Path:
    """
    获取 devroot（带缓存）。

    优先级：
    1. 显式传入参数
    2. 已缓存值
    3. 环境变量 DEVROOT
    4. 自动探测（如果 allow_probe=True）

    参数:
        explicit_devroot: 显式指定的 devroot 路径
        allow_probe: 是否允许自动探测（默认 True）

    返回:
        Path: 已验证的 devroot 绝对路径

    异常:
        RuntimeError: 无法获取有效的 devroot
    """
    global _CACHED_DEVROOT

    # 1. 显式参数
    if explicit_devroot:
        validated = validate_devroot(explicit_devroot)
        _CACHED_DEVROOT = validated
        return validated

    # 2. 缓存
    if _CACHED_DEVROOT is not None:
        return _CACHED_DEVROOT

    # 3. 环境变量
    env_devroot = os.environ.get("DEVROOT", "")
    if env_devroot:
        validated = validate_devroot(env_devroot)
        _CACHED_DEVROOT = validated
        return validated

    # 4. 自动探测
    if allow_probe:
        probed = probe_devroot()
        _CACHED_DEVROOT = probed
        return probed

    raise RuntimeError(
        "无法获取 devroot。"
        "请通过以下方式之一指定："
        "1) 显式传入参数; 2) 设置环境变量 DEVROOT; "
        "3) 确保当前文件在 devroot/references/tasks/ 的子目录下"
    )


def record_devroot(devroot_path: str) -> None:
    """
    将 devroot 记录到环境变量，供其他进程/插件使用。

    参数:
        devroot_path: devroot 路径
    """
    validated = validate_devroot(devroot_path)
    os.environ["DEVROOT"] = str(validated)
    global _CACHED_DEVROOT
    _CACHED_DEVROOT = validated


def clear_cache() -> None:
    """清除 devroot 缓存（用于测试）"""
    global _CACHED_DEVROOT
    _CACHED_DEVROOT = None


# 模块自测试
if __name__ == "__main__":
    print("Devroot 探测与验证测试")
    print("=" * 40)

    # 测试 1: 自动探测（references/tasks/ 结构）
    print("\n测试 1: 自动探测（references/tasks/ 结构）")
    try:
        clear_cache()
        devroot = get_devroot()
        print(f"探测结果: {devroot}")
        print(f"验证通过: True")
    except Exception as e:
        print(f"探测失败: {e}")

    # 测试 2: 显式指定
    print("\n测试 2: 显式指定")
    try:
        clear_cache()
        devroot = get_devroot(explicit_devroot=r"D:\pjt\cursor\cs_py")
        print(f"显式结果: {devroot}")
    except Exception as e:
        print(f"显式失败: {e}")

    # 测试 3: 记录到环境变量
    print("\n测试 3: 记录到环境变量")
    clear_cache()
    record_devroot(r"D:\pjt\cursor\cs_py")
    print(f"环境变量 DEVROOT: {os.environ.get('DEVROOT')}")
