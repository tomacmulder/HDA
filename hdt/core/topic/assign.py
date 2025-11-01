from __future__ import annotations
from typing import List, Dict, Tuple
import re
from .schema import TopicAssignment
from ..amu.schema import AMU

# ultra-lean keyword buckets; extendable later or by config
_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "finance": ("revenue", "profit", "margin", "cost", "price", "budget", "roi", "cash", "sales"),
    "tech": ("model", "api", "latency", "throughput", "python", "deploy", "data", "feature"),
    "health": ("patient", "therapy", "drug", "vaccine", "health", "mental", "risk"),
    "climate": ("emission", "carbon", "climate", "sustainab", "renewable", "green"),
    "policy": ("regulation", "bill", "law", "policy", "compliance"),
    "sports": ("match", "game", "tournament", "score", "league"),
}

def _slug(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "general"

def _score_label(text: str) -> Tuple[str, float, list]:
    t = text.lower()
    best_label, best_hits = "general", 0
    hits_list: list[str] = []
    for label, keys in _KEYWORDS.items():
        h = [k for k in keys if k in t]
        if len(h) > best_hits:
            best_label, best_hits = label, len(h)
            hits_list = h
    conf = min(1.0, 0.5 + 0.1 * best_hits) if best_label != "general" else 0.4
    return best_label, conf, hits_list

def assign_topics(amus: List[AMU]) -> List[TopicAssignment]:
    out: List[TopicAssignment] = []
    for a in amus:
        label, conf, hits = _score_label(a.Text_Span)
        tid = f"topic:{_slug(label)}"
        out.append(TopicAssignment(
            AMU_ID=a.AMU_ID,
            Topic_ID=tid,
            Topic_Label=label,
            Topic_Assign_Confidence=conf,
            Topic_Disambiguators=list(sorted(set(hits))),
        ))
    return out
