# metainflow-studio-cli

`metainflow-studio-cli` is a Python CLI toolkit. The current implemented commands are `parse-doc` and `search-summary`.

## Skills

Project skills live in `metainflow-skills/` inside this repository so they stay versioned with the CLI implementation.

For local OpenCode discovery, symlink a skill into `~/.agents/skills/` from the repo root:

```bash
ln -sfn "$(pwd)/metainflow-skills/metainflow-doc-parse" "$HOME/.agents/skills/metainflow-doc-parse"
```

More agent-facing setup details are in `docs/agent-usage.md`.

Available repo-local skills:

- `metainflow-doc-parse`
- `metainflow-web-search`

## Quick Start

```bash
python -m pip install -e .[dev]
pytest -q
python -m metainflow_studio_cli.main parse-doc --file ./sample.txt --output json
python -m metainflow_studio_cli.main search-summary --query "React 19 新特性" --output json
```

## Search Summary

Use `search-summary` when you need keyword-based web search plus AI-generated summary:

```bash
metainflow search-summary --query "React 19 新特性" --instruction "按功能分类整理" --output json
```

`metainflow-studio-cli` acquires search results itself using a robust, three-tiered failover strategy:
1. **Zhipu Web Search API** (Primary, highest quality via AI summarization)
2. **SearXNG API** (Secondary fast fallback when Zhipu blocks or returns empty)
3. **Baidu via undetected Playwright** (Ultimate fallback when APIs fail)

After results are extracted, it uses the configured model only for the final summarization.

## Supported `parse-doc` extensions

- `.pdf`
- `.doc` (converted via LibreOffice `soffice`)
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
| `PROVIDER_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | ZhipuAI-compatible API base URL (search) |
| `PROVIDER_API_KEY` | _(required)_ | API key for search provider |
| `PROVIDER_TIMEOUT_SECONDS` | `60` | Request timeout in seconds |
| `PROVIDER_MAX_RETRIES` | `2` | Max retries on failure |
| `PROVIDER_MODEL_DOC_PARSE` | `gpt-4.1-mini` | Model used by `parse-doc` |
| `PROVIDER_MODEL_WEB_SEARCH` | `glm-4-air` | Reserved (currently unused at runtime) |
| `SUMMARY_BASE_URL` | _(falls back to `PROVIDER_BASE_URL`)_ | Override endpoint for summarization |
| `SUMMARY_API_KEY` | _(falls back to `PROVIDER_API_KEY`)_ | Override key for summarization |
| `SUMMARY_MODEL` | `glm-4-flash` | Model used to summarize search results |
| `SEARCH_PAGE_TIMEOUT_SECONDS` | `30` | Playwright page load timeout |
| `WEB_SEARCH_BACKEND` | `auto` | `auto` / `zhipu-web-search` / `baidu-playwright` |
| `SEARCH_PROVIDER_ENGINE` | `search_pro` | ZhipuAI search engine tier |
| `SEARCH_RESULT_COUNT` | `10` | Number of search results to request |
| `SEARXNG_BASE_URL` | `http://localhost:8080` | Endpoint for the SearXNG secondary fallback |
| `METAINFLOW_RUN_SAMPLE_MATRIX` | _(unset)_ | Set to `1` to enable integration tests |

### Playwright fallback (optional)

The Baidu Playwright fallback requires the `playwright` extra and browser binaries:

```bash
pip install -e ".[playwright,dev]"
python -m playwright install chromium
```

If not installed, `WEB_SEARCH_BACKEND=auto` will skip the Playwright fallback gracefully.

### SearXNG fallback (Recommended)

To enable the secondary SearXNG fallback tier, you can run a local container with **JSON format explicitly allowed**:

```bash
# Create custom settings.yml to bypass SearXNG default JSON ban
mkdir -p /tmp/searxng && cat << 'EOF' > /tmp/searxng/settings.yml
search:
  formats:
    - html
    - json
server:
  port: 8080
  bind_address: "0.0.0.0"
  secret_key: "my_ultra_secret_key"
EOF

# Run SearXNG
docker run --rm -d --name searxng -p 8080:8080 -v /tmp/searxng:/etc/searxng searxng/searxng
```

Once running on port `8080` (or another host via `SEARXNG_BASE_URL`), the `WEB_SEARCH_BACKEND=auto` router will seamlessly catch requests that Zhipu fails to process.

## Ubuntu dependencies

Install system packages for full `.doc` / `.xls` and OCR support:

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
