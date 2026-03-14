from typer.testing import CliRunner

from metainflow_studio_cli.main import app


runner = CliRunner()


def test_help_contains_parse_doc_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "parse-doc" in result.stdout
