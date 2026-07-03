#!/usr/bin/env python3
r"""
插件：运行时工具版本检测器（Runtime Version Detector）v1.0.0
标签：core, utility
依赖：process_runner

职责：检测本地可执行文件/工具的实际版本号，供 update-version 等下游工具调用。
纯 Python 实现，不依赖外部 PowerShell 脚本。

支持的检测模式：
┌──────────────────┬────────────────────────────────────────────────┐
│ mode             │ 说明                                           │
├──────────────────┼────────────────────────────────────────────────┤
│ subprocess-version│ exe --version / --ver，正则提取版本号          │
│ file-version     │ Windows PE 文件版本（纯 Python ctypes）         │
│ cursor-special   │ cursor.cmd → package.json → file-version       │
│ package-import   │ python -c "import pkg; print(pkg.__version__)" │
│ python-self      │ interpreter --version（subprocess-version 特例）│
└──────────────────┴────────────────────────────────────────────────┘

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["utility"])
    result = registry.runtime_version.detect(
        exe_path=r"D:\pjt\cursor\cs_py\venv\node\node.exe",
        mode="subprocess-version",
        version_arg="--version"
    )
    print(result["version"])  # "v26.3.1"

用法（直接 import）：
    from runtime_version import detect, resolve_path
    result = detect("${devroot}\\venv\\node\\node.exe", mode="subprocess-version")
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

# 编码由底层 process_runner 统一保障（设置+恢复闭环），本模块不再重复设置
# process_runner 加载时已执行 sys.stdout/stderr.reconfigure(encoding="utf-8")

# 复用 process_runner 做 subprocess，禁止自行调 subprocess.run
_SCRIPTS_DIR = Path(__file__).parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from process_runner import run_simple


# =============================================================================
# 路径解析
# =============================================================================

def resolve_path(path_template: str, devroot: str = "") -> str:
    """解析 ${devroot} / ${toolchainroot} / %LOCALAPPDATA% 等占位符"""
    if not devroot:
        devroot = str(_resolve_devroot())
    toolchainroot = os.environ.get("TOOLCHAINROOT", "D:\\download")
    resolved = path_template.replace("${devroot}", devroot).replace("${toolchainroot}", toolchainroot)
    resolved = os.path.expandvars(resolved)
    return resolved


def _resolve_devroot() -> Path:
    """从当前文件位置向上探测 devroot（检查 references/tasks/ 结构）"""
    current = Path(__file__).resolve().parent
    for _ in range(6):
        parent = current.parent
        if parent == current:
            break
        # devroot 特征：包含 references/tasks/ 目录
        if (parent / "references" / "tasks").exists():
            return parent
        current = parent
    # fallback：用环境变量
    env = os.environ.get("DEVROOT", "")
    if env:
        return Path(env)
    raise RuntimeError("无法探测 devroot，请设置 DEVROOT 环境变量")


# =============================================================================
# 主接口：detect
# =============================================================================

def detect(
    exe_path: str,
    mode: str = "subprocess-version",
    devroot: str = "",
    **kwargs
) -> dict:
    """
    检测单个可执行文件的本地版本。

    参数:
        exe_path: 可执行文件路径（支持 ${devroot} 占位符）
        mode: 检测模式（见模块文档）
        devroot: devroot 绝对路径（自动探测时可不传）
        **kwargs: 模式特定参数
            - subprocess-version: version_arg="--version"
            - package-import: interpreter, package_name
            - python-self: interpreter
            - cursor-special: 无
            - file-version: 无

    返回:
        {
            "version": str|None,
            "path": str,          # 解析后的绝对路径
            "status": "OK"|"ERROR",
            "source": str,        # 版本来源标识
            "error": str|None
        }
    """
    resolved = resolve_path(exe_path, devroot)
    result = {
        "version": None,
        "path": resolved,
        "status": "ERROR",
        "source": mode,
        "error": None,
    }

    if not os.path.exists(resolved):
        result["error"] = f"文件不存在: {resolved}"
        return result

    try:
        if mode == "subprocess-version":
            ver = _detect_subprocess_version(resolved, kwargs.get("version_arg", "--version"))
        elif mode == "file-version":
            ver = _detect_file_version(resolved)
        elif mode == "cursor-special":
            ver = _detect_cursor_special(resolved)
        elif mode == "package-import":
            ver = _detect_package_import(
                kwargs.get("interpreter") or resolved,
                kwargs.get("package_name", ""),
                devroot
            )
        elif mode == "python-self":
            ver = _detect_subprocess_version(kwargs.get("interpreter") or resolved, "--version")
        else:
            result["error"] = f"未知的检测模式: {mode}"
            return result

        if ver:
            result["version"] = ver
            result["status"] = "OK"
        else:
            result["error"] = "未能提取到版本号"
    except Exception as e:
        result["error"] = str(e)

    return result


# =============================================================================
# 各模式实现（全部走 process_runner.run_simple，禁止自行 subprocess.run）
# =============================================================================

def _detect_subprocess_version(exe: str, version_arg: str = "--version") -> Optional[str]:
    """exe --version → 正则提取版本号"""
    proc = run_simple([exe, version_arg], label=f"subprocess-version: {exe}")
    output = proc.stdout.strip() or proc.stderr.strip()
    if not output:
        return None
    match = re.search(r"v?(\d+(?:\.\d+)+(?:[-\w.]*))", output)
    return match.group(1) if match else None


def _detect_file_version(exe: str) -> Optional[str]:
    """
    Windows PE 文件版本读取。
    优先纯 Python ctypes（不依赖 PowerShell），失败时 fallback 到 Get-ItemProperty。
    """
    # 尝试 1：纯 Python ctypes
    ver = _get_pe_version_ctypes(exe)
    if ver:
        return ver

    # 尝试 2：PowerShell Get-ItemProperty（fallback）
    proc = run_simple(
        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command",
         f"(Get-ItemProperty '{exe}').VersionInfo.ProductVersion"],
        label=f"file-version(ps): {exe}"
    )
    ver = proc.stdout.strip()
    return ver if ver else None


def _get_pe_version_ctypes(exe: str) -> Optional[str]:
    """纯 Python ctypes 读取 Windows PE 文件 ProductVersion"""
    try:
        import ctypes
        from ctypes import wintypes

        wapi = ctypes.windll.version
        kernel32 = ctypes.windll.kernel32

        # 获取版本信息大小
        dw_dummy = wintypes.DWORD(0)
        dw_len = wapi.GetFileVersionInfoSizeW(exe, ctypes.byref(dw_dummy))
        if dw_len == 0:
            return None

        # 获取版本信息
        buf = ctypes.create_string_buffer(dw_len)
        if not wapi.GetFileVersionInfoW(exe, 0, dw_len, buf):
            return None

        # 查询语言/代码页
        u_len = wintypes.UINT(0)
        lp_buf = ctypes.c_void_p()
        if not wapi.VerQueryValueW(
            buf, r"\VarFileInfo\Translation", ctypes.byref(lp_buf), ctypes.byref(u_len)
        ):
            return None

        lang_codepage = ctypes.cast(lp_buf, ctypes.POINTER(wintypes.DWORD)).contents.value
        lang = lang_codepage & 0xFFFF
        codepage = (lang_codepage >> 16) & 0xFFFF

        # 查询 ProductVersion
        sub_block = f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\ProductVersion"
        if not wapi.VerQueryValueW(buf, sub_block, ctypes.byref(lp_buf), ctypes.byref(u_len)):
            # fallback 到 FileVersion
            sub_block = f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\FileVersion"
            if not wapi.VerQueryValueW(buf, sub_block, ctypes.byref(lp_buf), ctypes.byref(u_len)):
                return None

        return ctypes.wstring_at(lp_buf)
    except Exception:
        return None


def _detect_cursor_special(exe: str) -> Optional[str]:
    """
    cursor 专用检测：
    Priority 1: cursor.cmd --version（无 GUI 副作用，最干净）
    Priority 2: package.json version 字段
    Priority 3: PE file-version
    """
    base = os.path.dirname(exe)
    cursor_cmd = os.path.join(base, "resources", "app", "bin", "cursor.cmd")

    # P1: cursor.cmd --version
    if os.path.exists(cursor_cmd):
        try:
            ver = _detect_subprocess_version(cursor_cmd, "--version")
            if ver:
                return ver
        except Exception:
            pass

    # P2: package.json
    pkg_json = os.path.join(base, "resources", "app", "package.json")
    if os.path.exists(pkg_json):
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            ver = data.get("version")
            if ver:
                return ver
        except Exception:
            pass

    # P3: file-version fallback
    return _detect_file_version(exe)


def _detect_package_import_whl(package: str, devroot: str) -> Optional[str]:
    """从 whl 文件名正则提取版本号，作为兜底。"""
    toolchainroot = os.environ.get("TOOLCHAINROOT", "D:\\download")
    import glob
    patterns = [
        os.path.join(toolchainroot, f"{package}-*", "*.whl"),
        os.path.join(toolchainroot, f"{package}", "*.whl"),
    ]
    for pattern in patterns:
        for whl_path in glob.glob(pattern):
            basename = os.path.basename(whl_path)
            match = re.search(rf"{re.escape(package)}-(\d+\.\d+\.\d+)", basename)
            if match:
                return match.group(1)
    return None


def _detect_package_import(interpreter: str, package: str, devroot: str) -> Optional[str]:
    """
    检测 Python 包版本。
    优先直接在当前进程中 import（同进程，无 subprocess，无临时文件），
    失败时 fallback 到 whl 文件名正则提取。
    """
    if not package:
        return None
    try:
        mod = __import__(package)
        ver = getattr(mod, '__version__', None)
        if ver:
            return ver
        import importlib.metadata
        return importlib.metadata.version(package)
    except Exception:
        pass
    return _detect_package_import_whl(package, devroot)


# =============================================================================
# 模块自测试
# =============================================================================

if __name__ == "__main__":
    print("Runtime Version Detector 自测试")
    print("=" * 50)

    test_cases = [
        ("${devroot}\\venv\\py\\python.exe", "python-self", {}),
        ("${devroot}\\venv\\node\\node.exe", "subprocess-version", {"version_arg": "--version"}),
        ("${devroot}\\venv\\opencode\\opencode.exe", "subprocess-version", {"version_arg": "--version"}),
        ("${toolchainroot}\\chrome-win64\\chrome.exe", "file-version", {}),
        ("C:\\Program Files\\cursor\\Cursor.exe", "cursor-special", {}),
    ]

    for exe, mode, kwargs in test_cases:
        try:
            result = detect(exe, mode=mode, **kwargs)
            print(f"\n[{mode}] {result['path']}")
            print(f"  status: {result['status']}, version: {result['version']}, source: {result['source']}")
            if result['error']:
                print(f"  error: {result['error']}")
        except Exception as e:
            print(f"\n[{mode}] {exe} -> 异常: {e}")
