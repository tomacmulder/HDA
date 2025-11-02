from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import re

__all__ = ["infer_links"]

def _dget(obj: Any, keys, default=None):
    if isinstance(keys, str): keys = [keys]
    if isinstance(obj, dict):
        for k in keys:
            if k in obj:
                return obj[k]
    for k in keys:
        v = getattr(obj, k, None)
        if v is not None:
            return v
    return default

def _tokhits(text: str, phrases: List[str]) -> List[str]:
    tl = (text or "").lower()
    hits = []
    for p in (phrases or []):
        pl = p.lower()
        # word-ish match, allow multi-word phrases
        if re.search(rf"\b{re.escape(pl)}\b", tl):
            hits.append(p)
    return hits

def _strength(n_hits: int, base: float = 0.33) -> str:
    # crude: 1 hit = weak, 2 = moderate, 3+ = strong
    if n_hits >= 3: return "strong"
    if n_hits == 2: return "moderate"
    return "weak" if n_hits >= 1 else "weak"

def infer_links(statements: List[Any],
                threads: Optional[List[Dict[str, Any]]] = None,
                guides: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Deterministic link inference:
      - Walk statements in original order.
      - Within the same thread (if provided), connect each statement to the most recent prior statement in that thread.
      - Classify as supports / opposes / references by lexical cues (from guides, with sensible defaults).
      - Outputs one row per statement with aggregated target IDs & cues.
    Schema columns expected:
      Statement_Text_ID, Supports_IDs[], Opposes_IDs[], References_IDs[], Relation_Cues[], Relation_Strength
    """
    g = guides or {}
    cues_sup = g.get("supports_cues", ["agree", "supports", "consistent with", "confirms", "corroborates", "makes sense"])
    cues_opp = g.get("opposes_cues",  ["but", "however", "disagree", "contradict", "refute", "undermines", "inconsistent"])
    cues_ref = g.get("references_cues", ["according to", "as stated", "as reported", "cites", "refers to", "see"])

    # Build quick lookups
    sid_order: List[str] = []
    sid_text: Dict[str, str] = {}
    for i, st in enumerate(statements):
        sid = _dget(st, ["id","statement_id","Statement_Text_ID"], f"S{i+1}")
        txt = _dget(st, ["text","Statement_Text","raw"], "")
        sid_order.append(sid)
        sid_text[sid] = txt

    sid_thread: Dict[str, str] = {}
    if threads:
        for r in threads:
            s = _dget(r, "Statement_Text_ID")
            t = _dget(r, "Thread_ID")
            if s and t:
                sid_thread[s] = t

    rows: List[Dict[str, Any]] = []
    last_in_thread: Dict[str, str] = {}  # thread_id -> last sid

    for sid in sid_order:
        txt = sid_text.get(sid, "")
        tid = sid_thread.get(sid, "__global__")

        supports, opposes, references, cues = [], [], [], []

        prev_sid = last_in_thread.get(tid)
        if prev_sid:
            # Classify relationship from this text to the previous in-thread statement
            sup_hits = _tokhits(txt, cues_sup)
            opp_hits = _tokhits(txt, cues_opp)
            ref_hits = _tokhits(txt, cues_ref)
            n_all = len(sup_hits) + len(opp_hits) + len(ref_hits)

            if len(opp_hits) > max(len(sup_hits), len(ref_hits)):
                opposes.append(prev_sid); cues.extend(opp_hits)
            elif len(sup_hits) > max(len(opp_hits), len(ref_hits)):
                supports.append(prev_sid); cues.extend(sup_hits)
            elif len(ref_hits) > 0:
                references.append(prev_sid); cues.extend(ref_hits)
            # If no cues, leave empty; downstream steps can still use threads.

            strength = _strength(n_all)
        else:
            strength = "weak"

        rows.append({
            "Statement_Text_ID": sid,
            "Supports_IDs": supports,
            "Opposes_IDs": opposes,
            "References_IDs": references,
            "Relation_Cues": list(dict.fromkeys(cues)),  # de-dup preserve order
            "Relation_Strength": strength
        })

        # update pointer
        last_in_thread[tid] = sid

    return rows
