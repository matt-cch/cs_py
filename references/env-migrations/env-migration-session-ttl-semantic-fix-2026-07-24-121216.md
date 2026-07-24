---
title: env-migration — Session TTL 语义修正与续期验证标准建设
description: 修正 chrome_session TTL 算法，区分「核心登录态有效期」与「保守最短有效期」，确保续期前后对比基于同一语义维度。
date: 2026-07-24
meta:
  version: "1.0.0"
---

# env-migration-session-ttl-semantic-fix-2026-07-24-121216

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Session TTL 语义修正与续期验证标准建设 |
| **日期** | 2026-07-24 |
| **文件名时间戳** | `2026-07-24-121216` |
| **触发原因** | 续期前后 TTL 对比发现异常：核心登录态 sessionid（30 天）被非核心追踪 cookie tt_scid（7 天）拉低，导致结论失真 |
| **影响范围** | 2 个脚本：`py-plugins/chrome_session.py`、`py-tools/atomic-check-chrome-session.py` |
| **风险等级** | **中** — 影响 session 状态结论判断，可能导致用户误判续期时机 |


## 一、问题背景：同一个语义维度的陷阱

### 1.1 现象

续期前（2026-07-24 09:52）：
- `download-article.py` Preflight 输出：`Session 有效期 3.1 天`
- 用户经验判断：这是核心登录态（sessionid）即将过期，需要续期

续期后（首次修正前）：
- `atomic-check-chrome-session.py` 输出：`Session 有效，有效期 7.0 天`
- 用户质疑：续期前是 3.1 天，续期后怎么才 7 天？上个月新登录时明明很长

### 1.2 根因分析

查看 manifest 发现：

| Cookie | 域名 | 续期前 | 续期后 |
|--------|------|--------|--------|
| `sessionid` / `sessionid_ss` | .toutiao.com | ~3.1 天 | **60 天** |
| `passport_auth_status` / `_ss` | .toutiao.com | ~3.1 天 | **30 天** |
| `tt_scid` | xxbg.snssdk.com | ~3.1 天 | **7.0 天** |

**问题**：`analyze_ttl()` 的 `conservative_ttl` 取的是**全部 key cookie 中的最短值**（含 `tt_scid`）。

`tt_scid` 是非核心追踪/统计 cookie，服务端给它下发短效期（7 天），但它**不影响登录态有效性**。真正的核心登录态（`sessionid`, `passport_auth_status`）续期后已恢复到 30~60 天。

### 1.3 核心矛盾

**续期验证必须基于同一个语义维度**：
- 续期前：3.1 天（用户感知的是核心登录态衰减）
- 续期后：如果拿 `tt_scid` 的 7 天来比 → **不同维度，无意义**
- 续期后：如果拿 `sessionid` 的 60 天或 `passport_auth_status` 的 30 天来比 → **同一维度，证明续期成功**


## 二、代码改造

### 2.1 chrome_session.py

| 变更 | 说明 |
|------|------|
| 新增 `core_session_ttl` | 仅统计 `sessionid`, `sessionid_ss`, `passport_auth_status`, `passport_auth_status_ss` 的最短有效期 |
| 保留 `conservative_ttl` | 全部 key cookie 最短值，降为「仅供参考」 |
| 结论生成逻辑 | 优先使用 `core_session_ttl`，无则 fallback 到 `conservative_ttl` |

**核心登录态定义**：
```python
core_session_cookies = {
    "sessionid", "sessionid_ss",
    "passport_auth_status", "passport_auth_status_ss",
}
```

### 2.2 atomic-check-chrome-session.py

| 变更 | 说明 |
|------|------|
| `_build_conclusion()` | 优先取 `core_session_ttl`，结论文字明确标注「核心登录态有效期」 |
| 返回码逻辑 | 以 `core_session_ttl` 为准判断 session 是否可用 |


## 三、验证记录

### 3.1 续期前（2026-07-24 09:52）

- 工具：`download-article.py` Preflight
- 输出：`Session 有效期 3.1 天`
- 语义：当时 `conservative_ttl` 即核心登录态（无 `core_session_ttl` 字段，但恰好 `sessionid` 是最短值）

