from __future__ import annotations
from typing import Union, Optional
from ..normalizer import normalize_bytes

def parse_auto(source: Union[str, bytes, bytearray], *, encoding: str = "utf-8", path: Optional[str] = None):
    """
    Flexible parser:
      - If `source` is a path (str), read the file.
      - If `source` is bytes/bytearray, use that directly. Optionally pass `path` to help pick media_type.
    Media types:
      - .md/.markdown -> text/markdown
      - otherwise     -> text/plain
    """
    if isinstance(source, (bytes, bytearray)):
        raw = bytes(source)
        ext_src = (path or "").lower()
    elif isinstance(source, str):
        path = source
        ext_src = path.lower()
        with open(path, "rb") as f:
            raw = f.read()
    else:
        raise TypeError("parse_auto: source must be str path or bytes")

    if ext_src.endswith(".md") or ext_src.endswith(".markdown"):
        media_type = "text/markdown"
    else:
        media_type = "text/plain"

    return normalize_bytes(raw, media_type=media_type, encoding=encoding)
