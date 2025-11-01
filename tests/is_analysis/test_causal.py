from __future__ import annotations
from hdt.core.ingest.normalizer import normalize_bytes
from hdt.core.segment.rules import segment_document
from hdt.core.amu.extract import extract_amus
from hdt.core.topic.assign import assign_topics
from hdt.core.threads.build import build_threads
from hdt.core.links.extract import extract_links
from hdt.core.is_analysis.causal import causal_from_links

def test_causal_edge_from_support():
    text = "Demand grew. Therefore, revenue increased."
    _, can, _ = normalize_bytes(text.encode("utf-8"))
    stmts = segment_document(can)
    amus = extract_amus(stmts)
    topics = assign_topics(amus)
    threads = build_threads(stmts, amus, topics)
    links = extract_links(stmts, threads)
    edges = causal_from_links(links)
    ids = [s.id for s in stmts]
    d = edges[0].model_dump()
    assert d["from_id"] == ids[0] and d["to_id"] == ids[1] and d["kind"] == "causes"
