# metainflow-studio-cli 使用文档

## 一句话说明

`metainflow-studio-cli` 当前主功能是：

- `parse-doc`：解析文档（本地或 URL），输出文本或 JSON
- `web-crawl`：抓取指定 URL 的网页内容，并按需总结/提取

支持格式：`.pdf .doc .docx .pptx .xls .xlsx .csv .txt .md .html`

## 0) 环境变量配置

复制模版并填入实际值：

```bash
cp .env.example .env
```

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PROVIDER_BASE_URL` | `https://api.openai.com/v1` | OpenAI 兼容接口地址 |
| `PROVIDER_API_KEY` | _(必填)_ | API 密钥 |
| `PROVIDER_TIMEOUT_SECONDS` | `60` | 单次请求超时秒数 |
| `PROVIDER_MAX_RETRIES` | `2` | 失败后最大重试次数 |
| `PROVIDER_MODEL_DOC_PARSE` | `gpt-4.1-mini` | `parse-doc` 使用的模型 |
| `PROVIDER_MODEL_WEB_FETCH` | `gpt-4.1-mini` | `web-crawl` 使用的模型 |
| `METAINFLOW_WEB_FETCH_VERIFY_SSL` | `1` | `web-crawl` 是否校验 SSL |
| `METAINFLOW_RUN_SAMPLE_MATRIX` | _(未设置)_ | 设为 `1` 启用真实样本矩阵集成测试 |

## 1) 安装

在项目根目录执行：

```bash
python -m pip install -e '.[dev]'
```

验证命令是否可用：

```bash
which metainflow
```

## 1.1) 本地更新 CLI

当本地代码有更新时，重新安装一次即可：

```bash
python -m pip install -e '.[dev]'
hash -r
```

## 1.2) 本地更新后验证

推荐按这个顺序验证：

```bash
metainflow --help
metainflow parse-doc --help
metainflow web-crawl --help
pytest -q
```

## 2) 最常用命令

### 解析本地文件

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx
```

### 输出 JSON

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
```

### 抓取指定 URL

```bash
metainflow web-crawl --url "https://example.com/page.html"
```

### 抓取并输出 JSON

```bash
metainflow web-crawl --url "https://example.com/page.html" --instruction "提取主要观点" --output json
```

如果 `metainflow` 命令不可用，可临时用：

```bash
python -m metainflow_studio_cli.main parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
python -m metainflow_studio_cli.main web-crawl --url https://example.com/page.html --output json
```

## 3) JSON 输出结构

`parse-doc --output json` 统一返回：

```json
{
  "success": true,
  "data": {
    "markdown": "...",
    "blocks": [],
    "tables": [],
    "source": {
      "input": "...",
      "resolved_path": "...",
      "file_type": ".docx"
    }
  },
  "meta": {
    "parser": "local",
    "latency_ms": 1,
    "request_id": ""
  },
  "error": null
}
```

`web-crawl --output json` 统一返回：

```json
{
  "success": true,
  "data": {
    "markdown": "...",
    "extracted": "...",
    "url": "https://example.com/page.html",
    "title": "...",
    "instruction": "提取主要观点",
    "links": []
  },
  "meta": {
    "fetch_provider": "crawl4ai",
    "summary_provider": "llm",
    "model": "...",
    "latency_ms": 0,
    "request_id": "..."
  },
  "error": null
}
```

## 4) Ubuntu 必装依赖

为保证 `.doc` 转换和 PDF OCR 可用：

```bash
sudo apt-get update
sudo apt-get install -y libreoffice tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng poppler-utils fonts-noto-cjk
```

## 5) 测试命令

```bash
pytest -q
```

Attribution: This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.
