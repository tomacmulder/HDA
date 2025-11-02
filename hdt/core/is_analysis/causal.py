from __future__ import annotations
from typing import List, Dict, Any
import json

def build_scm(scaffold_rows: List[Dict[str, Any]], guides: Dict[str, Any] | None=None) -> List[Dict[str, Any]]:
    # Minimal, conservative: create one node per scaffold AMU; infer no edges by default.
    # Future: use guides.edge_markers to propose edges between consecutive related nodes.
    out = []
    for sc in scaffold_rows or []:
        node_id = sc.get("AMU_ID") or ""
        out.append({
            "SCM_Node_ID": node_id,
            "SCM_Edges": json.dumps([], ensure_ascii=False),
            "Mechanism_Role": ""
        })
    return out
# --- compat shim for legacy pipeline usage
def _to_dict(obj):
    if isinstance(obj, dict): return obj
    for attr in ("model_dump","dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                d = fn()
                if isinstance(d, dict):
                    return d
            except Exception:
                pass
    return {}

def causal_from_links(*args, **kwargs):
    """
    Accepts (links[, guides]) or kwargs like links=[...].
    Produces a minimal causal edge list; if nothing usable, returns [].
    """
    links = None
    if args:
        # allow (links) or (unused, links)
        for a in args:
            if isinstance(a, (list, tuple)):
                links = a; break
    if links is None:
        links = kwargs.get("links", []) or kwargs.get("rows", []) or []
    out = []
    for i, row in enumerate(links):
        d = _to_dict(row)
        src = d.get("from") or d.get("source") or d.get("src") or d.get("head") or ""
        dst = d.get("to")   or d.get("target") or d.get("tgt") or d.get("tail") or ""
        kind = (d.get("kind") or d.get("type") or d.get("relation") or "correlates")
        out.append({
            "SCM_Node_ID": f"N{i+1}",
            "SCM_Edges": [{"from": src, "to": dst, "kind": str(kind)}],
            "Mechanism_Role": d.get("mechanism_role", "")
        })
    return out
