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

`metainflow-studio-cli` acquires search results itself (currently `www.baidu.com` as primary and `m.baidu.com` as fallback via undetected Playwright), then uses the configured model only for summarization.

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

- `PROVIDER_BASE_URL`
- `PROVIDER_API_KEY`
- `PROVIDER_TIMEOUT_SECONDS`
- `PROVIDER_MAX_RETRIES`
- `PROVIDER_MODEL_DOC_PARSE`
- `PROVIDER_MODEL_WEB_SEARCH`

### Search Summary Config

`search-summary` uses Playwright for search acquisition and a normal chat/completions-compatible model for summarization.

Typical local setup:

```bash
export PROVIDER_BASE_URL="https://your-openai-compatible-endpoint/v1"
export PROVIDER_API_KEY="your-api-key"
export PROVIDER_MODEL_WEB_SEARCH="your-model-name"
export WEB_SEARCH_PAGE_TIMEOUT_SECONDS="30"
```

Then verify with:

```bash
python -m playwright install chromium
metainflow search-summary --query "React 19 新特性" --output json
```

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
