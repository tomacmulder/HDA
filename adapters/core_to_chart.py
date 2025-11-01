from __future__ import annotations
from typing import List, Dict, Any
from hdt.core.segment.spans import Statement
from hdt.core.threads.schema import ThreadRow
from hdt.core.links.schema import LinkRow

def _node_radius(text: str) -> float:
    # simple, deterministic radius
    words = max(1, len(text.split()))
    return 4.0 + words ** 0.5

def to_bubble_chart(statements: List[Statement],
                    threads: List[ThreadRow],
                    links: List[LinkRow],
                    meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    meta = dict(meta or {})

    role_of = {t.Statement_Text_ID: t.Thread_Role for t in threads}

    nodes = []
    for s in statements:
        nodes.append({
            "id": s.id,
            "role": role_of.get(s.id, "support"),
            "speaker": None,
            "text": s.text,
            "relation_strength": None,
            "r": _node_radius(s.text),
        })

    edges = []
    for r in links:
        for tgt in r.Supports_IDs:
            edges.append({"src": r.Statement_Text_ID, "tgt": tgt, "kind": "supports"})
        for tgt in r.Opposes_IDs:
            edges.append({"src": r.Statement_Text_ID, "tgt": tgt, "kind": "opposes"})
        for tgt in r.References_IDs:
            edges.append({"src": r.Statement_Text_ID, "tgt": tgt, "kind": "references"})

    return {
        "nodes": nodes,
        "edges": edges,
        "threadCircle": {"R": 100},  # placeholder compatible with your D3
        "legends": {"speakers": []},
        "meta": meta,
    }
