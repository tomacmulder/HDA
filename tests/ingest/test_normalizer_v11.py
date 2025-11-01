from __future__ import annotations
import unicodedata
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.ingest.alignment import compute_byte_starts, AlignmentIndex

def test_nfc_on_combining_marks():
    # "Cafe\u0301" (e + combining acute) should become "Café" in NFC
    s_orig = "Cafe\u0301\n"
    s_nfc = unicodedata.normalize("NFC", s_orig)
    raw = s_orig.encode("utf-8")
    raw_doc, can_doc, orig = normalize_bytes(raw, encoding="utf-8")
    assert can_doc.canonical_text == s_nfc
    # basic mapping sanity across whole string
    idx = AlignmentIndex(can_doc.alignment, compute_byte_starts(orig, raw_doc.encoding))
    b0, b1 = idx.inverse_bytes((0, len(can_doc.canonical_text)))
    assert b0 == 0 and b1 == len(raw)

def test_family_emoji_grapheme_cluster():
    s = "family: ??\u200d??\u200d??\u200d?? end"
    raw = s.encode("utf-8")
    raw_doc, can_doc, orig = normalize_bytes(raw, encoding="utf-8")
    assert can_doc.canonical_text == s  # emoji cluster preserved
    idx = AlignmentIndex(can_doc.alignment, compute_byte_starts(orig, raw_doc.encoding))
    assert idx.forward_char(0) == 0
    assert idx.inverse_char(len(can_doc.canonical_text)) == len(orig)
