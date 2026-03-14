import json
from pathlib import Path

from typer.testing import CliRunner

from metainflow_studio_cli.main import app


runner = CliRunner()


def test_parse_doc_json_output_for_txt(tmp_path: Path) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text("sample content", encoding="utf-8")

    result = runner.invoke(app, ["parse-doc", "--file", str(input_file), "--output", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["data"]["source"]["file_type"] == ".txt"
