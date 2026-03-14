from pathlib import Path
import os

import pytest

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
