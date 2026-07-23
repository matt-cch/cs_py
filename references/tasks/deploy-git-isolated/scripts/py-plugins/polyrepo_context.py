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


def _resolve_repo_url(toolchain_root: Path, target: Path, git_exe: Path) -> tuple[str, str]:
    """
    解析目标仓库的 remote URL（基准 vs 实测对碰模型）。

    返回 (resolved_url, source_hint):
      - resolved_url: 解析到的 URL（空字符串表示未找到）
      - source_hint: 来源标记，用于日志（git-remote / git-security / .env / none）

    对碰逻辑：
      1. 读取 git-security.json 中的 repo_url（基准/审计真源）
      2. 读取 git remote get-url origin（实测值）
      3. 两者均存在但不一致 → 返回 ("", "mismatch")，调用方应报错阻断
      4. 仅 git-security 有值 → 返回该值（适用于初次 clone 未设置 origin 的场景）
      5. 仅 git-remote 有值 → 返回该值
      6. 两者均无 → fallback 到 .env（兼容旧场景，已淘汰）
    """
    # 1. 读取基准（git-security.json）
    security_url = ""
    security_path = target / "git-security.json"
    if security_path.exists():
        try:
            data = json.loads(security_path.read_text(encoding="utf-8"))
            security_url = data.get("repo_url", "").strip()
        except Exception:
            pass

    # 2. 读取实测（git remote）
    r = _run_git(git_exe, ["-C", str(target), "remote", "get-url", "origin"], cwd=target)
    remote_url = r.stdout.strip() if (r.returncode == 0 and r.stdout.strip()) else ""

    # 3. 对碰
    if security_url and remote_url:
        if security_url == remote_url:
            return remote_url, "git-remote+git-security"
        return "", "mismatch"

    if security_url:
        return security_url, "git-security"

    if remote_url:
        return remote_url, "git-remote"

    # 4. fallback 到 .env（已淘汰的 anti-pattern）
    env_path = toolchain_root / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_REPO_URL="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'"), ".env"
        except Exception:
            pass

    return "", "none"


def _resolve_branch(target: Path, git_exe: Path) -> str:
    """读取 target 仓库当前分支。"""
    r = _run_git(git_exe, ["-C", str(target), "branch", "--show-current"], cwd=target)
    return r.stdout.strip() if r.returncode == 0 else ""


def _resolve_default_branch(target: Path) -> str:
    """
    读取 target 仓库的默认分支。

    优先级：
      1. git-security.json → default_branch
      2. 返回 "main"（兜底，符合当前潮流）
    """
    security_path = target / "git-security.json"
    if security_path.exists():
        try:
            data = json.loads(security_path.read_text(encoding="utf-8"))
            db = data.get("default_branch", "").strip()
            if db:
                return db
        except Exception:
            pass
    return "main"


def _load_security_config(target: Path) -> dict:
    """
    读取 target 仓库的 git-security.json，返回安全策略字典。

    返回字段：
      - repo_url: str
      - default_branch: str
      - allow_direct_push_to: list[str]
      - security_level: str
    """
    defaults = {
        "repo_url": "",
        "default_branch": "main",
        "allow_direct_push_to": [],
        "security_level": "normal",
    }
    security_path = target / "git-security.json"
    if security_path.exists():
        try:
            data = json.loads(security_path.read_text(encoding="utf-8"))
            defaults["repo_url"] = data.get("repo_url", "").strip()
            defaults["default_branch"] = data.get("default_branch", "main").strip()
            defaults["allow_direct_push_to"] = data.get("allow_direct_push_to", [])
            defaults["security_level"] = data.get("security_level", "normal").strip()
        except Exception:
            pass
    return defaults


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
    default_branch: str
    allow_direct_push_to: list
    security_level: str
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

        repo_url, _ = _resolve_repo_url(toolchain_root, target, git_exe)
        branch = _resolve_branch(target, git_exe)
        sec_cfg = _load_security_config(target)

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
            default_branch=sec_cfg["default_branch"],
            allow_direct_push_to=sec_cfg["allow_direct_push_to"],
            security_level=sec_cfg["security_level"],
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
            "default_branch": self.default_branch,
            "allow_direct_push_to": self.allow_direct_push_to,
            "security_level": self.security_level,
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
            default_branch=data.get("default_branch", "main"),
            allow_direct_push_to=data.get("allow_direct_push_to", []),
            security_level=data.get("security_level", "normal"),
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            manifest_path=Path(data["manifest_path"]),
        )
