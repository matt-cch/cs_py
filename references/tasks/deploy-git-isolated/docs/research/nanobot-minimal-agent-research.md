---
title: 自研极简 Agent（Nanobot）与外部 CLI Agent 的路线对比
description: 基于 OpenCode/Aider 源码分析，提炼自研极简 Agent 的最小可行架构，并与进程级集成外部 CLI 进行全维度对比。
date: 2026-06-22
meta:
  version: 1.0.0
  parent_research: cli-agent-integration-research.md
---

# 自研极简 Agent（Nanobot）路线研究

> **研究触发**：用户在 `cli-agent-integration-research.md` 基础上提出「nanobot 极简智能体」思想——不依赖外部 CLI 工具，自己实现 Agent 核心循环。
> 
> **核心问题**：自己写一个极简 Agent 需要多少代码？与调用 Pi/OpenCode 等外部 CLI 相比，哪种路线更适合 deploy-git-isolated workflow？

***

## 1. 什么是「nanobot」思想

**定义**：用最小代码量（几十到几百行）实现一个功能完整的 AI Agent，不依赖任何外部 CLI 框架，直接通过 HTTP API 与 LLM 交互。

**核心信念**：
- OpenCode（Go）和 Aider（Python）虽然功能强大，但代码量巨大（Aider 的 `base_coder.py` 就超过 35,000 行），大部分功能（TUI、Git 集成、LSP、多模型适配）在 workflow 场景下是冗余的。
- 一个 Agent 的本质就是：**循环调用 LLM，直到任务完成**。这个核心逻辑可以用不到 100 行 Python 实现。
- 自研 Agent = 白盒、零依赖（除 `requests`/`httpx`）、完全可控。

***

## 2. 自研 Agent 的最小可行架构（MVP）

基于对 OpenCode `processGeneration`（标准 ReAct）和 Aider `send_message`（单次生成+反射）的源码分析，一个极简 Agent 的核心只需要三层：

### 2.1 第一层：单次 LLM 调用（~20 行）

这是 90% 的 workflow 场景（包括我们的「读 diff → 生成摘要」）所需的全部：

```python
import httpx
import os

def chat(messages, model="kimi-k2.5", api_key=None, base_url=None):
    """最小 LLM 调用，OpenAI 兼容格式。"""
    api_key = api_key or os.environ["MOONSHOT_API_KEY"]
    base_url = (base_url or "https://api.moonshot.cn/v1").rstrip("/")
    
    r = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": 0.3},
        timeout=120.0,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"], data["choices"][0].get("finish_reason")
```

### 2.2 第二层：标准 ReAct 循环（~40 行）

当任务需要多步推理（如「读文件 → 分析 → 写文件 → 验证」）时，需要标准的 ReAct 循环：

```python
def run_agent(prompt, tools, system="你是一个 helpful assistant"):
    """标准 ReAct Agent：思考 → 工具调用 → 观察 → 再思考。"""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    
    for _ in range(10):  # 最大 10 轮，防止无限循环
        message, finish_reason = chat(messages, tools=tools)
        
        if finish_reason == "tool_calls":
            # LLM 要求执行工具
            messages.append(message)
            for tool_call in message["tool_calls"]:
                result = execute_tool(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": str(result),
                })
            continue  # 继续循环，让 LLM 基于工具结果再生成
        
        # finish_reason == "stop" 或 "length"，直接返回答案
        return message.get("content", "")
    
    return "（Agent 达到最大轮次，未收敛）"
```

**与 OpenCode 源码的对应关系**：

| 极简实现 | OpenCode 源码 | 说明 |
|---------|--------------|------|
| `for _ in range(10)` | `processGeneration` 中的 `for {}` | OpenCode 用无限循环 + `ctx.Done()` 取消 |
| `finish_reason == "tool_calls"` | `agentMessage.FinishReason() == message.FinishReasonToolUse` | 完全等价 |
| `messages.append(message)` | `msgHistory = append(msgHistory, agentMessage)` | 追加 assistant 消息 |
| `execute_tool(tool_call)` | `tool.Run(ctx, tools.ToolCall{...})` | 工具执行 |
| `messages.append({role:"tool"...})` | `msgHistory = append(msgHistory, *toolResults)` | 追加 tool 结果 |

