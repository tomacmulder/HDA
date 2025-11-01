from __future__ import annotations
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field

SpanKind = Literal["keep", "delete", "insert", "replace"]

class SpanOp(BaseModel):
    """A delta from original-decoded text (char indices) to canonical text (char indices)."""
    kind: SpanKind
    orig: tuple[int, int]        # [start,end) in original *decoded* text (char indices)
    canon: tuple[int, int]       # [start,end) in canonical text (char indices)

class Alignment(BaseModel):
    """Char-index level alignment between original-decoded text and canonical text."""
    version: str = "v1"
    ops: List[SpanOp]
    encoding: str = "utf-8"
    orig_len: int
    canon_len: int

class RawDocument(BaseModel):
    doc_id: str
    media_type: str = "text/plain"
    encoding: str = "utf-8"
    bytes_len: int
    source_uri: Optional[str] = None

class CanonicalDocument(BaseModel):
    doc_id: str
    canonical_text: str
    # Optional: simple language blocks; v1 we keep one block until detection is added.
    lang_blocks: List[Dict[str, object]] = Field(default_factory=list)
    alignment: Alignment
