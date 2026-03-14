# metainflow-studio-cli

`metainflow-studio-cli` is a Python CLI toolkit. The first implemented command is `parse-doc`.

## Quick Start

```bash
python -m pip install -e .[dev]
pytest -q
python -m metainflow_studio_cli.main parse-doc --file ./sample.txt --output json
```

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

- `PROVIDER_BASE_URL`
- `PROVIDER_API_KEY`
- `PROVIDER_TIMEOUT_SECONDS`
- `PROVIDER_MAX_RETRIES`
- `PROVIDER_MODEL_DOC_PARSE`

## Ubuntu dependencies

Install system packages for full `.doc` and OCR support:

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
