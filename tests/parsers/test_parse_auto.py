from __future__ import annotations
from pathlib import Path
from hdt.core.ingest.parsers.auto import parse_auto

def test_parse_txt(tmp_path: Path):
    p = tmp_path / "demo.txt"
    # Write CRLF + NBSP as raw bytes to avoid newline translation
    p.write_bytes("Hello\r\nWorld\u00A0!".encode("utf-8"))
    raw, can, orig = parse_auto(str(p))
    assert can.canonical_text == "Hello\nWorld !"

def test_parse_md(tmp_path: Path):
    p = tmp_path / "demo.md"
    p.write_bytes("# Title\r\n\r\nBody.".encode("utf-8"))
    raw, can, orig = parse_auto(str(p))
    assert "Body." in can.canonical_text
