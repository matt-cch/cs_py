#!/usr/bin/env python3
r"""
atomic-chrome-login-interactive.py — Chrome 交互式登录原子 CLI
标签：py-tools
版本：v1.0.0

职责：
  启动交互式 Chrome 浏览器窗口，让用户在持久化 Profile 中手动完成登录或续期操作。
  通过 py_lib 统一入口加载 browser_session 插件，复用已有 Chrome Session（如有），
  操作完成后 session / cookies 自动保留在 user-data-dir 中。

  典型续期流程（以头条为例）：
    1. 执行本脚本，Chrome 窗口打开并自动登录（利用现有有效 Session）
    2. 用户在网页端手动退出账号
    3. 用户重新扫码或密码登录
    4. 服务端下发新 cookie，TTL 重置
    5. 用户将地址栏导航到 https://example.com 结束会话（或等待超时）

审计产物与追踪路径：
  - 交互式会话 manifest:
      由调用者通过 `--output` 显式指定路径，pipeline 连贯工作时必须传入。
      记录开始时间、目标 URL、user_data_dir、超时设定、完成状态。

参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --devroot | str | 否 | 自动探测 | 工具链根绝对路径 |
| --url | str | 否 | https://www.toutiao.com | 目标登录页面 URL |
| --timeout | int | 否 | 300 | 等待用户结束会话的超时秒数 |
| --output | str | ✅ | 无 | manifest 输出路径（pipeline 调用时必须显式指定） |

调用示例：

  # 默认打开头条（用于续期头条 Session），显式指定 manifest 输出路径
  python atomic-chrome-login-interactive.py --output "venv/tmp/chrome-login-interactive-manifest.json"

  # 指定 GitHub 登录页
  python atomic-chrome-login-interactive.py --url "https://github.com/login" --output "venv/tmp/github-login-manifest.json"

  # 指定 devroot 与超时
  python atomic-chrome-login-interactive.py --devroot "D:/workspace/other-repo" --timeout 600 --output "venv/tmp/login-manifest.json"

返回码：
  0 — 会话正常结束（用户导航到 example.com 或超时后关闭）
  1 — 插件加载失败、Chrome 路径缺失或其他异常
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _devroot() -> str:
    """推断 devroot（向上探测到包含 verified-runtime-index.json 的目录）"""
    current = Path(__file__).resolve()
    while current.parent != current:
        candidate = current.parent
        if (candidate / "references" / "runtime" / "verified-runtime-index.json").exists():
            return str(candidate)
        current = candidate
    raise RuntimeError("无法自动探测 devroot：未找到 references/runtime/verified-runtime-index.json")


def _build_manifest(
    url: str,
    user_data_dir: str,
    timeout: int,
    started_at: str,
    finished_at: str,
    status: str,
) -> dict:
    """构造结构化 manifest。"""
    return {
        "meta": {
            "generated_at": finished_at,
            "tool": "atomic-chrome-login-interactive",
            "version": "1.0.0",
        },
        "environment": {
            "user_data_dir": user_data_dir,
        },
        "session": {
            "url": url,
            "timeout_seconds": timeout,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
        },
    }


def _write_manifest(manifest: dict, output_path: Path) -> Path:
    """写入 manifest 并回读验证。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # 回读验证
    data = json.loads(output_path.read_text(encoding="utf-8"))
    print(f"[Chrome Login] 📄 Manifest 已保存: {output_path}")
    print(f"[Chrome Login] 📄 Manifest 状态: {data['session']['status']}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Chrome 交互式登录")
    parser.add_argument("--devroot", default=None, help="工具链根绝对路径（默认自动探测）")
    parser.add_argument("--url", default="https://www.toutiao.com", help="目标登录页面 URL")
    parser.add_argument("--timeout", type=int, default=300, help="等待超时秒数（默认 300s）")
    parser.add_argument("--output", required=True, help="manifest 输出路径（pipeline 调用时必须显式指定）")
    args = parser.parse_args()

    devroot = args.devroot or _devroot()
    started_at = datetime.now(timezone.utc).isoformat()

    # 通过 py_lib 加载 Layer 1 插件（禁止直接 import browser_session）
    try:
        from py_lib import load_plugins
        registry = load_plugins(devroot=devroot, tags=["core", "browser"])
        bs = registry.browser_session.BrowserSession(devroot=devroot)
    except Exception as e:
        print(f"[Chrome Login] ❌ 插件加载失败: {e}")
        sys.exit(1)

    print(f"[Chrome Login] 启动交互式 Chrome")
    print(f"[Chrome Login] 目标 URL: {args.url}")
    print(f"[Chrome Login] 超时设定: {args.timeout} 秒")
    print(f"[Chrome Login] user-data-dir: {bs.user_data_dir}")
    print("[Chrome Login] 请在浏览器中完成登录/续期操作。")
    print("[Chrome Login] 完成后请将地址栏导航到 https://example.com 以结束会话...")

    try:
        bs.interactive_login(url=args.url, timeout=args.timeout)
        status = "completed"
        print("[Chrome Login] ✅ 交互式会话已结束，session / cookies 已保留")
    except Exception as e:
        status = f"error: {e}"
        print(f"[Chrome Login] ❌ 交互式会话异常: {e}")
        sys.exit(1)
    finally:
        finished_at = datetime.now(timezone.utc).isoformat()

        manifest = _build_manifest(
            url=args.url,
            user_data_dir=bs.user_data_dir,
            timeout=args.timeout,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
        )

        manifest_path = Path(args.output)
        _write_manifest(manifest, manifest_path)

    sys.exit(0)


if __name__ == "__main__":
    main()
