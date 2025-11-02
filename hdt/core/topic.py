from __future__ import annotations
from typing import List, Dict, Any
import re

def _score(span: str, kws: list[str]) -> tuple[float, list[str]]:
    if not span or not kws: return 0.0, []
    tl = span.lower()
    hits = [kw for kw in kws if re.search(rf"\b{re.escape(kw.lower())}\b", tl)]
    if not hits: return 0.0, []
    # simple saturation curve
    conf = min(1.0, 0.4 + 0.15 * len(set(hits)))
    return conf, hits

def assign_topics(amus: List[Dict[str, Any]], guides: Dict[str, Any]) -> List[Dict[str, Any]]:
    vocab: Dict[str, list[str]] = guides.get("topic_keywords", {})
    default_id = guides.get("default_topic_id", "misc")
    default_label = guides.get("default_topic_label", "Miscellaneous")

    out: List[Dict[str, Any]] = []
    for row in amus:
        span = row.get("Text_Span","")
        best_id, best_label, best_conf, hits = default_id, default_label, 0.0, []
        for topic_id, kws in vocab.items():
            conf, h = _score(span, kws or [])
            if conf > best_conf:
                best_id, best_label, best_conf, hits = topic_id, topic_id, conf, h
        out.append({
            "AMU_ID": row.get("AMU_ID"),
            "Topic_ID": best_id,
            "Topic_Label": best_label,
            "Topic_Assign_Confidence": round(best_conf, 3),
            "Topic_Disambiguators": sorted(list(set(hits))),
        })
    return out
