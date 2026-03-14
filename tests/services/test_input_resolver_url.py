from pathlib import Path

from metainflow_studio_cli.services.doc_parse.input_resolver import resolve_input


class _FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return None


def test_resolve_url_downloads_file(monkeypatch, tmp_path: Path) -> None:
    def fake_get(url: str, timeout: int) -> _FakeResponse:
        assert url == "https://example.com/sample.html"
        assert timeout == 30
        return _FakeResponse(b"<html><body>ok</body></html>")

    monkeypatch.setattr("metainflow_studio_cli.services.doc_parse.input_resolver.httpx.get", fake_get)

    resolved = resolve_input(
        "https://example.com/sample.html",
        download_dir=tmp_path,
        timeout_seconds=30,
    )

    assert resolved.source_type == "url"
    assert resolved.local_path.exists()
    assert resolved.local_path.suffix == ".html"
