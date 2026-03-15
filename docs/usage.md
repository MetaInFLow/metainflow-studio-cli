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

说明：当前 `search-summary` 由 `metainflow-studio-cli` 自己获取搜索结果，再调用配置模型做总结。默认策略是先走智谱结构化搜索，再在失败时回退到百度 Playwright。

### 搜索并输出 JSON

```bash
metainflow search-summary --query "ByteDance 开源项目" --instruction "按项目类型分类" --output json
```

### 搜索总结的模型配置

`search-summary` 自己完成搜索，模型只负责总结。默认已内置智谱搜索 API 的 base URL，通常只需要配置 API Key：

```bash
export PROVIDER_API_KEY="your-api-key"
# 可选：如果总结阶段要走别的端点或 Key，可单独配置
# export SUMMARY_BASE_URL="https://your-summary-endpoint/v1"
# export SUMMARY_API_KEY="your-summary-api-key"
# 可选：单独指定“总结阶段”的模型
# export SUMMARY_MODEL="glm-4.7-flash"
export SEARCH_PAGE_TIMEOUT_SECONDS="30"
export WEB_SEARCH_BACKEND="auto"
export SEARCH_PROVIDER_ENGINE="search_pro"
export SEARCH_RESULT_COUNT="10"
```

说明：
- `PROVIDER_BASE_URL` 默认值是 `https://open.bigmodel.cn/api/paas/v4`
- 如果要切换到别的兼容端点，再显式覆盖 `PROVIDER_BASE_URL`
- 如果总结阶段要单独走其他端点或 API Key，可使用 `SUMMARY_BASE_URL` 和 `SUMMARY_API_KEY`
- `SEARCH_PROVIDER_ENGINE` 控制搜索阶段使用的 provider 搜索引擎/档位
- `SEARCH_RESULT_COUNT` 控制搜索阶段返回的结果数量
- `SUMMARY_MODEL` 控制总结阶段使用的模型；如果没有设置，默认使用 `glm-4.7-flash`

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
