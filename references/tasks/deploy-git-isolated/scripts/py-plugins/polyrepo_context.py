#!/usr/bin/env python3
"""
插件：Polyrepo 上下文管理（Polyrepo Context）
标签：core, polyrepo

职责：统一推导、持久化和消费 polyrepo 场景下的运行时上下文。
      在 workflow 启动时生成，下游 atomic/step/plugin 通过 manifest 文件引用，
      避免各步骤自行推导导致的不一致。

上下文持久化文件（manifest）命名格式：
    polyrepo-context-{session-id}-{timestamp}.json
    例：polyrepo-context-2026-07-08T143052-20260708-143052.json

用法（同层插件直接 import）：
    from polyrepo_context import PolyrepoContext
    ctx = PolyrepoContext.from_args(toolchain_root=Path("${devroot}"), target=Path("${devroot}") / "apps" / "repos" / "jywl-team" / "jywl-lab")
    manifest_path = ctx.persist()

    # 下游消费
    ctx = PolyrepoContext.load(manifest_path)
    print(ctx.repo_url, ctx.branch)
"""
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from session_id import detect_session_id


def _run_git(git_exe: Path, args: list, cwd: Path) -> subprocess.CompletedProcess:
    """执行 git 命令，输出固定 UTF-8。"""
    cmd = [str(git_exe)] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd),
    )


def _resolve_repo_url(toolchain_root: Path, target: Path, git_exe: Path) -> str:
    """
    解析目标仓库的 remote URL。

    仅从 target 的 git remote 读取，不 fallback 到 .env，
    防止 polyrepo 场景下 repo_url 错位。
    """
    # 1. 优先从 target 的 git remote 读取
    r = _run_git(git_exe, ["-C", str(target), "remote", "get-url", "origin"], cwd=target)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()

    # 2. fallback 到 .env
    env_path = toolchain_root / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_REPO_URL="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass

    return ""


def _resolve_branch(target: Path, git_exe: Path) -> str:
    """读取 target 仓库当前分支。"""
    r = _run_git(git_exe, ["-C", str(target), "branch", "--show-current"], cwd=target)
    return r.stdout.strip() if r.returncode == 0 else ""


@dataclass
class PolyrepoContext:
    """Polyrepo 运行时上下文。"""

    toolchain_root: Path
    devroot: Path          # 同 toolchain_root，方便下游统一语义
    target: Path
    is_polyrepo: bool
    git_exe: Path
    python_exe: Path
    env_file: Path
    git_security: Path     # target 下的 git-security.json 路径
    repo_url: str
    branch: str
    session_id: str
    timestamp: str
    manifest_path: Path = None

    def __post_init__(self):
        if self.manifest_path is None:
            self.manifest_path = (
                self.toolchain_root
                / "venv"
                / "tmp"
                / f"polyrepo-context-{self.session_id}-{self.timestamp}.json"
            )

    @classmethod
    def from_args(cls, toolchain_root: Path, target: Path = None) -> "PolyrepoContext":
        """
        从参数构造 PolyrepoContext。

        参数:
            toolchain_root: 工具链根目录绝对路径
            target: 操作目标仓库绝对路径。省略时默认等于 toolchain_root
        """
        if target is None:
            target = toolchain_root

        is_polyrepo = target.resolve() != toolchain_root.resolve()

        git_exe = toolchain_root / "venv" / "git" / "cmd" / "git.exe"
        python_exe = toolchain_root / "venv" / "py" / "python.exe"
        env_file = toolchain_root / ".env"

        session_id = detect_session_id(toolchain_root)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

        repo_url = _resolve_repo_url(toolchain_root, target, git_exe)
        branch = _resolve_branch(target, git_exe)

        return cls(
            toolchain_root=toolchain_root,
            devroot=toolchain_root,
            target=target,
            is_polyrepo=is_polyrepo,
            git_exe=git_exe,
            python_exe=python_exe,
            env_file=env_file,
            git_security=target / "git-security.json",
            repo_url=repo_url,
            branch=branch,
            session_id=session_id,
            timestamp=timestamp,
        )

    def persist(self) -> Path:
        """将上下文序列化到 manifest 文件，返回文件路径。"""
        data = {
            "toolchain_root": str(self.toolchain_root),
            "devroot": str(self.devroot),
            "target": str(self.target),
            "is_polyrepo": self.is_polyrepo,
            "git_exe": str(self.git_exe),
            "python_exe": str(self.python_exe),
            "env_file": str(self.env_file),
            "git_security": str(self.git_security),
            "repo_url": self.repo_url,
            "branch": self.branch,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "manifest_path": str(self.manifest_path),
        }
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.manifest_path

    @classmethod
    def load(cls, manifest_path: Path) -> "PolyrepoContext":
        """从 manifest 文件反序列化。"""
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return cls(
            toolchain_root=Path(data["toolchain_root"]),
            devroot=Path(data.get("devroot", data["toolchain_root"])),
            target=Path(data["target"]),
            is_polyrepo=data["is_polyrepo"],
            git_exe=Path(data["git_exe"]),
            python_exe=Path(data["python_exe"]),
            env_file=Path(data["env_file"]),
            git_security=Path(data.get("git_security", str(Path(data["target"]) / "git-security.json"))),
            repo_url=data["repo_url"],
            branch=data["branch"],
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            manifest_path=Path(data["manifest_path"]),
        )
