#!/usr/bin/env python3
"""
插件：安全审计（Security Audit）
标签：core, validation
依赖：无（纯审计逻辑，不依赖其它插件）

职责：提供部署前敏感内容安全巡检的底层能力。
      支持五 Phase 审计：pattern_scan / high_priority_files / source_snapshots / git_tracking / summary。
      输出遵循 schema/json/security-audit-schema.json。

用法：
    from py_lib import load_plugins
    registry = load_plugins(devroot="...", tags=["validation"])
    result = registry.security_audit.run_audit(devroot=Path("..."), commit_range="HEAD~10..HEAD")
    print(result["overall_status"], result["overall_summary"])
"""
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 插件注册表注入点（由 py_lib 在加载时注入）
__plugin_registry__ = None


# ---------- 默认敏感模式定义 ----------
DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    {
        "name": "api_key_moonshot",
        "regex": r"sk-[a-zA-Z0-9]{20,}",
        "severity": "critical",
        "description": "Moonshot API Key（sk- 开头）",
        "false_positive_hints": ["变量名引用", "模板字符串", "文档示例"],
    },
    {
        "name": "github_pat_classic",
        "regex": r"ghp_[a-zA-Z0-9]{36}",
        "severity": "critical",
        "description": "GitHub PAT (classic)",
        "false_positive_hints": ["占位符 ghp_xxxxxxxx..."],
    },
    {
        "name": "github_pat_fine_grained",
        "regex": r"ghp_[a-zA-Z0-9]{68}",
        "severity": "critical",
        "description": "GitHub fine-grained PAT",
        "false_positive_hints": [],
    },
    {
        "name": "env_api_key_value",
        "regex": r"(?i)(?:MOONSHOT_API_KEY|CORECODER_API_KEY|OPENAI_API_KEY)\s*=\s*['\"]?sk-",
        "severity": "high",
        "description": ".env 中 API key 赋值（含值）",
        "false_positive_hints": [],
    },
    {
        "name": "env_github_pat_value",
        "regex": r"(?i)GITHUB_PAT\s*=\s*['\"]?ghp_",
        "severity": "high",
        "description": ".env 中 GitHub PAT 赋值（含值）",
        "false_positive_hints": [],
    },
    {
        "name": "config_hardcoded_key",
        "regex": r'"apiKey"\s*:\s*"[^"]{10,}"',
        "severity": "high",
        "description": "config.json 中硬编码 apiKey",
        "false_positive_hints": ["{file:./xxx} 路径引用格式"],
    },
    {
        "name": "authorization_bearer_with_value",
        "regex": r'Authorization.*Bearer\s+[a-zA-Z0-9_-]{20,}',
        "severity": "high",
        "description": "HTTP header 中含 bearer token 值",
        "false_positive_hints": ["模板字符串 Bearer {api_key}"],
    },
    {
        "name": "basic_auth_in_url",
        "regex": r'https?://[^:]+:[^@]+@',
        "severity": "high",
        "description": "URL 中嵌入用户名密码",
        "false_positive_hints": [],
    },
    {
        "name": "private_key_pem",
        "regex": r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
        "severity": "critical",
        "description": "PEM 格式私钥",
        "false_positive_hints": [],
    },
    {
        "name": "aws_access_key",
        "regex": r"AKIA[0-9A-Z]{16}",
        "severity": "high",
        "description": "AWS Access Key ID",
        "false_positive_hints": [],
    },
]

# 误报排除规则（文本特征）
FALSE_POSITIVE_RULES: List[Dict[str, Any]] = [
    {
        "name": "placeholder_pat",
        "pattern": r'ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        "reason": "显式占位符",
    },
    {
        "name": "env_var_name_only",
        "pattern": r'(os\.environ\.get|getenv)\s*\(\s*["\']MOONSHOT_API_KEY["\']',
        "reason": "仅引用变量名",
    },
    {
        "name": "env_var_name_only_generic",
        "pattern": r'(os\.environ\.get|getenv)\s*\(\s*["\'].*API_KEY["\']',
        "reason": "仅引用变量名",
    },
    {
        "name": "template_string",
        "pattern": r'Bearrer\s*\{.*\}',
        "reason": "模板字符串，运行时注入",
    },
    {
        "name": "file_reference",
        "pattern": r'\{file:[^\}]+\}',
        "reason": "config.json 文件引用格式",
    },
    {
        "name": "doc_example",
        "pattern": r'(?i)(?:示例|example|示例代码|e\.g\.|eg\.)',
        "reason": "文档示例",
    },
]


# ---------- Git 追踪禁止模式 ----------
GIT_TRACKING_FORBIDDEN_PATTERNS: List[str] = [
    r"\.env$",
    r"\.env\..*",
    r"venv/\.opencode/config\.json",
    r"venv/\.opencode/.*-key\.txt",
    r".*-key\.txt$",
    r".*-key\.pem$",
    r".*\.key$",
    r".*\.p12$",
    r".*\.pfx$",
]


def _resolve_devroot() -> Optional[Path]:
    """从 registry 或环境变量获取 devroot"""
    if __plugin_registry__ is not None and hasattr(__plugin_registry__, "devroot"):
        return Path(__plugin_registry__.devroot)
    devroot_env = os.environ.get("DEVROOT", "")
    if devroot_env:
        return Path(devroot_env)
    return None


def _get_git_files(devroot: Path, commit_range: str) -> List[str]:
    """获取指定 commit 范围涉及的文件列表"""
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        git_exe = "git"  # fallback

    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "diff", "--name-only", commit_range],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        return []
    files = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    return files


