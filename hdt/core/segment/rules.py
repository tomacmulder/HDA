# -*- coding: utf-8 -*-
from __future__ import annotations
import regex as re
from typing import List
from .spans import Span, Statement, trim_span
from ..schema_ingest import CanonicalDocument  # <-- fixed

# Deterministic sentence ender: ., ?, ! optionally followed by quotes/brackets, then whitespace or end
_SENT_END = re.compile(r'([.?!])(?:["\'\)\]]+)?(?=\s+|$)')

def _statement_id(doc_id: str, start: int, end: int) -> str:
    return f"{doc_id}_S{start}-{end}"

def segment_document(doc: CanonicalDocument) -> List[Statement]:
    text = doc.canonical_text
    n = len(text)
    out: List[Statement] = []
    cursor = 0

    for m in _SENT_END.finditer(text):
        end_idx = m.end()
        raw_span = Span(start=cursor, end=end_idx).clamp(n)
        span = trim_span(text, raw_span)
        if span.end > span.start:
            out.append(Statement(
                id=_statement_id(doc.doc_id, span.start, span.end),
                start=span.start, end=span.end, text=text[span.start:span.end]
            ))
        cursor = end_idx

    if cursor < n:
        span = trim_span(text, Span(start=cursor, end=n))
        if span.end > span.start:
            out.append(Statement(
                id=_statement_id(doc.doc_id, span.start, span.end),
                start=span.start, end=span.end, text=text[span.start:span.end]
            ))

    return out