**结论**：OpenCode 的 `processGeneration`（~150 行 Go）的核心逻辑，用 Python 只需要 ~40 行。

### 2.3 第三层：工具注册与执行（~30 行）

```python
_registry = {}

def tool(name, description, params_schema):
    """工具装饰器。"""
    def decorator(fn):
        _registry[name] = {"fn": fn, "description": description, "params": params_schema}
        return fn
    return decorator

@tool("read_file", "读取文件内容", {"path": {"type": "string", "description": "文件路径"}})
def read_file(path):
    return Path(path).read_text(encoding="utf-8")

@tool("bash", "执行 shell 命令", {"cmd": {"type": "string", "description": "命令"}})
def bash(cmd):
    import subprocess
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

def execute_tool(tool_call):
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])
    if name not in _registry:
        return f"未知工具: {name}"
    return _registry[name]["fn"](**args)

def get_tools_spec():
    """生成 OpenAI function calling 格式的 tools 定义。"""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": meta["description"],
                "parameters": {"type": "object", "properties": meta["params"], "required": list(meta["params"].keys())},
            },
        }
        for name, meta in _registry.items()
    ]
```

### 2.4 完整极简 Agent：不到 100 行

```python
"""
nanobot.py — 极简 Agent，不到 100 行核心代码。
依赖：pip install httpx
"""
import json, os, httpx
from pathlib import Path

# ---------- 配置 ----------
API_KEY = os.environ.get("MOONSHOT_API_KEY")
BASE_URL = os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/")
MODEL = os.environ.get("NANOBOT_MODEL", "kimi-k2.5")
MAX_ROUNDS = int(os.environ.get("NANOBOT_MAX_ROUNDS", "10"))

# ---------- 工具注册 ----------
_registry = {}
def tool(name, description, params):
    def decorator(fn):
        _registry[name] = {"fn": fn, "description": description, "params": params}
        return fn
    return decorator

@tool("read_file", "读取文件", {"path": {"type": "string"}})
def _read_file(path): return Path(path).read_text(encoding="utf-8", errors="replace")

@tool("bash", "执行命令", {"cmd": {"type": "string"}})
def _bash(cmd):
    import subprocess
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

def _execute_tool(tc):
    name, args = tc["function"]["name"], json.loads(tc["function"]["arguments"])
    return _registry[name]["fn"](**args) if name in _registry else f"未知工具: {name}"

def _tools_spec():
    return [{"type": "function", "function": {"name": n, "description": m["description"], "parameters": {"type": "object", "properties": m["params"], "required": list(m["params"])}}} for n, m in _registry.items()]

# ---------- LLM 调用 ----------
def _chat(messages, tools=None):
    payload = {"model": MODEL, "messages": messages, "temperature": 0.3}
    if tools: payload["tools"] = tools
    r = httpx.post(f"{BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=120)
    r.raise_for_status()
    c = r.json()["choices"][0]
    return c["message"], c.get("finish_reason")

# ---------- Agent 循环 ----------
def run(prompt, system="你是一个 helpful assistant"):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    for _ in range(MAX_ROUNDS):
        msg, reason = _chat(msgs, _tools_spec() if _registry else None)
        if reason == "tool_calls":
            msgs.append(msg)
            for tc in msg.get("tool_calls", []):
                msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": str(_execute_tool(tc))})
            continue
        return msg.get("content", "")
    return "（达到最大轮次）"

# ---------- 入口 ----------
if __name__ == "__main__":
    import sys
    print(run(sys.argv[1]) if len(sys.argv) > 1 else run("你好"))
```

**代码统计**：
- 有效代码行数：~90 行（含注释和空行）
- 外部依赖：仅 `httpx`
- 与 OpenCode 对比：OpenCode 的 Agent 模块（`internal/llm/agent/`）约 2,000+ 行 Go，加上 TUI、LSP、MCP 等总共数万行。

***

## 2.5 SubZeroClaw：C 语言的 380 行标杆验证

> **来源**：https://github.com/genlayerlabs/subzeroclaw（2026-06-22 获取完整源码）
> 
> **项目定位**：「An agent small enough to run anywhere. A minimal agentic runtime in C — ~380 lines, 54KB binary, ~2MB RAM.」

