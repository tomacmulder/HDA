from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.segment.rules import segment_document
from hdt.core.amu.extract import extract_amus
from hdt.core.topic.assign import assign_topics
from hdt.core.threads.build import build_threads
from hdt.core.links.extract import extract_links

def _pipeline(text: str):
    _, can, _ = normalize_bytes(text.encode("utf-8"))
    stmts = segment_document(can)
    amus = extract_amus(stmts)
    topics = assign_topics(amus)
    threads = build_threads(stmts, amus, topics)
    links = extract_links(stmts, threads)
    return stmts, threads, links

def test_support_then_oppose():
    # S1 -> S2 supports (therefore), S3 opposes previous (however)
    text = "Demand grew. Therefore, revenue increased. However, costs rose."
    stmts, threads, links = _pipeline(text)
    ids = [s.id for s in stmts]

    # Find rows by statement id
    rows = {r.Statement_Text_ID: r for r in links}
    # S2 supports S1
    assert rows[ids[1]].Supports_IDs == [ids[0]]
    # S3 opposes S2
    assert rows[ids[2]].Opposes_IDs == [ids[1]]
    # No self loops
    assert ids[0] not in rows[ids[0]].Supports_IDs + rows[ids[0]].Opposes_IDs + rows[ids[0]].References_IDs

def test_reference_cue_weak():
    text = "We published a report. See the report for details."
    stmts, threads, links = _pipeline(text)
    ids = [s.id for s in stmts]
    rows = {r.Statement_Text_ID: r for r in links}
    assert rows[ids[1]].References_IDs == [ids[0]]
    assert rows[ids[1]].Relation_Strength == "weak"
