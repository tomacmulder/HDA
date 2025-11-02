from __future__ import annotations
from typing import List, Dict, Any
import json, re

def _lower(s:str)->str: return (s or "").lower()

def analyze_amus(amus: List[Dict[str, Any]], guides: Dict[str, Any] | None=None) -> List[Dict[str, Any]]:
    g = guides.get("guides.scaffold_rules", {}) if guides else {}
    membership = [m.lower() for m in g.get("membership_markers", [])]
    definition = [m.lower() for m in g.get("definition_markers", [])]
    change     = [m.lower() for m in g.get("change_markers", [])]
    negs       = [m.lower() for m in g.get("negation_markers", [])]
    belief     = [m.lower() for m in g.get("belief_markers", [])]

    out = []
    for row in amus or []:
        if (row.get("AMU_Type") or "").lower() != "d_prop":
            continue
        amu_id = row.get("AMU_ID")
        span   = _lower(row.get("Text_Span",""))

        # Event_Kind
        if any(k in span for k in change):
            kind = "process"
        elif re.search(r"\b(\w+ing)\b", span):
            kind = "process"
        elif re.search(r"\b(won|reached|achieved|completed)\b", span):
            kind = "achievement"
        else:
            kind = "state"

        # Predication
        if any(k in span for k in definition):
            pred = "definition"
        elif any(k in span for k in membership):
            pred = "membership"
        elif any(k in span for k in change):
            pred = "change_delta"
        else:
            pred = "state_is"

        # Negation / Intensionality
        neg = "explicit" if any(k in span for k in negs) else "none"
        inten = "belief_about_world" if any(k in span for k in belief) else "extensional"

        args = {}  # keep empty; later, slot-filling can enrich
        out.append({
            "AMU_ID": amu_id,
            "Event_Kind": kind,
            "Predication": pred,
            "Arguments": json.dumps(args, ensure_ascii=False),
            "Negation": neg,
            "Intensionality": inten
        })
    return out
# --- compat shim: legacy callers expect analyze(...) in scaffold.py
def analyze(statements_or_amus, guides=None):
    return analyze_amus(statements_or_amus, guides=guides)
