#!/usr/bin/env python3
r"""
插件：Git 安全扫描（Git Security）
标签：git, validation
依赖：constants, git_env

职责：在 commit/push 前执行安全扫描，确保敏感文件被正确屏蔽，
      不会随 push 泄露到远程仓库。

配置：
  每个仓库根级可放置 git-security.json（与 .gitattributes 同级），
  定义该仓库专属的敏感模式。缺失时回退到本模块内建默认值。

检测项：
  1. .gitignore 存在性
  2. 关键敏感文件是否被 .gitignore 屏蔽（.env / *.pem / venv/ 等）
  3. 已 tracked / staged 文件中是否包含敏感文件
  4. 已 staged 文件中是否包含疑似敏感内容（API key、PAT、私钥正则）

用法（同层插件直接 import）：
    from git_security import scan_git_security
    result = scan_git_security(Path(r"D:\pjt\cursor\cs_py"))
    if result.violations:
        print("存在安全风险，禁止 push")
"""
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

__plugin_registry__ = None  # 由 py_lib.py 注入


@dataclass
class GitSecurityResult:
    """安全扫描结果。"""
    ok: bool = False
    violations: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    tracked_files: list = field(default_factory=list)
    staged_files: list = field(default_factory=list)
    untracked_files: list = field(default_factory=list)


# ========== 全局默认配置（fallback）==========

_DEFAULT_REQUIRED_IGNORE_PATTERNS = [
    (".env", ".env"),
    (".env.*", ".env.*"),
    ("venv/", "venv/"),
    ("*.pem", "*.pem"),
    ("*.key", "*.key"),
    ("*-key.txt", "*-key.txt"),
    ("*secret*", "*secret*"),
    ("*token*", "*token*"),
    ("*password*", "*password*"),
    ("credentials*", "credentials*"),
    ("__pycache__/", "__pycache__/"),
]

_DEFAULT_SENSITIVE_TRACKED = [
    ".env", "*.pem", "*.key",
    "id_rsa", "id_ecdsa", "id_ed25519",
]


def _load_security_config(devroot: Path) -> dict:
    """
    读取仓库根级的 git-security.json，回退到全局默认值。

    返回:
        {
            "required_ignore_patterns": [(pattern, desc), ...],
            "sensitive_tracked": [pattern, ...],
            "source": "local" | "default"
        }
    """
    config_path = devroot / "git-security.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            # 解析 required_ignore_patterns
            ignore_patterns = []
            for item in data.get("required_ignore_patterns", []):
                pattern = item.get("pattern", "")
                desc = item.get("description", pattern)
                if pattern:
                    ignore_patterns.append((pattern, desc))

            # 解析 sensitive_tracked_patterns
            tracked = data.get("sensitive_tracked_patterns", [])

            return {
                "required_ignore_patterns": ignore_patterns or _DEFAULT_REQUIRED_IGNORE_PATTERNS,
                "sensitive_tracked": tracked or _DEFAULT_SENSITIVE_TRACKED,
                "source": "local",
            }
        except Exception as e:
            # 配置文件损坏时回退到默认，并记录警告
            return {
                "required_ignore_patterns": _DEFAULT_REQUIRED_IGNORE_PATTERNS,
                "sensitive_tracked": _DEFAULT_SENSITIVE_TRACKED,
                "source": f"default (config parse error: {e})",
            }

    # 无本地配置，使用全局默认
    return {
        "required_ignore_patterns": _DEFAULT_REQUIRED_IGNORE_PATTERNS,
        "sensitive_tracked": _DEFAULT_SENSITIVE_TRACKED,
        "source": "default",
    }


def _run_git(git_exe: Path, args: list, cwd: Path) -> subprocess.CompletedProcess:
    """执行 git 命令。"""
    cmd = [str(git_exe)] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd),
    )