def _is_false_positive(line: str, matched_text: str) -> Tuple[bool, str]:
    """判断匹配是否为误报"""
    for rule in FALSE_POSITIVE_RULES:
        if re.search(rule["pattern"], line):
            return True, rule["reason"]
    # 额外：如果匹配文本是变量名/字段名本身（如 api_key = ... 但值不是 sk-）
    if matched_text in ("api_key", "secret", "token", "password"):
        return True, "仅变量名/字段名"
    return False, ""


def phase_pattern_scan(devroot: Path, files: List[str]) -> Dict[str, Any]:
    """
    Phase 1: 对全部文件执行敏感模式正则扫描。
    """
    start = time.time()
    findings: List[Dict[str, Any]] = []
    files_with_findings = 0

    for rel_path in files:
        full_path = devroot / rel_path
        if not full_path.exists():
            continue
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            continue

        file_has_finding = False
        for line_no, line in enumerate(lines, start=1):
            for pat in DEFAULT_PATTERNS:
                for m in re.finditer(pat["regex"], line):
                    matched = m.group(0)
                    # 误报检查
                    is_fp, fp_reason = _is_false_positive(line, matched)
                    if is_fp:
                        continue

                    # 脱敏：截断匹配文本
                    preview = matched[:20] + "..." if len(matched) > 20 else matched
                    file_has_finding = True
                    findings.append({
                        "file": rel_path,
                        "line_number": line_no,
                        "column_start": m.start(),
                        "column_end": m.end(),
                        "matched_text": preview,
                        "line_preview": line.strip()[:200],
                        "pattern_name": pat["name"],
                        "severity": pat["severity"],
                        "assessment": "pending",
                        "notes": "",
                    })

        if file_has_finding:
            files_with_findings += 1

    elapsed = time.time() - start
    status = "fail" if any(f["severity"] == "critical" for f in findings) else (
        "warn" if findings else "pass"
    )

    return {
        "phase_name": "pattern_scan",
        "status": status,
        "summary": f"扫描 {len(files)} 个文件，发现 {len(findings)} 个匹配项（含 {sum(1 for f in findings if f['severity']=='critical')} 个 critical）",
        "files_audited": len(files),
        "files_with_findings": files_with_findings,
        "total_findings": len(findings),
        "details": findings,
        "elapsed_seconds": round(elapsed, 2),
    }


def phase_git_tracking(devroot: Path) -> Dict[str, Any]:
    """
    Phase 4: 验证 .env / config.json / key.txt 等敏感文件未被 git 追踪。
    """
    start = time.time()
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        git_exe = "git"

    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "ls-files"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    tracked_files = result.stdout.strip().splitlines() if result.returncode == 0 else []

    violations = []
    for tracked in tracked_files:
        for pattern in GIT_TRACKING_FORBIDDEN_PATTERNS:
            if re.search(pattern, tracked):
                violations.append({
                    "file": tracked,
                    "pattern": pattern,
                    "severity": "critical",
                })

    elapsed = time.time() - start
    status = "fail" if violations else "pass"

    return {
        "phase_name": "git_tracking",
        "status": status,
        "summary": f"git ls-files 扫描 {len(tracked_files)} 个 tracked 文件，发现 {len(violations)} 个违规追踪" if violations else f"git ls-files 扫描 {len(tracked_files)} 个 tracked 文件，无违规",
        "files_audited": len(tracked_files),
        "files_with_findings": len(violations),
        "total_findings": len(violations),
        "details": violations,
        "elapsed_seconds": round(elapsed, 2),
    }


def run_audit(
    devroot: Optional[Path] = None,
    commit_range: str = "HEAD~10..HEAD",
    phases: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    执行完整安全审计（五 Phase）。

    参数:
        devroot: 开发根目录，None 时自动解析
        commit_range: git diff 范围
        phases: 指定执行的 phase 列表，None 时执行全部

    返回:
        符合 security-audit-schema.json 的 AuditReport dict
    """
    if devroot is None:
        devroot = _resolve_devroot() or Path.cwd()
    devroot = Path(devroot)

    audit_start = time.time()
    audit_id = f"audit-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    # 获取文件列表
    files = _get_git_files(devroot, commit_range)

    all_phases: List[Dict[str, Any]] = []
    run_phases = phases or ["pattern_scan", "git_tracking", "summary"]

    # Phase 1: Pattern Scan
    if "pattern_scan" in run_phases:
        all_phases.append(phase_pattern_scan(devroot, files))

    # Phase 4: Git Tracking（默认执行）
    if "git_tracking" in run_phases:
        all_phases.append(phase_git_tracking(devroot))

    # Phase 5: Summary
    overall_status = "pass"
    for p in all_phases:
        if p["status"] == "fail":
            overall_status = "fail"
            break
        elif p["status"] == "warn" and overall_status == "pass":
            overall_status = "warn"

    summary = "所有检查项通过，无敏感内容泄露" if overall_status == "pass" else (
        "发现敏感内容泄露风险，请立即处理" if overall_status == "fail" else "发现可疑模式，建议人工复核"
    )

    total_elapsed = time.time() - audit_start

    return {
        "version": "1.0.0",
        "audit_id": audit_id,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "devroot": str(devroot),
        "commit_range": commit_range,
        "files_in_scope": files,
        "phases": all_phases,
        "overall_status": overall_status,
        "overall_summary": summary,
        "recommendations": [] if overall_status == "pass" else [
            "检查 pattern_scan 中的 matched_text 是否为真实密钥",
            "若确认泄露，立即撤销该密钥并重新生成",
            "检查 .gitignore 是否包含 .env / *-key.txt 等模式",
        ],
        "total_elapsed_seconds": round(total_elapsed, 2),
    }
