from __future__ import annotations
from typing import List
from .schema import CausalEdge
from ..links.schema import LinkRow

def causal_from_links(links: List[LinkRow]) -> List[CausalEdge]:
    """
    Very small SCM-lite: treat "supports" as a causal arrow from the supported statement → current.
    Opposes/references are ignored here (can be extended later).
    """
    edges: List[CausalEdge] = []
    for r in links:
        for sup in r.Supports_IDs:
            edges.append(CausalEdge(from_id=sup, to_id=r.Statement_Text_ID, kind="causes"))
    return edges
