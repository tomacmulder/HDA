from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.ingest.alignment import compute_byte_starts, AlignmentIndex

def test_crlf_cr_nbsp_normalization_and_index():
    raw = "a\r\nb\rc\u00A0d".encode("utf-8")
    raw_doc, can_doc, orig = normalize_bytes(raw, encoding="utf-8")
    assert can_doc.canonical_text == "a\nb\nc d"
    byte_starts = compute_byte_starts(orig, raw_doc.encoding)
    idx = AlignmentIndex(can_doc.alignment, byte_starts)
    assert idx.forward_char(0) == 0
    assert idx.inverse_char(0) == 0
    assert idx.forward_char(len(orig)) == len(can_doc.canonical_text)
    assert idx.inverse_char(len(can_doc.canonical_text)) == len(orig)
    b0, b1 = idx.inverse_bytes((0, len(can_doc.canonical_text)))
    assert b0 == 0 and b1 == len(raw)

def test_emoji_and_unicode_stability():
    s = "hello ?? ??\u200d??\u200d??\u200d??"
    raw = s.encode("utf-8")
    _, can_doc, orig = normalize_bytes(raw, encoding="utf-8")
    assert can_doc.canonical_text == s
    idx = AlignmentIndex(can_doc.alignment, compute_byte_starts(orig, "utf-8"))
    assert idx.forward_char(0) == 0
    assert idx.inverse_char(len(can_doc.canonical_text)) == len(orig)

def test_utf8_bom_is_removed():
    # bytes with UTF-8 BOM + text
    raw = ("\ufeff" + "Demand grew.").encode("utf-8")
    _, can_doc, _ = normalize_bytes(raw, encoding="utf-8")
    assert can_doc.canonical_text == "Demand grew."
