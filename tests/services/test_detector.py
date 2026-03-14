from metainflow_studio_cli.services.doc_parse.detector import SUPPORTED_EXTENSIONS, detect_extension


def test_supported_extensions_cover_required_formats() -> None:
    expected = {".pdf", ".doc", ".docx", ".pptx", ".xlsx", ".csv", ".txt", ".md", ".html"}
    assert expected.issubset(SUPPORTED_EXTENSIONS)


def test_detect_extension_lowercases_suffix() -> None:
    assert detect_extension("Report.PDF") == ".pdf"