def _check_gitignore(devroot: Path, git_exe: Path, patterns: list) -> list:
    """检查 .gitignore 存在性及关键规则。"""
    violations = []
    gitignore = devroot / ".gitignore"
    if not gitignore.exists():
        violations.append(".gitignore 不存在")
        return violations

    content = gitignore.read_text(encoding="utf-8")
    for pattern, desc in patterns:
        # 简单检查：pattern 是否出现在 .gitignore 中（含注释行也被认为有效，宽松处理）
        if pattern not in content:
            violations.append(f".gitignore 中缺少: {desc}")
    return violations


def _check_tracked_files(devroot: Path, git_exe: Path) -> tuple[list, list, list]:
    """获取 tracked / staged / untracked 文件列表。"""
    # tracked（已跟踪）
    r = _run_git(git_exe, ["ls-files"], devroot)
    tracked = [f.strip() for f in r.stdout.splitlines() if f.strip()]

    # staged（已暂存）
    r = _run_git(git_exe, ["diff", "--cached", "--name-only"], devroot)
    staged = [f.strip() for f in r.stdout.splitlines() if f.strip()]

    # untracked（未跟踪）
    r = _run_git(git_exe, ["ls-files", "--others", "--exclude-standard"], devroot)
    untracked = [f.strip() for f in r.stdout.splitlines() if f.strip()]

    return tracked, staged, untracked


def _check_sensitive_in_staged(devroot: Path, git_exe: Path, staged_files: list) -> list:
    """扫描 staged 文件内容中的敏感模式。"""
    violations = []
    for filepath in staged_files:
        fpath = devroot / filepath
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 通过 constants 唯一真源扫描
        from constants import scan_sensitive_content
        violations.extend(scan_sensitive_content(content, filepath))
    return violations


def _check_gitignore_effectiveness(devroot: Path, git_exe: Path, patterns: list) -> list:
    """验证 .gitignore 是否包含关键规则（git check-ignore 支持对不存在的文件检查模式）。"""
    violations = []
    for pattern, desc in patterns:
        r = _run_git(git_exe, ["check-ignore", "-q", desc], devroot)
        if r.returncode != 0:
            violations.append(f"{desc} 未被 .gitignore 屏蔽")
    return violations


def scan_git_security(devroot: Path, git_exe: Path = None) -> GitSecurityResult:
    """
    执行 Git 安全扫描。

    参数:
        devroot: 开发根目录绝对路径
        git_exe: 可选，git 可执行文件路径。如未传入，自动推导

    返回:
        GitSecurityResult
    """
    result = GitSecurityResult()

    if git_exe is None:
        git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        result.violations.append(f"git.exe 不存在: {git_exe}")
        return result

    # 加载本地配置（或回退到全局默认）
    config = _load_security_config(devroot)
    if config["source"] != "local":
        result.warnings.append(f"[git-security] 使用 {config['source']} 配置")

    # 1. .gitignore 检查
    ignore_violations = _check_gitignore(devroot, git_exe, config["required_ignore_patterns"])
    result.violations.extend(ignore_violations)

    # 2. 获取文件状态
    tracked, staged, untracked = _check_tracked_files(devroot, git_exe)
    result.tracked_files = tracked
    result.staged_files = staged
    result.untracked_files = untracked

    # 3. 检查 tracked 中是否有敏感文件
    for f in tracked:
        for s in config["sensitive_tracked"]:
            if Path(f).match(s):
                result.violations.append(f"敏感文件已被 tracked: {f}")

    # 4. .gitignore 生效性验证
    effectiveness = _check_gitignore_effectiveness(devroot, git_exe, config["required_ignore_patterns"])
    result.violations.extend(effectiveness)

    # 5. staged 文件内容扫描
    if staged:
        content_violations = _check_sensitive_in_staged(devroot, git_exe, staged)
        result.violations.extend(content_violations)
    else:
        result.warnings.append("无 staged 文件（请检查是否已执行 git add），跳过内容扫描")

    result.ok = len(result.violations) == 0
    return result


def scan_quick_security(devroot: Path) -> list:
    """快速安全检查：仅返回违规列表（无文件状态详情）。"""
    r = scan_git_security(devroot)
    return r.violations