SubZeroClaw 是「nanobot 思想」在真实世界中的工业级实现。它用 C 语言写了一個完整的 ReAct Agent，源码仅 380 行，编译后 54KB，运行时占用 ~2MB RAM。这不是玩具代码——它支持 tool calling、上下文压缩、session 日志、skill 系统，且可以在树莓派上编译运行。

### 2.5.1 核心架构（从源码提炼）

SubZeroClaw 的源码结构极其清晰：

```
subzeroclaw.c (~380 lines)
├── config_load()          # 读取 ~/.subzeroclaw/config + 环境变量
├── agent_build_system_prompt()  # 读取 skills/*.md 拼入 system prompt
├── http_post()            # 通过 popen("curl ...") 发送 HTTP 请求
├── tool_execute()         # 唯一的工具：shell —— popen("/bin/sh -c ...")
├── parse_response()       # 解析 OpenAI 格式的 JSON 响应
├── compact_messages()     # 上下文压缩：超限时让 LLM 摘要历史消息
├── process_tool_calls()   # 执行 tool_calls 并追加结果到消息历史
└── agent_run()            # 核心 ReAct 循环（for turn=1..max_turns）
```

**关键代码片段（agent_run 循环）**：

```c
for (int turn = 1; turn <= cfg->max_turns; turn++) {
    compact_messages(cfg, msgs, log);  // 上下文超限则压缩
    char *rb = llm_chat(cfg, msgs, tools);  // 调用 LLM
    Response resp;
    parse_response(rb, &resp);
    cJSON_AddItemToArray(msgs, resp.msg);  // 追加 assistant 消息

    if (!strcmp(resp.finish_reason, "stop")) {
        printf("%s\n", resp.text); return 0;  // 任务完成
    }
    if (!strcmp(resp.finish_reason, "tool_calls") && resp.tool_calls) {
        process_tool_calls(resp.tool_calls, msgs, log);  // 执行工具
        continue;  // 继续下一轮
    }
}
```

这与我们前面提炼的 Python 版 ReAct 循环完全同构：

| SubZeroClaw (C) | nanobot (Python) | OpenCode (Go) |
|-----------------|-----------------|---------------|
| `for (turn=1; turn<=max_turns; turn++)` | `for _ in range(MAX_ROUNDS)` | `for {}` |
| `compact_messages()` | （尚未实现） | `Summarize()` |
| `llm_chat() → http_post()` | `_chat() → httpx.post()` | `provider.StreamResponse()` |
| `finish_reason == "tool_calls"` | `reason == "tool_calls"` | `FinishReasonToolUse` |
| `process_tool_calls()` | `_execute_tool() + msgs.append()` | `tool.Run()` |
| `continue` | `continue` | `continue` |

### 2.5.2 极简主义的设计选择

SubZeroClaw 在多个维度上做了激进的减法，这些选择对我们的 nanobot 设计有直接参考价值：

#### 选择 1：只有一个工具 —— shell

```c
static const char TOOLS_JSON[] =
    "[{\"type\":\"function\",\"function\":{\"name\":\"shell\","
    "\"description\":\"Run a shell command\","
    "\"parameters\":{\"type\":\"object\","
    "\"properties\":{\"command\":{\"type\":\"string\"}},\"required\":[\"command\"]}}}]");
```

> 「The adapter is the shell. Since the LLM has a shell, it has git, curl, ffmpeg, jq — whatever you install. For file operations, the model uses cat, tee, sed, etc. No adapters, no integrations.」

**启示**：我们的 nanobot 也不需要为「读文件」「写文件」「执行 bash」分别定义工具。一个 `shell` 工具就够了，让 LLM 自己决定用 `cat`、`tee` 还是 `sed`。

#### 选择 2：Skill = 纯文本 markdown

```c
char *agent_build_system_prompt(const char *skills_dir) {
    // 读取 skills/*.md，直接拼到 system prompt 后面
    // 没有格式规范、没有 schema、没有注册表
}
```

> 「No format spec. No skill registry. No trigger matching. Just plain text the LLM reads.」

**启示**：我们 workflow 中的「AI 摘要生成任务」本身就是一个 skill，可以直接作为 system prompt 的一部分，不需要额外的 skill 框架。

#### 选择 3：通过 curl 子进程做 HTTP

```c
static char *http_post(const char *url, const char *api_key, const char *body) {
    // 写入临时文件 → popen("curl -s -m 120 ...") → 读取 stdout
}
```

