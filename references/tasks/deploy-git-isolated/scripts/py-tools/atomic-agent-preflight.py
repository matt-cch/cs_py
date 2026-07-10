#!/usr/bin/env python3
r"""
atomic-agent-preflight.py — Agent / LLM 探活预检原子工具
标签：py-tools
版本：v1.0.0

职责：在调用 LLM 生成摘要或其他耗时任务前，先发送轻量级探活请求，
      确认 AgentCore 初始化成功且 LLM 服务可达，避免长时间堵塞后才发现 429/5xx。
      执行后自动生成 manifest JSON，供 workflow 审计追踪。

用法：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-agent-preflight.py" --devroot "${devroot}"

参数：
    --devroot   工具链根路径（默认 Path.cwd()）
    --prompt    自定义探活 prompt（默认：请仅回复'OK'...）
    --manifest  manifest 输出路径（默认：devroot/venv/tmp/agent-preflight-{ts}.json）

返回（stdout 最后一行 JSON）：
    {"success": true, "model": "kimi-k2.6", "base_url": "...", "response_time_ms": 2710, "response_preview": "OK", "manifest": "..."}
    {"success": false, "error": "..."}
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent / LLM 探活预检原子工具")
    parser.add_argument("--devroot", default=None, help="工具链根路径（默认 Path.cwd()）")
    parser.add_argument("--prompt", default="请仅回复'OK'，不要添加任何其他内容。", help="自定义探活 prompt")
    parser.add_argument("--manifest", default=None, help="manifest 输出路径。由上游 workflow 显式命名传入，便于上下文追踪。未传入时回退到 devroot/venv/tmp/agent-preflight-{ts}.json")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}", file=sys.stderr)
        return 1

    print(f"[{datetime.now().isoformat()}] [Progress] Agent Preflight 开始 — devroot={devroot}")
    sys.stdout.flush()
    overall_start = time.time()

    result = {
        "success": False,
        "model": None,
        "base_url": None,
        "response_time_ms": None,
        "response_preview": None,
        "error": None,
        "manifest": None,
    }

    try:
        print(f"[{datetime.now().isoformat()}] [Progress] 加载 agent 插件体系...")
        sys.stdout.flush()
        step_start = time.time()
        registry = load_plugins(devroot=str(devroot), profile="agent")
        print(f"[{datetime.now().isoformat()}] [Progress] 插件加载完成 (耗时 {time.time() - step_start:.2f}s)")
        sys.stdout.flush()

        provider_cfg = registry.provider_config.get_provider(source="config_json")
        result["model"] = provider_cfg.get("model")
        result["base_url"] = provider_cfg.get("base_url")
        print(f"[{datetime.now().isoformat()}] [Progress] Provider: model={result['model']} | base_url={result['base_url']}")
        sys.stdout.flush()

        print(f"[{datetime.now().isoformat()}] [Progress] AgentCore 初始化...")
        sys.stdout.flush()
        step_start = time.time()
        agent = registry.agent_core.AgentCore(
            enable_tools=False,
            provider_cfg=provider_cfg,
        )
        print(f"[{datetime.now().isoformat()}] [Progress] AgentCore 初始化完成 (耗时 {time.time() - step_start:.2f}s)")
        sys.stdout.flush()

        print(f"[{datetime.now().isoformat()}] [Progress] 发送探活请求...")
        sys.stdout.flush()
        llm_start = time.time()
        response = agent.run(
            prompt=args.prompt,
            system="你是测试助手。",
            max_turns=1,
        )
        response_time_ms = (time.time() - llm_start) * 1000
        result["response_time_ms"] = round(response_time_ms, 1)
        result["response_preview"] = response[:100] if response else "(空响应)"
        result["success"] = True

        print(f"[{datetime.now().isoformat()}] [Progress] 探活成功 (耗时 {response_time_ms / 1000:.2f}s)，响应: {result['response_preview']}...")
        sys.stdout.flush()

    except Exception as e:
        elapsed = time.time() - overall_start
        result["error"] = str(e)
        print(f"[{datetime.now().isoformat()}] [Progress] 探活失败 (耗时 {elapsed:.2f}s): {e}", file=sys.stderr)
        sys.stdout.flush()

    # 生成 manifest
    manifest = {
        "meta": {
            "script": str(Path(__file__).resolve()),
            "version": "1.0.0",
            "tag": "py-tools",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "devroot": str(devroot),
        },
        "request": {
            "prompt": args.prompt,
            "model": result["model"],
            "base_url": result["base_url"],
        },
        "response": {
            "success": result["success"],
            "response_time_ms": result["response_time_ms"],
            "response_preview": result["response_preview"],
            "error": result["error"],
        },
    }

    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    manifest_path = Path(args.manifest) if args.manifest else manifest_dir / f"agent-preflight-{ts}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    result["manifest"] = str(manifest_path)

    print(f"[{datetime.now().isoformat()}] [Progress] Manifest 已生成: {manifest_path}")
    sys.stdout.flush()

    # stdout 最后一行输出 JSON，供上游脚本解析
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
