---
name: metainflow-enterprise-query
description: "Use when user needs enterprise data lookup with routing between exact lookup and fuzzy search, including 工商信息/资质证书/专利查询/年报信息/税号开票, 企业模糊搜索, 企业全称查询, 统一社会信用代码查询, registration lookup, enterprise balance diagnostics."
---

# Enterprise Query Routing

通过 `metainflow-studio-cli` 的企业查询命令，按输入内容自动决定走精确查询还是模糊搜索。

## Quick Reference

| 场景 | 命令 |
|---|---|
| 精确查询企业详情 | `metainflow enterprise-query --type business --keyword "企业全称"` |
| 模糊搜索企业候选 | `metainflow enterprise-search --keyword "简称或片段"` |
| 查询余额 | `metainflow enterprise-balance --output json` |

## Routing Policy

- 输入是统一社会信用代码或注册号：直接走 `enterprise-query`
- 输入明显像企业全称：先走 `enterprise-query`
- 输入像简称、片段、别名：先走 `enterprise-search`
- 企业全称精确查询无结果：回退 `enterprise-search`
- 模糊搜索多候选：先展示候选，不自动继续详情查询
- 模糊搜索单候选：用候选的 `credit_no` 或 `name` 再走详情查询

## Full-name Heuristic

只有明显像完整企业名时才视为“全称”，例如以这些后缀结尾：

- `有限公司`
- `有限责任公司`
- `股份有限公司`
- `集团有限公司`
- `合伙企业`
- `事务所`
- `研究院`

如果不满足上面条件，默认按模糊搜索处理。

## Cache And Refresh

- 只有传入 `session_id` 时，才启用缓存
- 相同 `session_id` + 相同参数时复用缓存
- `enterprise-search` 和 `enterprise-query` 分开缓存，不能互相替代
- 当用户明确说 `重新查 / 最新 / 别用缓存 / 刷新` 时，加 `--refresh`

推荐把宿主 agent 的 thread/session 标识映射到：

- `--session-id "<thread-or-session-id>"`

## Candidate Display

模糊搜索返回多家企业时，只展示精简字段：

- `name`
- `oper_name`
- `credit_no`
- `start_date`

## Common Mistakes

| 错误 | 正确做法 |
|---|---|
| 已知统一社会信用代码还先走模糊搜索 | 直接用 `enterprise-query` |
| 输入企业简称后直接查详情接口 | 先用 `enterprise-search` |
| 模糊搜索多候选时自动默认第一条 | 先让用户确认目标企业 |
| 用户要求最新结果但仍复用缓存 | 使用 `--refresh` |
