---
name: metainflow-web-fetch
description: "Use when user needs to crawl or fetch a specific URL to extract/summarize its content. Provides web-crawl command for fetching known URLs. 触发词：网页抓取, 抓取网页, 提取网页内容, web crawl, 爬取, fetch url, 总结网页, 抓取 URL, 读取网页"
---

# Web Fetch

通过 `metainflow web-crawl` 抓取指定网页内容，由 AI 自动总结/提取。默认抓取引擎为 Crawl4AI。

## Quick Reference

| 参数 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `--url` | 网页 URL | 是 | - |
| `--instruction` | AI 处理指令 | 否 | 总结主要信息 |
| `--output, -o` | 输出格式: text/json | 否 | text |

## 命令选择决策树

```
用户想获取互联网信息
├─ 有具体 URL → metainflow web-crawl
└─ 无具体 URL，需搜索 → 当前分支未提供搜索命令，先通过其他方式拿到目标 URL，再用 web-crawl
```

## 使用示例

```bash
# 抓取指定 URL 并提取信息
metainflow web-crawl --url https://example.com/pricing --instruction "提取所有套餐的价格和功能对比"
```

## --instruction 编写指南

| 场景 | instruction 示例 |
|------|-----------------|
| 提取结构化数据 | `"提取所有产品名称、价格、规格，以表格形式输出"` |
| 按条件筛选 | `"只保留 2024 年之后发布的内容"` |
| 对比分析 | `"对比各方案的优缺点，给出推荐"` |
| 翻译总结 | `"用中文总结主要观点"` |
| 不指定（默认） | AI 自动总结主要信息 |

## Common Mistakes

| 错误 | 正确做法 |
|------|----------|
| 无具体 URL 时用 `metainflow web-crawl` | 先通过其他方式拿到具体 URL，再用 `metainflow web-crawl` |
| `--instruction` 过于笼统（如"总结一下"） | 明确指定提取目标、输出格式、筛选条件 |
| 需要后续程序处理结果但未加 `--output json` | 需要解析结果时始终加 `--output json` |
| 命令失败后不检查退出码 | 退出码 `1/2/3` 表示不同失败类型，检查参数和网络后重试 |
