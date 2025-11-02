from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, Iterable
import re

__all__ = ["form_threads"]

def _tokset(s: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))

def _jaccard(a: set, b: set) -> float:
    if not a or not b: return 0.0
    inter = len(a & b); union = len(a | b)
    return inter / union if union else 0.0

def _coerce_dict(obj: Any) -> Dict[str, Any]:
    """Best-effort to view obj as a dict (supports Pydantic v1/v2 and plain dict)."""
    if isinstance(obj, dict):
        return obj
    for attr in ("model_dump", "dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                d = fn()
                if isinstance(d, dict):
                    return d
            except Exception:
                pass
    # Fallback: attempt attribute harvest for common fields
    d: Dict[str, Any] = {}
    for k in ("id","statement_id","sid","Statement_Text_ID",
              "text","raw","content","Statement_Text"):
        if hasattr(obj, k):
            d[k] = getattr(obj, k)
    return d

def _first(d: Dict[str, Any], keys: Iterable[str], default=None):
    for k in keys:
        v = d.get(k, None)
        if v is not None and v != "":
            return v
    return default

def _score_anchor(text: str, g: Dict[str, Any]) -> Tuple[float, str]:
    w = g.get("weights", {})
    length_min = int(g.get("length_min", 60))
    phatic = set(x.lower() for x in g.get("phatic_markers", []))
    claimy = set(x.lower() for x in g.get("claimy_markers", []))
    qmarks = g.get("question_markers", ["?"])

    t = (text or "").strip()
    tl = t.lower()
    score = 0.0
    role_hint = None

    if any(q in t for q in qmarks):
        score += float(w.get("question_mark", 0.35))
        role_hint = "question"

    if len(t) >= length_min:
        score += float(w.get("long_text", 0.2))

    if any(k in tl for k in claimy):
        score += float(w.get("claimy_terms", 0.25))

    if any(re.search(rf"\b{re.escape(p)}\b", tl) for p in phatic):
        score += float(w.get("phatic_penalty", -0.4))

    # clamp
    score = max(0.0, min(1.0, score))
    return score, (role_hint or "anchor")

def form_threads(statements: List[Dict[str, Any]], guides: Optional[Dict[str, Any]]=None) -> List[Dict[str, Any]]:
    """
    Deterministic threader:
    - Starts T1 at first anchor; starts new T when anchor score >= threshold or similarity to last anchor < threshold.
    - Roles: question/answer if interrogative pair, else anchor/reply.
    Output rows match schema: Statement_Text_ID, Thread_ID, Thread_Role, Anchor_Eligibility_Score
    """
    g = guides or {}
    thr = float(g.get("anchor_threshold", 0.5))
    sim_thr = float(g.get("new_thread_similarity_threshold", 0.20))

    rows: List[Dict[str, Any]] = []
    cur_tid_idx = 0
    last_anchor_vec: Optional[set] = None
    last_role: Optional[str] = None

    def _next_tid() -> str:
        nonlocal cur_tid_idx
        cur_tid_idx += 1
        return f"T{cur_tid_idx}"

    cur_tid = None

    for i, st in enumerate(statements):
        d = _coerce_dict(st)
        sid = _first(d, ("id","statement_id","sid","Statement_Text_ID"), default=f"S{i+1}")
        txt = _first(d, ("text","raw","content","Statement_Text"), default="")

        score, role_hint = _score_anchor(txt, g)
        vec = _tokset(txt)

        start_new = (score >= thr)
        if last_anchor_vec is not None:
            sim = _jaccard(vec, last_anchor_vec)
            if sim < sim_thr:
                start_new = True

        if start_new or cur_tid is None:
            cur_tid = _next_tid()
            role = role_hint if role_hint == "question" else "anchor"
            last_anchor_vec = vec
        else:
            role = "answer" if (last_role == "question" and "?" not in txt) else "reply"

        last_role = role

        rows.append({
            "Statement_Text_ID": sid,
            "Thread_ID": cur_tid,
            "Thread_Role": role,
            "Anchor_Eligibility_Score": round(float(score), 3)
        })

    return rows
