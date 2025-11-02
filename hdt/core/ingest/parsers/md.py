from __future__ import annotations
from ..normalizer import normalize_bytes

def parse_md(path: str):
    with open(path, "rb") as f:
        raw = f.read()
    # Treat markdown as text; normalization handles CR/LF, NBSP, BOM, etc.
    return normalize_bytes(raw, media_type="text/markdown", encoding="utf-8")
