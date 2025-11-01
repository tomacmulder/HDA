from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.segment.rules import segment_document

def test_segment_three_sentences_with_crlf_and_nbsp():
    s = "Hello world!\r\nThis is a test.\nNew line\u00A0with NBSP."
    raw, can, _ = normalize_bytes(s.encode("utf-8"))
    statements = segment_document(can)
    texts = [st.text for st in statements]
    assert texts == ["Hello world!", "This is a test.", "New line with NBSP."]