SubZeroClaw 没有链接 libcurl，也没有用任何 HTTP 库。它通过 `popen("curl ...")` 发起请求。**这和我们用 `httpx.post()` 是同一思想**：不要引入重量级依赖，用最简单的方式完成 HTTP 调用。

#### 选择 4：上下文压缩 = 让 LLM 自己摘要

```c
static int compact_messages(const Config *cfg, cJSON *msgs, FILE *log) {
    if (total <= cfg->max_messages) return 0;
    // 1. 把历史消息拼成文本
    // 2. 发送给 LLM："Summarize this conversation..."
    // 3. 用摘要替换旧消息
}
```

当消息数超过 `max_messages`（默认 40）时，SubZeroClaw 不是简单地截断，而是**把历史消息发给 LLM 做摘要**，然后用「摘要 + 最近 N 条原始消息」替换完整历史。

**启示**：这比简单的截断更智能，且实现成本极低（一次额外的 LLM 调用）。

#### 选择 5：安全设计 —— 读取后立即擦除 API Key

```c
// 从环境变量读取后，原地覆盖为 \0，然后 unsetenv
char *p = getenv(secret_vars[i]);
if (p) memset(p, 0, strlen(p));
unsetenv(secret_vars[i]);
```

SubZeroClaw 明确意识到：由于工具是 shell，LLM 可以通过 `echo $API_KEY` 或 `env` 读取环境变量。因此它在启动后立即从进程中擦除密钥。

**启示**：我们的 nanobot 虽然只在 workflow 中运行（不暴露交互式 shell），但如果未来扩展为通用 Agent，这个安全模式值得借鉴。

### 2.5.3 与「重型」框架的对比

| 维度 | SubZeroClaw | OpenClaw | ZeroClaw |
|------|------------|----------|----------|
| **语言** | C | TypeScript | Rust |
| **代码量** | ~380 行 | ~430,000 行 | ~15,000 行 |
| **二进制** | 54 KB | 80+ MB | 3.4 MB |
| **运行时内存** | ~2 MB | 80-120 MB | < 5 MB |
| **编译时间（Pi）** | 0.5s | OOM / 极慢 | 较慢 |
| **依赖** | curl, cJSON | ~800 npm 包 | ~100 crates |
| **工具** | 1 个（shell） | 数十个（适配器层） | 多个 |
| **架构哲学** | anti-framework | platform | framework |

SubZeroClaw 的 README 直接点明了这种差异的本质：

> 「OpenClaw solved the agentic loop with 430,000 lines of TypeScript. ZeroClaw re-solved it with 15,000 lines of Rust. Both are good — but both carry the weight of problems that only exist at platform scale: multi-tenancy, channel routing, identity portability, plugin registries. SubZeroClaw asks: what if the problem is just 'one agent, one skill, one device'? Then the answer is ~380 readable lines of C.」

### 2.5.4 对 deploy-git-isolated 的启示

SubZeroClaw 验证了我们的核心假设：

1. **Agent 循环确实可以用几十行代码实现** —— 不是理论，而是已在生产环境运行的 C 程序
2. **单工具 shell 足够应付绝大多数任务** —— 文件操作、命令执行、HTTP 请求都可以用 shell 完成
3. **Skill 不需要框架** —— 纯文本 markdown 直接拼入 system prompt 即可
4. **上下文压缩是必选项** —— 但实现方式可以极其简单（让 LLM 自己摘要）
5. **HTTP 调用不需要重量级库** —— `curl` 子进程或 `httpx` 都可以

**直接可借鉴的代码模式**：

```python
# nanobot 借鉴 SubZeroClaw 的上下文压缩
import httpx

def compact_messages(messages, max_messages=40):
    if len(messages) <= max_messages:
        return messages
    # 让 LLM 摘要前半部分
    summary_prompt = "Summarize this conversation. Keep all facts, file paths, commands, and decisions.\n\n" + format_history(messages[:-10])
    summary = httpx.post(..., json={"messages": [{"role": "user", "content": summary_prompt}]}).json()["choices"][0]["message"]["content"]
    return [
        messages[0],  # system prompt
        {"role": "user", "content": "[Summary of previous context]"},
        {"role": "assistant", "content": summary},
        *messages[-10:],  # 保留最近 10 条原始消息
    ]
```

