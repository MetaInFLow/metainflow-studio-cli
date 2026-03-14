---
name: metainflow-doc-parse
description: "Use when user needs to parse, extract, or read content from documents (PDF, Word, Excel, PPT, CSV, text, HTML) with metainflow-studio-cli. 触发词：文档解析, 解析文档, 解析 PDF, 解析 Word, 解析 Excel, 读取文档, 提取文档内容, parse document, doc parse, 文档转 Markdown, 提取表格"
---

# Document Parse

通过 `metainflow-studio-cli` 的 `parse-doc` 命令解析文档内容，支持本地文件和 URL 输入。

## Quick Reference

| 参数 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `--file` | 文档路径或 URL | 是 | - |
| `--output` | 输出格式: text/json | 否 | text |

## 支持的文档格式

| 格式 | 扩展名 | 典型场景 |
|------|--------|---------|
| PDF | `.pdf` | 报告、论文、合同 |
| Word | `.doc`, `.docx` | 文档、方案 |
| PowerPoint | `.pptx` | 演示文稿 |
| Excel | `.xls`, `.xlsx` | 表格数据 |
| CSV | `.csv` | 结构化数据 |
| 纯文本 | `.txt`, `.md` | 文本文件 |
| 网页 | `.html` | HTML 页面 |

## 使用示例

```bash
# 解析本地文档
metainflow parse-doc --file report.pdf

# 解析旧版 Excel（需要 LibreOffice / soffice）
metainflow parse-doc --file legacy.xls --output json

# 解析 URL 并输出 JSON
metainflow parse-doc --file https://example.com/document.docx --output json

# 未安装 console script 时，可用 Python 模式
python -m metainflow_studio_cli.main parse-doc --file data.xlsx --output json
```

## 使用场景决策

```
需要获取文档内容
├─ 文档是本地文件或可下载 URL → metainflow parse-doc
├─ 文档是网页正文抓取任务 → 未来可接 metainflow web-crawl（待实现）
└─ 需要结构化结果供程序处理 → 使用 --output json
```

## 表格输出说明

- `.xls` 先通过 `LibreOffice soffice` 转成 `.xlsx`，再复用现有 Excel 解析链路
- `--output json` 的 `tables` 字段会返回规则二维数组，适合脚本和 agent 消费
- 对 merged cells，输出会按可读性优先展开：用左上角单元格值填充整个合并区域
- Markdown 表格和 `tables` 的内容保持一致

## Common Mistakes

| 错误 | 正确做法 |
|------|----------|
| 文件路径包含空格未加引号 | 路径有空格时用引号：`--file "my file.pdf"` |
| 需要程序处理结果但未加 `--output json` | 需要机器可读结果时始终加 `--output json` |
| `.doc` / `.xls` 解析失败 | 在 Ubuntu 安装 LibreOffice，确保 `soffice` 可用 |
| 扫描 PDF 输出为空 | 安装 `tesseract-ocr` 和 `poppler-utils` 后重试 |
