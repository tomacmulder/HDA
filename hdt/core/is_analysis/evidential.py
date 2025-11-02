from __future__ import annotations
from typing import List, Dict, Any
import re

# Simple lexicon-based cues; deterministic and explainable
_TESTIMONIAL = re.compile(r"\b(according to|reported by|says|said|told|per\s+\w+)\b", re.I)
_EMPIRICAL   = re.compile(r"\b(data|evidence|measured|observed|survey|dataset|study|trial|experiment|statistic)\b|\d+(\.\d+)?\s*%|\b\d{4}\b", re.I)
_INFERENTIAL = re.compile(r"\b(therefore|thus|hence|implies|suggests|indicates)\b", re.I)
_THEORETICAL = re.compile(r"\b(theory|model|axiom|hypothesis)\b", re.I)
_ANECDOTAL   = re.compile(r"\b(i think|i believe|in my opinion|from experience)\b", re.I)
_SPECULATIVE = re.compile(r"\b(maybe|perhaps|could|might|possible|possibly|rumor|speculation)\b", re.I)

def _pick(text: str) -> str:
    if _EMPIRICAL.search(text):   return "empirical"
    if _TESTIMONIAL.search(text): return "testimonial"
    if _INFERENTIAL.search(text): return "inferential"
    if _THEORETICAL.search(text): return "theoretical"
    if _ANECDOTAL.search(text):   return "anecdotal"
    if _SPECULATIVE.search(text): return "speculative"
    return "none"

def assign(statements: List[Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for st in statements:
        s = st.model_dump() if hasattr(st, "model_dump") else st
        t = s.get("text","")
        rows.append({
            "statement_id": s["id"],
            "Evidential_Basis": _pick(t),
        })
    return rows
# --- compatibility alias for callers expecting assign_evidential ---
def assign_evidential(statements):
    return assign(statements)
# --- compatibility alias for callers expecting classify_evidence ---
def classify_evidence(statements):
    return assign(statements)
# === tolerant adapters (EOF patch) ===
try:
    _HDT_EV_ORIG_ASSIGN = assign  # type: ignore[name-defined]
except Exception:
    try:
        _HDT_EV_ORIG_ASSIGN = analyze  # some modules export analyze(...)
    except Exception:
        _HDT_EV_ORIG_ASSIGN = None

def _hdt_ev_call(statements, guides=None):
    fn = _HDT_EV_ORIG_ASSIGN
    if callable(fn):
        try:
            return fn(statements, guides=guides)   # keyword
        except TypeError:
            try:
                return fn(statements, guides)      # positional
            except TypeError:
                try:
                    return fn(statements)          # bare
                except TypeError:
                    pass
    # Fallback: emit "none" evidentials per statement
    rows = []
    for i, st in enumerate(statements):
        sid = getattr(st, "id", None) or getattr(st, "statement_id", None) or getattr(st, "Statement_Text_ID", None) or f"S{i+1}"
        rows.append({"Statement_Text_ID": sid, "Evidential_Basis": "none"})
    return rows

def assign(statements, guides=None):  # tolerant entry
    return _hdt_ev_call(statements, guides)
