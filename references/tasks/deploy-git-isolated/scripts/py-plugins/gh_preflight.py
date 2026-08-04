#!/usr/bin/env python3
"""
插件：gh CLI 前置检测（GH Preflight）
标签：github, gh, preflight
依赖：constants, env_config

职责：为所有 gh CLI 业务脚本提供统一的前置验证，确保隔离部署的 gh CLI
      可用、认证有效、配置目录就绪。

【真实意图：polyrepo 场景下的仓库真源上下文化】
gh CLI 的默认行为依赖当前工作目录（CWD）的 git remote 推断操作目标仓库。
在 polyrepo 工作区中，CWD 通常是 devroot（cs_py），而业务操作对象（--target）
是另一个仓库（如 jywl-settlement）。如果 preflight 只验证"工具有电"而不解析
目标仓库的 owner/repo，下游 gh pr create / gh pr view 等命令会因 CWD 错配而
操作到错误仓库，导致 Head sha can't be blank, No commits between main and ... 等
隐蔽失败。

解法：
  1. verify() / check() 接收 target 参数（操作目标仓库的绝对路径）
  2. 从 target 执行 `git remote get-url origin` 提取远程 URL
  3. 解析为 owner/repo 格式（如 matt-cch/jywl-settlement）
  4. 用 `gh repo view owner/repo` 向 GitHub 验证远程真源存在
  5. 将 owner_repo 写入 GhContext，供下游所有 gh CLI 调用显式 `--repo` 使用

这样，下游命令不再需要依赖 CWD，也不再需要自行构造 owner/repo，真源由
preflight 统一解析并携带，形成"传了 target → 带出 owner_repo → 所有 gh 命令
显式指定"的自闭环。

用法：
    import sys
    sys.path.insert(0, r"...\scripts")
    from py_lib import load_plugins
    registry = load_plugins(devroot="D:/pjt/cursor/cs_py", tags=["gh"])

    # 方式一：直接调用（失败时自动打印并退出）
    ctx = registry.gh_preflight.check(target=Path(".../jywl-settlement.wt/feat-demo"))

    # 方式二：仅验证不退出（返回结果对象）
    result = registry.gh_preflight.verify(target=Path(".../jywl-settlement.wt/feat-demo"))
    if not result.ok:
        print(result.errors)

    # 下游使用：所有 gh CLI 命令显式传 --repo，彻底消除 CWD 依赖
    ctx.run_gh(["pr", "create", "--repo", ctx.owner_repo, "--title", "..."])

返回的 GhContext 包含：
    - gh_exe: Path      gh 可执行文件绝对路径
    - gh_config_dir: Path   隔离配置目录
    - token: str        GITHUB_PAT（从 .env 读取）
    - env: dict         完整的 .env 键值对
    - username: str     gh auth status 确认的用户名（verify 时填充）
    - repo: str         当前仓库名（如 "owner/repo"）
    - owner_repo: str   从 target 解析并验证的 owner/repo 真源（polyrepo 场景）
"""
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

__plugin_registry__ = None  # 由 py_lib.py 注入


@dataclass
class GhContext:
    """gh CLI 运行上下文，preflight 验证通过后返回给业务脚本使用。"""
    ok: bool = False
    gh_exe: Path = None
    gh_config_dir: Path = None
    token: str = ""
    env: dict = field(default_factory=dict)
    username: str = ""
    repo: str = ""
    owner_repo: str = ""
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def run_gh(self, args: list, check: bool = False, **kwargs) -> subprocess.CompletedProcess:
        """
        在已验证的隔离环境下调用 gh CLI。
        自动注入 GH_TOKEN 和 GH_CONFIG_DIR。

        参数:
            args: gh 子命令参数列表，如 ["pr", "list", "-L", "5"]
            check: 是否启用 subprocess.run(check=check)
            **kwargs: 其他 subprocess.run 参数

        返回:
            subprocess.CompletedProcess
        """
        env = os.environ.copy()
        env["GH_TOKEN"] = self.token
        env["GH_CONFIG_DIR"] = str(self.gh_config_dir)
        cmd = [str(self.gh_exe)] + args
        return subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
            **kwargs,
        )


