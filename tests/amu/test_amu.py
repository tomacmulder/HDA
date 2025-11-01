from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.segment.rules import segment_document
from hdt.core.amu.extract import extract_amus

def test_amus_from_statements_are_extractive_and_stable():
    s = "Cats purr. Dogs bark!"
    _, can, _ = normalize_bytes(s.encode("utf-8"))
    stmts = segment_document(can)
    amus = extract_amus(stmts)
    assert len(amus) == len(stmts)
    for amu, st in zip(amus, stmts):
        assert amu.Text_Span == st.text
        assert amu.Char_Start == st.start and amu.Char_End == st.end
        assert amu.AMU_ID.startswith(st.id + "@")
