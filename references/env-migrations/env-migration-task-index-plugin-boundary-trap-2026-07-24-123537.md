---
title: task-index 插件越界登记陷阱 — 层级边界认知缝隙
description: Agent 在修订联动 verified-task-index.json 时，因混淆命名前缀与层级边界，险些将 py-plugins 底层插件登记到 available_scripts_and_tools 中。本记录固化互斥集合认知，防止后续 Agent 重蹈覆辙。
date: 2026-07-24
meta:
  severity: high
  type: cognitive-boundary
  affected_files:
    - references/runtime/verified-task-index.json
  lesson: py-plugins 永远不进入 available_scripts_and_tools
---

# task-index 插件越界登记陷阱

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 修订联动：Chrome Session 检测/登录/文章下载 CLI 登记到可用工具索引 |
| **日期** | 2026-07-24 |
| **文件名时间戳** | `2026-07-24-123537` |
| **触发原因** | 用户提醒"还有个可用工具登记表 json 没有修订联动" |
| **影响范围** | `verified-task-index.json` 索引准确性、Agent 行为约束、层级边界认知 |
| **风险等级** | **高**（索引污染会导致下游 Agent 误调用不可执行文件） |


## 一、现象还原（完整时间线）

### 1.1 正常任务流

用户完成以下建设后，要求"索引和速查表的修订联动也要一起做"：

- `atomic-check-chrome-session.py`（CLI，Layer 3）
- `atomic-chrome-login-interactive.py`（CLI，Layer 3，新建）
- `download-article.py`（CLI，Layer 3）
- `chrome_session.py`（插件，Layer 1）
- `article_extractor.py`（插件，Layer 1）
- `js_loader.py`（插件，Layer 1）

### 1.2 Agent 第一轮操作（合规）

Agent 修订联动了以下 3 处：

1. **ENTRY.json** — `tools` 数组追加 `atomic-chrome-login-interactive.py`（状态 `ready`）
2. **TASK-TOOLS-INDEX.md** — Python CLI 入口表追加新条目
3. **EXEC-CHEATSHEET.md** — 新增 Stage S6.5.5，修正 Stage S6.6 前置提示

### 1.3 用户指出遗漏

> "你显然还有一个可用工具登记表 json 没有修订联动嘛"

### 1.4 Agent 第二轮操作（首次越界）

Agent 浏览 `verified-task-index.json` 时，看到已有大量 `atomic-*` 条目（如 `atomic-detect-local`、`atomic-query-upstream`、`atomic-route-probe` 等），**认知发生漂移**：

> "既然 atomic-* 都能登记，那 `article_extractor`、`chrome_session`、`js_loader` 也是 atomic 体系的一部分，应该一起登记。"

Agent 在 patch 文件中写下了包含 `article_extractor`、`chrome_session`、`js_loader` 的批量 add 操作，**即将把 py-plugins 底层插件塞入 `available_scripts_and_tools`**。

### 1.5 用户阻断

> "你在干什么？谁允许你登记 plugin 到可用工具表的？"

Agent 被强制叫停，撤回错误 patch，重新只登记 3 个 CLI 入口。


## 二、根因分析（为什么错）

### 2.1 直接根因：命名前缀幻觉

Agent 把 **"atomic" 前缀** 误当成了 **"登记资格"**。看到 `atomic-detect-local` 在索引里，就以为所有 atomic 开头的东西都该进索引。

**事实是**：
- `atomic-detect-local.py` 在 `py-tools/runtime-common/` → **有 CLI 入口** → 可以登记
- `chrome_session.py` 在 `py-plugins/` → **没有 CLI 入口** → **永远禁止登记**

前缀相同，层级完全不同。

### 2.2 深层根因：互斥集合认知未固化

`available_scripts_and_tools` 的收录规则是一个**互斥集合**，不存在"看看内容再决定"的灰色地带：

| 集合 | 判定标准 | 典型路径 | 是否可登记 |
|------|---------|---------|-----------|
| **可登记** | 终端可直接执行（`if __name__ == "__main__"`） | `py-tools/*.py` | ✅ |
| **禁止登记** | 内部插件，由 `py_lib.load_plugins()` 动态加载 | `py-plugins/*.py` | ❌ |

Agent 没有把这个互斥关系内化为**自动排除规则**，而是每次都要"判断一下"，给了幻觉可乘之机。

