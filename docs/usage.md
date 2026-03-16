# metainflow-studio-cli 使用文档

## 一句话说明

`metainflow-studio-cli` 当前主功能是：

- `parse-doc`：解析文档（本地或 URL），输出文本或 JSON
- `search-summary`：按关键词搜索互联网信息，并输出 AI 总结
- `web-crawl`：抓取指定 URL 的网页内容，并按需总结/提取
- `enterprise-query`：按企业全称/信用代码/注册号查询企业详情
- `enterprise-search`：按简称或片段模糊搜索企业候选
- `enterprise-balance`：查询企业接口余额

支持格式：`.pdf .doc .docx .pptx .xls .xlsx .csv .txt .md .html`

## 0) 环境变量配置

复制模版并填入实际值：

```bash
cp .env.example .env
```

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PROVIDER_BASE_URL` | `https://api.openai.com/v1` | OpenAI 兼容接口地址；如需启用 `search-summary` 的智谱主搜索链路，可改成 `https://open.bigmodel.cn/api/paas/v4` |
| `PROVIDER_API_KEY` | _(必填)_ | API 密钥 |
| `PROVIDER_TIMEOUT_SECONDS` | `60` | 单次请求超时秒数 |
| `PROVIDER_MAX_RETRIES` | `2` | 失败后最大重试次数 |
| `PROVIDER_MODEL_DOC_PARSE` | `gpt-4.1-mini` | `parse-doc` 使用的模型 |
| `PROVIDER_MODEL_WEB_SEARCH` | `glm-4-air` | 搜索 provider 的预留配置 |
| `PROVIDER_MODEL_WEB_FETCH` | `gpt-4.1-mini` | `web-crawl` 总结阶段使用的模型 |
| `SUMMARY_BASE_URL` | 回退到 `PROVIDER_BASE_URL` | `search-summary` 总结阶段可单独覆盖端点 |
| `SUMMARY_API_KEY` | 回退到 `PROVIDER_API_KEY` | `search-summary` 总结阶段可单独覆盖密钥 |
| `SUMMARY_MODEL` | `glm-4-flash` | `search-summary` 总结阶段使用的模型 |
| `SEARCH_PAGE_TIMEOUT_SECONDS` | `30` | 百度 Playwright fallback 的页面超时 |
| `WEB_SEARCH_BACKEND` | `auto` | `auto` / `zhipu-web-search` / `searxng-web-search` / `baidu-playwright` |
| `SEARCH_PROVIDER_ENGINE` | `search_pro` | 智谱搜索档位 |
| `SEARCH_RESULT_COUNT` | `10` | 搜索结果数量 |
| `SEARXNG_BASE_URL` | `http://localhost:8080` | SearXNG fallback 地址 |
| `METAINFLOW_WEB_FETCH_VERIFY_SSL` | `1` | `web-crawl` 是否校验 SSL |
| `METAINFLOW_ENTERPRISE_API_BASE_URL` | `https://test.jszypt.com:42211/admin/api/getTenantApi` | 企业查询接口地址 |
| `METAINFLOW_ENTERPRISE_BALANCE_URL` | `https://test.jszypt.com:42211/sys-tenant-hehe/query` | 企业余额接口地址 |
| `METAINFLOW_ENTERPRISE_API_APP_ID` | _(必填，enterprise 命令需要)_ | 企业接口 appid |
| `METAINFLOW_ENTERPRISE_API_SECRET` | _(必填，enterprise 命令需要)_ | 企业接口 secret |
| `METAINFLOW_ENTERPRISE_API_VERIFY_SSL` | `1` | 企业接口是否校验 SSL |
| `METAINFLOW_RUN_SAMPLE_MATRIX` | _(未设置)_ | 设为 `1` 启用真实样本矩阵集成测试 |

如果需要 `search-summary` 的 Baidu Playwright fallback：

```bash
pip install -e ".[playwright,dev]"
python -m playwright install chromium
```

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
metainflow search-summary --help
metainflow web-crawl --help
metainflow enterprise-search --help
metainflow enterprise-query --help
metainflow enterprise-balance --help
pytest -q
```

## 2) 最常用命令

### 解析本地文件

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx
```

### 解析 URL 并输出 JSON

```bash
metainflow parse-doc --file "https://example.com/page.html" --output json
```

### 搜索互联网信息

```bash
metainflow search-summary --query "React 19 新特性"
metainflow search-summary --query "ByteDance 开源项目" --instruction "按项目类型分类" --output json
```

说明：

- `search-summary` 会先获取搜索结果，再调用总结模型
- `auto` 模式下当前顺序是：智谱 provider 搜索 -> SearXNG -> 百度 Playwright
- 如果只想稳定走智谱主链路，请显式设置 `PROVIDER_BASE_URL=https://open.bigmodel.cn/api/paas/v4`

### 抓取指定 URL

```bash
metainflow web-crawl --url "https://example.com/page.html"
metainflow web-crawl --url "https://example.com/page.html" --instruction "提取主要观点" --output json
```

### 模糊搜索企业候选

```bash
metainflow enterprise-search --keyword "示例智能" --session-id "thread-123" --output json
```

### 精确查询企业详情

```bash
metainflow enterprise-query --type business --keyword "示例智能（深圳）科技有限公司" --session-id "thread-123" --output json
```

### 查询企业接口余额

```bash
metainflow enterprise-balance --session-id "thread-123" --output json
```

如果 `metainflow` 命令不可用，可临时用：

```bash
python -m metainflow_studio_cli.main parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
python -m metainflow_studio_cli.main search-summary --query "React 19 新特性" --output json
python -m metainflow_studio_cli.main web-crawl --url https://example.com/page.html --output json
python -m metainflow_studio_cli.main enterprise-search --keyword "示例智能" --output json
python -m metainflow_studio_cli.main enterprise-query --type business --keyword "示例智能（深圳）科技有限公司" --output json
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

### `search-summary` 没走智谱主链路

- 检查 `PROVIDER_BASE_URL` 是否已设为 `https://open.bigmodel.cn/api/paas/v4`
- 检查 `WEB_SEARCH_BACKEND` 是否被强制改成别的后端

### `web-crawl` 或 Playwright fallback 无法运行

- 执行 `python -m playwright install chromium`

## 6) 测试命令

```bash
pytest -q
```

真实样本矩阵校验：

```bash
METAINFLOW_RUN_SAMPLE_MATRIX=1 pytest -q tests/integration/test_real_sample_matrix.py
```

Attribution: This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.
