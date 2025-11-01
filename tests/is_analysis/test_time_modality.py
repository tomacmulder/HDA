from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.segment.rules import segment_document
from hdt.core.is_analysis.time_modality import analyze_time_modality

def test_future_hedged_next_quarter():
    text = "Revenue might increase next quarter."
    _, can, _ = normalize_bytes(text.encode("utf-8"))
    stmts = segment_document(can)
    row = analyze_time_modality(stmts)[0]
    assert row.Time_Axis == "future"
    assert row.Temporal_Horizon in {"short_term","long_term"}  # next quarter → long_term by our heuristic
    assert row.Epistemic_Modality == "hedged"

def test_counterfactual():
    text = "Revenue would grow if demand doubled."
    _, can, _ = normalize_bytes(text.encode("utf-8"))
    stmts = segment_document(can)
    row = analyze_time_modality(stmts)[0]
    assert row.Change_Tense_Signal == "counterfactual"
    assert row.Epistemic_Modality == "counterfactual"
