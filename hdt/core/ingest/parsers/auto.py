from __future__ import annotations
from pathlib import Path
from typing import Tuple
from .txt import parse_txt
from .md import parse_md
from .srt import parse_srt
from ...schema_ingest import RawDocument, CanonicalDocument

def parse_auto(raw_bytes: bytes, *, encoding: str = "utf-8", path: str | None = None) -> Tuple[RawDocument, CanonicalDocument, str]:
    ext = Path(path).suffix.lower() if path else ""
    if ext in {".md", ".markdown"}:
        return parse_md(raw_bytes, encoding=encoding)
    if ext in {".srt"}:
        return parse_srt(raw_bytes, encoding=encoding)
    return parse_txt(raw_bytes, encoding=encoding)