***

## 3. 两种路线的全维度对比

| 维度 | 自研极简 Agent（nanobot） | 进程级集成外部 CLI（Pi/OpenCode） |
|------|-------------------------|--------------------------------|
| **代码量** | ~100 行 Python | 0 行（但依赖 40MB+ 可执行文件） |
| **外部依赖** | `httpx`（pip install） | 可执行文件 + 可能的运行时依赖 |
| **环境要求** | 任何有 Python + pip 的环境 | 需要特定平台的可执行文件（pi.exe 是 Windows 的） |
| **可控性** | **完全白盒**，每行代码都可见 | **黑盒**，内部逻辑不可见 |
| **可定制性** | 极高，随时修改工具、prompt、循环逻辑 | 受 CLI 参数限制，无法修改内部行为 |
| **功能完整性** | 需自行实现（工具、错误处理、上下文管理） | 开箱即用（文件编辑、bash、git 等） |
| **维护负担** | 自己维护核心逻辑 | 外部项目维护（但版本更新可能破坏兼容性） |
| **跨平台** | **完美**（纯 Python） | 受可执行文件平台限制（pi.exe 只能在 Windows 跑） |
| **性能** | 无进程启动开销，HTTP 直连 | 进程启动开销（~100-500ms），内部可能有多层封装 |
| **调试难度** | 极低（直接 print/debugger） | 中等（需查看子进程 stdout/stderr） |
| **学习曲线** | 需要理解 ReAct 原理和 OpenAI API | 只需要学会 CLI 参数 |
| **风险** | 自己写的代码可能有 bug | 外部工具可能有未文档化的行为变更 |

***

## 4. 针对 deploy-git-isolated 的专门分析

### 4.1 我们的真实需求是什么？

回顾场景：在 Step 5 (commit) 后，让 AI 阅读 `git diff`，生成中文语义摘要。

**需求拆解**：
1. 读取一段文本（git diff）— 不需要工具
2. 调用 LLM 生成摘要 — 只需要一次 `chat.completions`
3. 返回文本结果 — 直接解析 JSON

**结论**：这个场景甚至不需要完整的 ReAct 循环！只需要「单次 LLM 调用」即可。

### 4.2 三种实现方案对比

| 方案 | 实现方式 | 代码量 | 评价 |
|------|---------|--------|------|
| **方案 A：自研 nanobot（单次调用）** | `httpx.post() → 解析 JSON → 返回 content` | ~15 行 | 最轻量、最可控、零黑盒 |
| **方案 B：自研 nanobot（ReAct 循环）** | 上面的 ~100 行完整 Agent | ~100 行 | 为将来扩展预留能力（如自动修复 lint） |
| **方案 C：进程级集成 Pi** | `subprocess.run(["pi.exe", "-p", ...])` | ~20 行 Python + 40MB 二进制 | 重、黑盒、跨平台差，但功能现成 |

### 4.3 关键决策点

**问题 1：将来是否需要 Agent 执行工具（如自动修复 lint、自动跑测试）？**
- **如果不需要** → 方案 A 足够，15 行代码搞定
- **如果需要** → 方案 B 更合适，100 行代码预留完整 ReAct 能力

**问题 2：是否需要支持非 Python 环境调用？**
- 自研 nanobot = 纯 Python，只能在 Python 环境中使用
- 但我们的 workflow 本身就是 Python，所以这不是问题

**问题 3：对 LLM 供应商的锁定？**
- 自研 nanobot 使用标准 OpenAI API 格式，切换供应商只需要改 `BASE_URL` 和 `API_KEY`
- Pi/OpenCode 也支持多供应商，但切换方式受限于它们的 CLI 参数设计

***

## 5. 推荐方案：自研 nanobot（渐进式路线）

### 5.1 为什么推荐自研

1. **场景匹配度高**：我们的需求（读 diff → 生成摘要）极其简单，不需要 40MB 的 CLI 工具
2. **完全可控**：白盒代码，每行都清楚在做什么，调试和排障成本极低
3. **零额外依赖**：项目中已有 `httpx`（或 `requests`），不需要安装/维护额外的可执行文件
4. **跨平台**：纯 Python，Windows/macOS/Linux 完全一致
5. **渐进扩展**：今天只做单次调用，明天需要工具调用时，只需在 100 行代码基础上加工具

