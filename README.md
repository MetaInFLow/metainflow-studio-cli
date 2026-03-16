# metainflow-studio-cli

`metainflow-studio-cli` is a Python CLI toolkit. The current implemented commands are `parse-doc`, `search-summary`, `web-crawl`, `enterprise-query`, `enterprise-search`, and `enterprise-balance`.

## Skills

Project skills live in `metainflow-skills/` inside this repository so they stay versioned with the CLI implementation.

For local OpenCode discovery, symlink skills into `~/.agents/skills/` from the repo root:

```bash
ln -sfn "$(pwd)/metainflow-skills/metainflow-doc-parse" "$HOME/.agents/skills/metainflow-doc-parse"
ln -sfn "$(pwd)/metainflow-skills/metainflow-web-search" "$HOME/.agents/skills/metainflow-web-search"
ln -sfn "$(pwd)/metainflow-skills/metainflow-web-fetch" "$HOME/.agents/skills/metainflow-web-fetch"
ln -sfn "$(pwd)/metainflow-skills/metainflow-enterprise-query" "$HOME/.agents/skills/metainflow-enterprise-query"
```

More agent-facing setup details are in `docs/agent-usage.md`.

Available repo-local skills:

- `metainflow-doc-parse`
- `metainflow-web-search`
- `metainflow-web-fetch`
- `metainflow-enterprise-query`

## Quick Start

```bash
python -m pip install -e .[dev]
pytest -q
python -m metainflow_studio_cli.main parse-doc --file ./sample.txt --output json
python -m metainflow_studio_cli.main search-summary --query "React 19 新特性" --output json
python -m metainflow_studio_cli.main web-crawl --url https://example.com --output json
python -m metainflow_studio_cli.main enterprise-search --keyword "示例智能" --output json
python -m metainflow_studio_cli.main enterprise-query --type business --keyword "示例智能（深圳）科技有限公司" --output json
```

## Search Summary

Use `search-summary` when you need keyword-based web search plus AI-generated summary.

The current routing strategy is:

1. Zhipu-compatible provider web search
2. SearXNG fallback
3. Baidu Playwright fallback

After results are collected, the configured summary model generates the final answer.

## Web Crawl

Use `web-crawl` when you already have a target URL and need page extraction with optional summarization. This command uses Crawl4AI for page retrieval.

## Enterprise Query

Use `enterprise-query` for exact enterprise detail lookup, `enterprise-search` for fuzzy candidate search, and `enterprise-balance` for balance diagnostics. The recommended agent routing is `exact-first, fuzzy-fallback` for strong full names and `fuzzy-first` for ambiguous fragments. Pass `--session-id` when you want cache reuse across repeated lookups for the same agent session.

## Supported `parse-doc` extensions

- `.pdf`
- `.doc` (converted via LibreOffice `soffice`)
- `.xls` (converted via LibreOffice `soffice`)
- `.docx`
- `.pptx`
- `.xlsx`
- `.csv`
- `.txt`, `.md`
- `.html`

## Environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `PROVIDER_BASE_URL` | `https://api.openai.com/v1` | Base URL for provider-compatible requests. Set this to `https://open.bigmodel.cn/api/paas/v4` if you want the Zhipu provider path for `search-summary`. |
| `PROVIDER_API_KEY` | _(required)_ | API key |
| `PROVIDER_TIMEOUT_SECONDS` | `60` | Request timeout in seconds |
| `PROVIDER_MAX_RETRIES` | `2` | Max retries on failure |
| `PROVIDER_MODEL_DOC_PARSE` | `gpt-4.1-mini` | Model used by `parse-doc` |
| `PROVIDER_MODEL_WEB_SEARCH` | `glm-4-air` | Reserved search-provider model setting |
| `PROVIDER_MODEL_WEB_FETCH` | `gpt-4.1-mini` | Model used by `web-crawl` summarization |
| `SUMMARY_BASE_URL` | _(falls back to `PROVIDER_BASE_URL`)_ | Optional separate endpoint for `search-summary` summarization |
| `SUMMARY_API_KEY` | _(falls back to `PROVIDER_API_KEY`)_ | Optional separate key for `search-summary` summarization |
| `SUMMARY_MODEL` | `glm-4-flash` | Model used to summarize search results |
| `SEARCH_PAGE_TIMEOUT_SECONDS` | `30` | Baidu Playwright page timeout |
| `WEB_SEARCH_BACKEND` | `auto` | `auto` / `zhipu-web-search` / `searxng-web-search` / `baidu-playwright` |
| `SEARCH_PROVIDER_ENGINE` | `search_pro` | Zhipu search engine tier |
| `SEARCH_RESULT_COUNT` | `10` | Number of search results to request |
| `SEARXNG_BASE_URL` | `http://localhost:8080` | Endpoint for the SearXNG fallback |
| `METAINFLOW_WEB_FETCH_VERIFY_SSL` | `1` | Whether `web-crawl` verifies SSL certificates |
| `METAINFLOW_ENTERPRISE_API_BASE_URL` | `https://test.jszypt.com:42211/admin/api/getTenantApi` | Enterprise query endpoint |
| `METAINFLOW_ENTERPRISE_BALANCE_URL` | `https://test.jszypt.com:42211/sys-tenant-hehe/query` | Enterprise balance endpoint |
| `METAINFLOW_ENTERPRISE_API_APP_ID` | _(required for enterprise commands)_ | Enterprise API appid |
| `METAINFLOW_ENTERPRISE_API_SECRET` | _(required for enterprise commands)_ | Enterprise API secret |
| `METAINFLOW_ENTERPRISE_API_VERIFY_SSL` | `1` | Whether enterprise requests verify SSL |
| `METAINFLOW_RUN_SAMPLE_MATRIX` | _(unset)_ | Set to `1` to enable real sample matrix integration tests |

### Playwright fallback

The Baidu fallback path in `search-summary` requires the optional `undetected-playwright` extra and browser binaries:

```bash
pip install -e ".[playwright,dev]"
python -m playwright install chromium
```

### Search provider note

If you want provider-backed search instead of pure fallback mode, set:

```bash
export PROVIDER_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
export PROVIDER_API_KEY="your-api-key"
```

You can still keep `SUMMARY_BASE_URL` and `SUMMARY_API_KEY` separate for summarization.

## Ubuntu dependencies

Install system packages for full `.doc` / `.xls` conversion and OCR support:

```bash
sudo apt-get update
sudo apt-get install -y libreoffice tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng poppler-utils fonts-noto-cjk
```

## Real sample matrix validation

1. Put real fixture files under `tests/integration/samples/` so that all required extensions exist.
2. Run:

```bash
METAINFLOW_RUN_SAMPLE_MATRIX=1 pytest -q tests/integration/test_real_sample_matrix.py
```

By default, the sample matrix test is skipped unless `METAINFLOW_RUN_SAMPLE_MATRIX=1` is set.

Attribution: This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.
