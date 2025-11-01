from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.segment.rules import segment_document
from hdt.core.amu.extract import extract_amus
from hdt.core.is_analysis.scaffold import build_scaffold

def _pipeline(text: str):
    _, can, _ = normalize_bytes(text.encode("utf-8"))
    stmts = segment_document(can)
    amus = extract_amus(stmts)
    return stmts, amus

def test_scaffold_change_vs_state():
    stmts, amus = _pipeline("Revenue increased. The system is stable.")
    rows = build_scaffold(stmts, amus)
    kinds = [r.Event_Kind for r in rows]
    preds = [r.Predication for r in rows]
    assert "process" in kinds
    assert "state" in kinds
    assert "change_delta" in preds
    assert "state_is" in preds

def test_scaffold_negation_and_intension():
    stmts, amus = _pipeline("We do not believe the report is accurate.")
    row = build_scaffold(stmts, amus)[0]
    assert row.Negation == "explicit"
    assert row.Intensionality == "belief_about_world"
