from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.segment.rules import segment_document
from hdt.core.is_analysis.evidential import classify_evidence

def test_testimonial_and_empirical():
    t1 = "According to the report, revenue increased."
    t2 = "The dataset shows an increase."
    for text, expected in [(t1, "testimonial"), (t2, "empirical")]:
        _, can, _ = normalize_bytes(text.encode("utf-8"))
        stmts = segment_document(can)
        row = classify_evidence(stmts)[0]
        assert row.Evidential_Basis == expected
