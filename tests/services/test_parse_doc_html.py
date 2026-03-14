from pathlib import Path

from metainflow_studio_cli.services.doc_parse.service import parse_document


def test_parse_html_extracts_text(tmp_path: Path) -> None:
    input_file = tmp_path / "page.html"
    input_file.write_text("<html><body><h1>Title</h1><p>Hello world</p></body></html>", encoding="utf-8")

    result = parse_document(str(input_file), output="json")

    assert result["success"] is True
    assert "Title" in result["data"]["markdown"]
    assert "Hello world" in result["data"]["markdown"]