### 3.2 续期操作（2026-07-24 11:02）

- 工具：`atomic-chrome-login-interactive.py`
- 流程：
  1. Chrome 窗口打开，利用现有 Session 自动进入头条
  2. 用户手动退出账号
  3. 用户重新扫码登录
  4. 导航到 `example.com` 结束会话

### 3.3 续期后验证（2026-07-24 12:03）

- 工具：`atomic-check-chrome-session.py`
- 核心登录态 TTL：
  - `passport_auth_status` = **30.0 天**（`core_session_ttl` 取最小值）
  - `sessionid` = 60.0 天
- 保守 TTL：`tt_scid` @ snssdk.com = 7.0 天（仅供参考）
- 结论：`Session 有效，核心登录态有效期 30.0 天`

### 3.4 同一维度对比

| 指标 | 续期前 | 续期后 | 变化 |
|------|--------|--------|------|
| **核心登录态 TTL** | ~3.1 天 | **30.0 天** | ✅ 恢复至初始有效期 |
| 保守 TTL（含 tt_scid） | ~3.1 天 | 7.0 天 | ⚠️ 非核心，不参与续期判断 |

**结论**：续期成功，核心登录态从 3.1 天恢复到 30 天。


## 四、标准建立

### 4.1 Session 状态判断铁律

1. **续期前后对比必须基于同一语义维度** — 核心登录态（sessionid / passport_auth_status）
2. **非核心追踪 cookie 不参与状态结论** — `tt_scid`, `_ga` 等仅供参考
3. ** conservative_ttl 不再作为状态结论唯一依据** — 仅作辅助参考

### 4.2 结论分级标准（以 core_session_ttl 为准）

| 核心登录态剩余天数 | 结论 | 行动建议 |
|------------------|------|---------|
| ≤ 1 天 | 即将过期 | 立即重新登录 |
| ≤ 7 天 | 有效期紧张 | 本周内续期 |
| ≤ 30 天 | 正常 | 续期窗口：{expires} |
| > 30 天 | 长期有效 | 无需近期关注 |


## 五、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 结果 |
|---------|---------|---------|------|
| `.py`（chrome_session.py） | `run-lint.py` lint_python | Python 语法 | ✅ 通过 |
| `.py`（atomic-check-chrome-session.py） | `run-lint.py` lint_python | Python 语法 | ✅ 通过 |
| `.py`（atomic-chrome-login-interactive.py） | `run-lint.py` lint_python | Python 语法 | ✅ 通过 |


## 六、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认核心 TTL 正确计算 | 执行 `atomic-check-chrome-session.py` | manifest 中包含 `core_session_ttl` 字段 |
| 2 | 确认结论基于核心 TTL | 查看 stdout 输出 | 出现「核心登录态有效期 X 天」字样 |
| 3 | 确认保守 TTL 仅作参考 | 查看 manifest | `conservative_ttl.note` 标注「仅供参考」 |
| 4 | 续期验证 | 执行 `atomic-chrome-login-interactive.py` → 重新登录 → 再检测 | 核心 TTL 恢复到 30 天左右 |


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 chrome_session.py | `git checkout <变更前 commit> -- references/tasks/deploy-git-isolated/scripts/py-plugins/chrome_session.py` |
| 恢复 atomic-check-chrome-session.py | `git checkout <变更前 commit> -- references/tasks/deploy-git-isolated/scripts/py-tools/atomic-check-chrome-session.py` |
| 验证回滚 | `run-lint.py` 验证语法 |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-24-121216 |
| **更新人** | Human + Agent Session |
| **变更触发** | Session TTL 语义修正：核心登录态与非核心追踪 cookie 分离 |
| **下次修订条件** | 核心登录态 cookie 定义扩展（如新增 auth 标志）；服务端下发策略变化 |
| **跨环境迁移参考** | 直接替换 chrome_session.py + atomic-check-chrome-session.py + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-24*  
*模板版本：v2*
