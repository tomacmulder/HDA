from __future__ import annotations
from typing import Any, Dict, List, Tuple

from ..ingest.parsers.auto import parse_auto
from ..segment.rules import segment_document
from ..amu.extract import extract_amus
from ..topic.assign import assign_topics
from ..threads.build import build_threads
from ..links.extract import extract_links
from ..is_analysis.time_modality import analyze_time_modality
from ..is_analysis.evidential import classify_evidence
from ..is_analysis.causal import causal_from_links

def run_all_for_path(path: str, *, encoding: str = "utf-8") -> Dict[str, Any]:
    data = open(path, "rb").read()
    raw, can, _orig = parse_auto(data, encoding=encoding, path=path)
    stmts = segment_document(can)
    amus = extract_amus(stmts)
    topics = assign_topics(amus)
    threads = build_threads(stmts, amus, topics)
    links = extract_links(stmts, threads)
    modal = analyze_time_modality(stmts)
    evid = classify_evidence(stmts)
    causal = causal_from_links(links)

    return {
        "raw": raw,
        "canonical": can,
        "statements": stmts,
        "amus": amus,
        "topics": topics,
        "threads": threads,
        "links": links,
        "modal": modal,
        "evidential": evid,
        "causal": causal,
    }
