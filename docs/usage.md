# metainflow-studio-cli 使用文档

## 一句话说明

`metainflow-studio-cli` 当前主功能是：

- `parse-doc`：解析文档（本地或 URL），输出文本或 JSON
- `search-summary`：按关键词搜索互联网信息，并输出 AI 总结

支持格式：`.pdf .doc .docx .pptx .xls .xlsx .csv .txt .md .html`

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

说明：
- `-e` 是 editable 安装，源码改动会直接指向当前目录
- 如果改了入口、依赖或脚本定义，重新执行一次最稳妥
- `hash -r` 用于刷新 shell 对命令路径的缓存

## 1.2) 本地更新后验证

推荐按这个顺序验证：

### 验证命令路径

```bash
which metainflow
```

### 验证帮助信息

```bash
metainflow --help
metainflow parse-doc --help
metainflow search-summary --help
```

### 验证真实样本

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
```

### 验证测试

```bash
pytest -q
```

## 2) 最常用命令

### 解析本地文件

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx
```

### 输出 JSON（推荐调试和程序调用）

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
```

### 解析 URL

```bash
metainflow parse-doc --file "https://example.com/page.html" --output json
```

### 搜索互联网信息

```bash
metainflow search-summary --query "React 19 新特性"
```

说明：当前 `search-summary` 由 `metainflow-studio-cli` 自己获取搜索结果，再调用配置模型做总结。

### 搜索并输出 JSON

```bash
metainflow search-summary --query "ByteDance 开源项目" --instruction "按项目类型分类" --output json
```

### 搜索总结的模型配置

`search-summary` 自己完成搜索，模型只负责总结。常用配置方式：

```bash
export PROVIDER_BASE_URL="https://your-openai-compatible-endpoint/v1"
export PROVIDER_API_KEY="your-api-key"
export PROVIDER_MODEL_WEB_SEARCH="your-model-name"
export WEB_SEARCH_PAGE_TIMEOUT_SECONDS="30"
```

然后执行：

```bash
python -m playwright install chromium
metainflow search-summary --query "React 19 新特性" --output json
```

如果 `metainflow` 命令不可用，可临时用：

```bash
python -m metainflow_studio_cli.main parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
python -m metainflow_studio_cli.main search-summary --query "React 19 新特性" --output json
```

## 3) JSON 输出结构

`--output json` 统一返回：

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

`search-summary --output json` 统一返回：

```json
{
  "success": true,
  "data": {
    "summary": "...",
    "query": "React 19 新特性",
    "instruction": "按功能分类整理",
    "results": []
  },
  "meta": {
    "search_provider": "baidu-playwright",
    "summary_provider": "llm",
    "model": "...",
    "latency_ms": 0,
    "request_id": "..."
  },
  "error": null
}
```

## 4) Ubuntu 必装依赖

为保证 `.doc` / `.xls` 转换和 PDF OCR 可用：

```bash
sudo apt-get update
sudo apt-get install -y libreoffice tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng poppler-utils fonts-noto-cjk
```

## 5) 常见问题

### `zsh: command not found: metainflow`
- 先执行：`python -m pip install -e '.[dev]'`
- 再执行：重开终端或 `hash -r`

### `.doc` / `.xls` 解析失败（`soffice not found`）
- 安装 `libreoffice`

### PDF 输出为空
- 安装 `tesseract-ocr`、`poppler-utils` 与语言包后重试

## 6) 测试命令

```bash
pytest -q
```

真实样本矩阵校验：

```bash
METAINFLOW_RUN_SAMPLE_MATRIX=1 pytest -q tests/integration/test_real_sample_matrix.py
```

## 7) 面向开发者的文档

如果你是 agent 接入者或需要开发新能力，请看：

- `docs/agent-usage.md`
