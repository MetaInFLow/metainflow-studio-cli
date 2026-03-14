from pathlib import Path

from metainflow_studio_cli.testing.sample_matrix import REQUIRED_SAMPLE_EXTENSIONS, summarize_sample_matrix


def test_sample_matrix_reports_missing_extensions(tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_bytes(b"x")
    (tmp_path / "legacy.xls").write_bytes(b"x")
    (tmp_path / "b.xlsx").write_bytes(b"x")

    summary = summarize_sample_matrix(tmp_path)

    assert ".pdf" in summary["present_extensions"]
    assert ".xls" in summary["present_extensions"]
    assert ".xlsx" in summary["present_extensions"]
    assert ".doc" in summary["missing_extensions"]
    assert set(summary["required_extensions"]) == REQUIRED_SAMPLE_EXTENSIONS