def _print_banner(title: str, width: int = 50):
    print(f"\n{'='*width}")
    print(f"[GH Preflight] {title}")
    print(f"{'='*width}")


def _parse_owner_repo(remote_url: str) -> str:
    """从 git remote URL 解析 owner/repo（如 matt-cch/jywl-settlement）。"""
    url = remote_url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return ""


def _read_env(devroot: Path) -> dict:
    """从 .env 读取键值对。"""
    env_file = devroot / ".env"
    env = {}
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                env[key] = val
    return env


def verify(devroot: Path = None, target: Path = None) -> GhContext:
    """
    执行 gh CLI 前置验证，返回 GhContext（不自动退出）。

    参数:
        devroot: 开发根目录。如未传入，尝试从 registry 或环境变量获取。
        target: 操作目标仓库路径（polyrepo 场景）。如传入，从 target 的 git remote
                解析 owner/repo 并验证远程真源，结果写入 ctx.owner_repo。

    返回:
        GhContext: 验证结果。ok=True 表示全部通过。
    """
    ctx = GhContext()

    # 1. 确定 devroot
    if devroot is None:
        # 尝试从 registry 获取
        if __plugin_registry__ is not None and hasattr(__plugin_registry__, "devroot"):
            devroot = Path(__plugin_registry__.devroot)
        else:
            devroot_str = os.environ.get("DEVROOT", r"D:\pjt\cursor\cs_py")
            devroot = Path(devroot_str)
    else:
        devroot = Path(devroot)

    # 2. 检查 gh.exe
    gh_exe = devroot / "venv" / "gh" / "bin" / "gh.exe"
    if not gh_exe.exists():
        ctx.errors.append(f"gh.exe 不存在: {gh_exe}")
        return ctx
    ctx.gh_exe = gh_exe

    # 3. 检查 GH_CONFIG_DIR
    gh_config_dir = devroot / "venv" / "data-gh"
    try:
        gh_config_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        ctx.errors.append(f"GH_CONFIG_DIR 创建失败: {e}")
        return ctx
    ctx.gh_config_dir = gh_config_dir

    # 4. 读取 .env
    env = _read_env(devroot)
    ctx.env = env
    token = env.get("GITHUB_PAT", "").strip()
    if not token:
        ctx.errors.append(".env 中 GITHUB_PAT 未配置")
        return ctx
    if token == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        ctx.errors.append(".env 中 GITHUB_PAT 仍是占位符，请填入真实 PAT")
        return ctx
    ctx.token = token

    # 5. 验证 gh CLI 版本（确认可执行）
    env_vars = os.environ.copy()
    env_vars["GH_TOKEN"] = token
    env_vars["GH_CONFIG_DIR"] = str(gh_config_dir)
    r = subprocess.run(
        [str(gh_exe), "--version"],
        env=env_vars,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode != 0:
        ctx.errors.append(f"gh --version 执行失败: {r.stderr.strip()}")
        return ctx

    # 6. 验证认证状态
    r = subprocess.run(
        [str(gh_exe), "auth", "status"],
        env=env_vars,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    # gh auth status 未登录时返回非 0，但 stdout 仍有信息
    auth_output = r.stdout if r.stdout else r.stderr
    if "Logged in to github.com" not in auth_output:
        ctx.errors.append(f"gh 认证失败: {auth_output.strip()}")
        return ctx

    # 提取用户名
    for line in auth_output.splitlines():
        if "account" in line.lower() or "Logged in to github.com" in line:
            # 典型输出: "  ✓ Logged in to github.com account matt-cch (GH_TOKEN)"
            parts = line.strip().split()
            for i, p in enumerate(parts):
                if p == "account" and i + 1 < len(parts):
                    ctx.username = parts[i + 1]
                    break
            break

    # 6.5. 如果传入了 target，从 target 解析 owner/repo 并验证远程真源
    if target is not None:
        target_path = Path(target)
        git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
        if git_exe.exists():
            r = subprocess.run(
                [str(git_exe), "-C", str(target_path), "remote", "get-url", "origin"],
                capture_output=True, text=True, encoding="utf-8"
            )
            if r.returncode == 0 and r.stdout.strip():
                owner_repo = _parse_owner_repo(r.stdout.strip())
                if owner_repo:
                    # 验证远程真源
                    r2 = subprocess.run(
                        [str(gh_exe), "repo", "view", owner_repo, "--json", "url,defaultBranchRef"],
                        env=env_vars, capture_output=True, text=True, encoding="utf-8"
                    )
                    if r2.returncode == 0 and r2.stdout.strip():
                        ctx.owner_repo = owner_repo
                        try:
                            info = json.loads(r2.stdout.strip())
                            ctx.repo = info.get("url", "").replace("https://github.com/", "")
                        except json.JSONDecodeError:
                            ctx.repo = owner_repo
                    else:
                        ctx.errors.append(f"target 远程真源验证失败: {owner_repo}")
                        return ctx
                else:
                    ctx.errors.append(f"无法从 remote URL 解析 owner/repo: {r.stdout.strip()}")
                    return ctx
            else:
                ctx.errors.append(f"无法获取 target 的 git remote: {target_path}")
                return ctx
        else:
            ctx.errors.append(f"git.exe 不存在，无法解析 target: {git_exe}")
            return ctx
    else:
        # 7. 无 target 时，回退到 CWD 推断（兼容旧行为，但发出警告）
        r = subprocess.run(
            [str(gh_exe), "repo", "view", "--json", "nameWithOwner,defaultBranchRef"],
            env=env_vars,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if r.returncode == 0 and r.stdout.strip():
            try:
                info = json.loads(r.stdout.strip())
                ctx.repo = info.get("nameWithOwner", "")
            except json.JSONDecodeError:
                pass
        ctx.warnings.append("未传入 target，gh CLI 仓库上下文依赖 CWD，polyrepo 场景下可能操作错误仓库")

    # 8. 检查 token scopes 警告
    if "Missing required token scopes" in auth_output:
        for line in auth_output.splitlines():
            if "Missing required token scopes" in line:
                ctx.warnings.append(line.strip().lstrip("! ").strip())

    ctx.ok = True
    return ctx


def check(devroot: Path = None, target: Path = None, exit_on_fail: bool = True) -> GhContext:
    """
    执行 gh CLI 前置验证，打印状态，可选失败时自动退出。

    这是业务脚本的推荐入口——直接调用，验证通过即获得可用上下文。

    参数:
        devroot: 开发根目录
        target: 操作目标仓库路径（polyrepo 场景下必填，确保 owner_repo 真源）
        exit_on_fail: 验证失败时是否 sys.exit(1)

    返回:
        GhContext: 验证通过的上下文（含 run_gh 方法）
    """
    _print_banner("前置验证")

    ctx = verify(devroot, target)

    # 打印结果
    print(f"[{'OK' if ctx.ok else 'FAIL'}] gh.exe: {ctx.gh_exe}")
    print(f"[{'OK' if ctx.ok else 'FAIL'}] GH_CONFIG_DIR: {ctx.gh_config_dir}")
    print(f"[{'OK' if ctx.ok else 'FAIL'}] GITHUB_PAT: 已读取（长度 {len(ctx.token)}）")
    if ctx.username:
        print(f"[OK] 认证用户: {ctx.username}")
    if ctx.owner_repo:
        print(f"[OK] 目标仓库（真源）: {ctx.owner_repo}")
    elif ctx.repo:
        print(f"[WARN] 当前仓库（CWD 推断）: {ctx.repo}")
    for w in ctx.warnings:
        print(f"[WARN] {w}")
    for e in ctx.errors:
        print(f"[FAIL] {e}")

    if not ctx.ok:
        print("\n[GH Preflight] ❌ 验证失败，终止执行\n")
        if exit_on_fail:
            sys.exit(1)
    else:
        print("[GH Preflight] ✅ 全部通过\n")

    return ctx