### 2.3 认知缝隙的具体表现

Agent 在反省时说：

> "差点把 `article_extractor`、`chrome_session`、`js_loader` 这些底层 plugin 也塞进去"

这句话本身就有问题——**"差点"暗示这是一个需要警惕的边缘情况**。实际上它不是"差点"，而是"绝对不可以"。

Agent 后续的反省还留了口子：

> "下次遇到索引补登，先问一句'这个层级该不该进这个表'再动手"

这依然是错的。**不需要问，看到 `py-plugins/` 路径就该自动排除**。问一句反而说明认知没到位。


## 三、正确认知（铁律）

### 3.1 零容忍互斥集合

`available_scripts_and_tools` 与 `py-plugins/` 是**互斥集合**，零交集。

- 路径含 `py-tools/` 且含 `if __name__ == "__main__"` → 可以登记
- 路径含 `py-plugins/` → **永远禁止登记，无需任何思考**

### 3.2 已有 atomic 条目的真实原因

`verified-task-index.json` 中已有的 `atomic-*` 条目（如 `atomic-detect-local`、`atomic-route-probe` 等）**全部位于 `py-tools/` 下**，是标准的 CLI 入口。它们与 `py-plugins/` 下的同名插件体系没有任何登记上的关联。

### 3.3 层级边界 ≠ 命名边界

| 维度 | 说明 |
|------|------|
| **命名边界** | "atomic-*" 前缀，表示原子化拆分的设计哲学 |
| **层级边界** | `py-tools/`（CLI 入口）vs `py-plugins/`（内部插件） |

Agent 必须以**层级边界**为唯一判定依据，命名前缀仅供参考，绝不构成登记资格。


## 四、影响与风险

若 Agent 的错误 patch 被执行：

1. **索引污染**：`verified-task-index.json` 中出现不可执行的条目
2. **下游误用**：后续 Agent 根据索引 "复用脚本" 时，尝试直接执行 `chrome_session.py`，会因为没有 CLI 入口而失败
3. **认知传染**：索引中出现 plugin 条目，会误导其他 Agent 认为 "plugin 也可以登记"，形成恶性循环
4. **真源失真**：索引的 `path_exists` 和 `verified_at` 对 plugin 无意义（plugin 不需要单独验证）


## 五、修复动作

### 5.1 撤回错误 patch

Agent 删除包含 plugin 条目的 `venv/tmp/task-index-patch.json`，重新只写入 3 个 CLI 入口：

- `atomic-check-chrome-session`
- `atomic-chrome-login-interactive`
- `download-article`

### 5.2 正确 patch 执行

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
    --file "${devroot}\references\runtime\verified-task-index.json" `
    --batch "@venv/tmp/task-index-patch.json" `
    --backup
```

执行成功，lint 验证通过 ✅。


## 六、验证清单（防止复发）

| # | 验证步骤 | 操作 | 期望结果 |
|---|---------|------|---------|
| 1 | 确认索引中无 plugin | `grep '"path"' verified-task-index.json \| grep 'py-plugins'` | **零匹配** |
| 2 | 确认所有登记条目可执行 | 抽查登记条目的 `.py` 文件，确认含 `if __name__ == "__main__"` | 全部通过 |
| 3 | 确认层级边界清晰 | 任何新增登记前，强制检查路径是否含 `py-tools/` | 不含则直接拒绝 |


## 七、回滚方案

若错误 patch 已被执行（plugin 已污染索引）：

```powershell
# 从备份恢复
Copy-Item "${devroot}\references\runtime\verified-task-index.json.bak" `
    "${devroot}\references\runtime\verified-task-index.json" -Force

# 重新执行正确 patch（仅 CLI 入口）
# ... 按 5.2 节命令执行
```


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-24-123537 |
| **更新人** | Agent（经用户阻断后修正） |
| **变更触发** | 用户明确指出 plugin 不应登记到 available_scripts_and_tools |
| **下次修订条件** | 若项目层级架构发生变化（如新增 Layer 4/5），需重新评估互斥集合 |
| **跨环境迁移参考** | 直接复制本文档；任何 Agent 触及 `verified-task-index.json` 前必读 |


## 九、核心教训（一句话）

> **`py-plugins/` 永远不进入 `available_scripts_and_tools`。这不是"谨慎"，是"禁止"。不需要思考，不需要询问，看到路径就排除。**
