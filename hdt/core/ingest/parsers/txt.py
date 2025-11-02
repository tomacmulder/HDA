from __future__ import annotations
from ..normalizer import normalize_bytes

def parse_txt(path: str):
    with open(path, "rb") as f:
        raw = f.read()
    # Treat all plain text as UTF-8 and let the normalizer handle CRLF, NBSP, BOM, etc.
    return normalize_bytes(raw, media_type="text/plain", encoding="utf-8")
