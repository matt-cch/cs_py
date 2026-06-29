---
title: env-migration — download-article.py 增加 Preflight 检查与头条 URL 验证
description: 记录 article_extractor / download-article 工具链的 preflight 增强、bug 修复及头条/非头条 URL 双路验证结果。
date: 2026-06-25
meta: {}
---

# env-migration — download-article.py 增加 Preflight 检查与头条 URL 验证

> **Session 主题**：download-article 工具链 preflight 增强与双路验证
> **文件名时间戳**：`2026-06-25-172700`
> **触发原因**：
> 1. 头条 URL 提取失败（Chrome Profile 被占用时抛出 `TargetClosedError exitCode=21`，错误信息不友好）
> 2. download-article.py 存在 `UnboundLocalError`（`extract_article` 变量重复赋值导致作用域冲突）
> 3. article_extractor.py 在独立调用时无法探测 devroot（缺少向上探测逻辑）
> **影响范围**：`py-tools/download-article.py`、`py-plugins/article_extractor.py`
> **风险等级**：低


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/download-article.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-article.py` |
| **变更类型** | `修改` |
| **修改内容** | ① 新增 `_preflight()` 函数：Chrome 路径验证 → Profile 占用检测 → 头条 Session 检测（调用 chrome_session 插件）；② 新增 `_is_chrome_profile_locked()`：通过 `tasklist` + lockfile 检测 Profile 是否被占用；③ 修复 `UnboundLocalError`：`extract_article_func` 替代重复赋值的 `extract_article`；④ 新增 `--skip-preflight` 参数（调试用） |
| **作用** | 提取前明确告知用户环境状态（Chrome 是否存在、Profile 是否被占、头条 Session 是否有效），避免底层 `TargetClosedError` 暴露给用户 |
| **验证方式** | `run-lint.py` 通过；MDN URL 提取成功；头条 URL 提取成功 |
| **迁移方式** | 直接覆盖 |

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/article_extractor.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/article_extractor.py` |
| **变更类型** | `修改` |
| **修改内容** | 在 `extract_article()` 函数内新增 devroot 向上探测逻辑（与 `browser_session._get_devroot()` 一致：向上查找包含 `references/runtime/verified-runtime-index.json` 的目录） |
| **作用** | 独立调用 `article_extractor` 时（非 py_lib registry 注入）也能正确找到 Chrome 路径 |
| **验证方式** | `run-lint.py` 通过；MDN/头条 URL 双路提取成功 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作

无。


## 三、环境变量速查

无变更。


## 四、落盘验证

| 文件 | 验证工具 | 验证内容 | 结果 |
|------|---------|---------|------|
| `download-article.py` | `run-lint.py`（`lint_python` + `lint_encoding`） | 语法、编码、BOM、换行符 | ✅ 通过 |
| `article_extractor.py` | `run-lint.py`（`lint_python` + `lint_encoding`） | 语法、编码、BOM、换行符 | ✅ 通过 |


## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 非头条 URL 提取 | `download-article.py --url "https://developer.mozilla.org/en-US/docs/Web/JavaScript" --tags "test,mdn" --headless` | Preflight 通过（Skip Session），输出 `.md` 文件 |
| 2 | 头条 URL 提取 | `download-article.py --url "https://www.toutiao.com/article/7654861221870502406/" --tags "test,toutiao" --headless` | Preflight 通过（8 个 Session 标志 + 6 天 TTL），输出 `.md` 文件 |
| 3 | Profile 占用检测 | 手动启动 Chrome 后执行头条提取 | Preflight 报错「Profile 被占用」，不启动 Playwright |
| 4 | Session 过期检测 | 等待 Session 过期后执行（或修改 key_cookies） | Preflight 报错「Session 未检测到登录态标志」 |


## 六、已知问题与待优化

1. **Profile 占用检测精度有限**：当前通过 `tasklist` + `lockfile` 粗略判断，无法精确定位到具体哪个 PID 占用了哪个 Profile。未来可考虑通过 Windows 句柄查询（如 `handle.exe` 或 WMI）精确定位。
2. **Session 有效期告警阈值硬编码**：紧张（≤7 天）、即将过期（≤1 天）的阈值写死在 `download-article.py` 中，未来可提取到配置。
3. **非头条 URL 未做通用 Session 检测**：当前只有头条域名触发 Session 检测，其他需要登录的站点（如知乎、微信公众号）未覆盖。


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-25-172700 |
| **更新人** | Human + Agent Session |
| **变更触发** | 头条 URL 提取失败 + 错误信息不友好 + 代码 bug |
| **下次修订条件** | 新增其他站点的 Session 检测；Profile 占用检测精度提升 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-25-172700*  
*模板版本：v2*
