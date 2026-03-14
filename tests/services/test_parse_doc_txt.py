from pathlib import Path

from metainflow_studio_cli.services.doc_parse.service import parse_document


def test_parse_txt_returns_success_envelope(tmp_path: Path) -> None:
    input_file = tmp_path / "demo.txt"
    input_file.write_text("hello\nworld", encoding="utf-8")

    result = parse_document(str(input_file), output="json")

    assert result["success"] is True
    assert "hello" in result["data"]["markdown"]
    assert result["data"]["source"]["file_type"] == ".txt"
    assert result["error"] is None
