from __future__ import annotations
from typing import Tuple
from ..normalizer import normalize_bytes
from ..schema_ingest import RawDocument, CanonicalDocument

def parse_srt(raw_bytes: bytes, *, encoding: str = "utf-8") -> Tuple[RawDocument, CanonicalDocument, str]:
    return normalize_bytes(raw_bytes, media_type="text/srt", encoding=encoding)