### 5.2 具体落地建议

**第一步：实现 `nanobot.py`（单次调用版）**

放在 `references/tasks/deploy-git-isolated/scripts/py-tools/` 下：

```python
def generate_summary(diff_text: str, commit_msg: str, model: str = "kimi-k2.5") -> str:
    api_key = os.environ["MOONSHOT_API_KEY"]
    prompt = f"""你是一位资深代码审查员...\n\nCommit: {commit_msg}\n\nDiff:\n```diff\n{diff_text[:8000]}\n```"""
    
    r = httpx.post(
        "https://api.moonshot.cn/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是代码审查员..."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
```

**第二步：集成到 workflow**

```python
# Step 5 后
try:
    from py_tools.nanobot import generate_summary
    ai_summary = generate_summary(diff_text, commit_msg)
except Exception:
    ai_summary = "（AI 摘要生成失败）"

meta["ai_summary"] = ai_summary
```

**第三步：若未来需要完整 Agent 能力**

将 `nanobot.py` 扩展为完整 ReAct 循环（参考上面的 ~100 行实现），增加 `read_file`、`bash` 等工具。

### 5.3 与 Pi/OpenCode 的关系

**不是替代，而是分层**：
- **自研 nanobot** = workflow 内部的标准化能力（生成摘要、轻量分析）
- **Pi/OpenCode** = 保留作为「重型任务」的备选（如完整的代码重构、多文件编辑）

当需要 Agent 执行复杂工具链（文件编辑、git 操作、测试运行）时，再调用外部 CLI；当只需要「读输入 → 生成文本输出」时，用自研 nanobot。

***

## 6. 潜在风险与缓解

| 风险 | 缓解 |
|------|------|
| 自己写的 HTTP 调用可能有 bug（重试、超时、流式） | `httpx` 已内置重试和超时；初期可用同步调用，复杂场景再升级 |
| 需要处理不同 LLM 供应商的 API 差异 | 坚持使用 OpenAI 兼容格式（Moonshot、OpenAI、Anthropic 都支持） |
| 没有现成的工具集（文件编辑、bash） | 当前场景不需要工具；未来需要时，工具实现只需几十行 |
| 上下文窗口管理（diff 过长） | 截断 diff（保留前 8000 字符）+ 优先传递文件名和 commit message |
| 缺乏 OpenCode/Pi 的「自动记忆」「会话管理」 | workflow 场景是单次调用，不需要会话管理 |

***

## 7. 结论

**nanobot 思想的核心价值**：Agent 不应该是沉重的黑盒 CLI，而应该是轻量、透明、可嵌入任何 workflow 的纯代码模块。

对于 deploy-git-isolated 的「AI 语义摘要」场景：
- **最优解 = 自研 ~15-100 行 Python**，直接调用 Moonshot API
- 不需要 40MB 的 pi.exe
- 不需要理解 OpenCode 的 Go 源码
- 不需要处理 subprocess 的编码、超时、权限问题

**行动建议**：
1. 立即实现 `nanobot.py`（单次调用版，~30 行）
2. 在 workflow 中集成，跑通第一个 commit 的 AI 摘要
3. 根据实际效果决定是否需要扩展到完整 ReAct 循环

***

## 附录：nanobot 与 OpenCode/Pi 的架构映射

```
OpenCode (Go, 2000+ 行 Agent 模块)
    ├── processGeneration()          → nanobot: run()
    ├── streamAndHandleEvents()      → nanobot: _chat()
    ├── processEvent()               → nanobot: 内联在 _chat() 的响应解析
    ├── tool.Run()                   → nanobot: _execute_tool()
    ├── AutoApproveSession()         → nanobot: 不需要（没有 TUI/权限对话框）
    ├── Session/Message Service      → nanobot: 不需要（单次调用，无状态）
    └── TUI/Bubble Tea               → nanobot: 不需要

Pi (Rust, 40MB 闭源)
    ├── -p "prompt"                  → nanobot: run(prompt)
    ├── --no-tools                   → nanobot: 默认无工具（_registry 为空）
    ├── --thinking off               → nanobot: temperature=0.3（或不传 reasoning_effort）
    └── --mode json                  → nanobot: 直接返回 Python dict/string
```
