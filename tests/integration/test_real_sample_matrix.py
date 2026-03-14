from pathlib import Path
import os
import shutil

import pytest

from metainflow_studio_cli.services.doc_parse.service import parse_document
from metainflow_studio_cli.testing.sample_matrix import summarize_sample_matrix


SAMPLES_DIR = Path(__file__).resolve().parent / "samples"


@pytest.mark.integration
def test_real_sample_matrix() -> None:
    if os.getenv("METAINFLOW_RUN_SAMPLE_MATRIX") != "1":
        pytest.skip("set METAINFLOW_RUN_SAMPLE_MATRIX=1 to run real sample matrix")

    if not SAMPLES_DIR.exists():
        pytest.skip("integration samples directory is missing")

    summary = summarize_sample_matrix(SAMPLES_DIR)
    missing = summary["missing_extensions"]
    assert not missing, f"missing sample extensions: {', '.join(missing)}"


@pytest.mark.integration
def test_parse_real_xls_sample_when_soffice_available() -> None:
    if os.getenv("METAINFLOW_RUN_SAMPLE_MATRIX") != "1":
        pytest.skip("set METAINFLOW_RUN_SAMPLE_MATRIX=1 to run real sample matrix")

    sample_xls = SAMPLES_DIR / "sample.xls"
    if not sample_xls.exists():
        pytest.skip("sample.xls fixture is missing")

    if shutil.which("soffice") is None:
        pytest.skip("LibreOffice is required to parse real .xls fixtures")

    result = parse_document(str(sample_xls), output="json")

    assert result["success"] is True
    assert result["data"]["source"]["resolved_path"] == str(sample_xls)
    assert result["data"]["source"]["file_type"] == ".xls"
    assert result["data"]["tables"][:3] == [
        ["region", "region", "total"],
        ["north", "", ""],
        ["north", "", ""],
    ]
