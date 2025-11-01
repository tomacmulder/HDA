from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.segment.rules import segment_document
from hdt.core.amu.extract import extract_amus
from hdt.core.topic.assign import assign_topics
from hdt.core.threads.build import build_threads

def test_threads_contiguous_and_anchor_not_phatic():
    text = "Okay, the revenue increased. Revenue grew again! We deploy a new API. API latency dropped."
    _, can, _ = normalize_bytes(text.encode("utf-8"))
    stmts = segment_document(can)
    amus = extract_amus(stmts)
    topics = assign_topics(amus)
    rows = build_threads(stmts, amus, topics)

    # two topic runs: finance then tech → expect 2 thread IDs
    tids = [r.Thread_ID for r in rows]
    assert len(set(tids)) == 2

    # In the first thread, first sentence is phatic, second should be the anchor
    first_tid = tids[0]
    first_thread = [r for r in rows if r.Thread_ID == first_tid]
    roles = [r.Thread_Role for r in first_thread]
    assert "anchor" in roles
    # anchor eligibility should be higher than a phatic opener
    scores = [r.Anchor_Eligibility_Score for r in first_thread]
    assert max(scores) > min(scores)
