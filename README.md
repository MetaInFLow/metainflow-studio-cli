# metainflow-studio-cli

`metainflow-studio-cli` is a Python CLI toolkit. The current implemented commands are `parse-doc` and `web-crawl`.

## Skills

Project skills live in `metainflow-skills/` inside this repository so they stay versioned with the CLI implementation.

For local OpenCode discovery, symlink a skill into `~/.agents/skills/` from the repo root:

```bash
ln -sfn "$(pwd)/metainflow-skills/metainflow-doc-parse" "$HOME/.agents/skills/metainflow-doc-parse"
ln -sfn "$(pwd)/metainflow-skills/metainflow-web-fetch" "$HOME/.agents/skills/metainflow-web-fetch"
```

More agent-facing setup details are in `docs/agent-usage.md`.

Available repo-local skills:

- `metainflow-doc-parse`
- `metainflow-web-fetch`

## Quick Start

```bash
python -m pip install -e .[dev]
pytest -q
python -m metainflow_studio_cli.main parse-doc --file ./sample.txt --output json
python -m metainflow_studio_cli.main web-crawl --url https://example.com --output json
```

## Web Crawl

Use `web-crawl` when you have a specific URL and need page content extraction with optional AI summarization.

Attribution: This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.

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
| `PROVIDER_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL |
| `PROVIDER_API_KEY` | _(required)_ | API key |
| `PROVIDER_TIMEOUT_SECONDS` | `60` | Request timeout in seconds |
| `PROVIDER_MAX_RETRIES` | `2` | Max retries on failure |
| `PROVIDER_MODEL_DOC_PARSE` | `gpt-4.1-mini` | Model used by `parse-doc` |
| `PROVIDER_MODEL_WEB_FETCH` | `gpt-4.1-mini` | Model used by `web-crawl` |
| `METAINFLOW_WEB_FETCH_VERIFY_SSL` | `1` | Whether `web-crawl` verifies SSL certificates |
| `METAINFLOW_RUN_SAMPLE_MATRIX` | _(unset)_ | Set to `1` to enable real sample matrix integration tests |

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
