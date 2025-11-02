from __future__ import annotations
from typing import List, Dict, Any
import re

# Very conservative, deterministic cues. We can refine later.
_FUTURE   = re.compile(r"\b(will|shall|going to|gonna|soon|tomorrow|next\s+(week|month|year))\b", re.I)
_PAST     = re.compile(r"\b(yesterday|last\s+(week|month|year)|ago|formerly|previously|was|were|did|had)\b", re.I)
_COUNTERF = re.compile(r"\b(would have|could have|should have|had\s+\w+ed\s+if|if\s+.*\bwould\b)\b", re.I)
_QMARK    = re.compile(r"\?\s*$")
_HEDGES   = re.compile(r"\b(might|may|could|possibly|perhaps|likely|unlikely|appears|seems)\b", re.I)
_UNIV     = re.compile(r"\b(all|every|always|none)\b", re.I)
_LOCAL    = re.compile(r"\b(most|many|often|usually|frequently|generally)\b", re.I)
_INDIV    = re.compile(r"\b(i|you|he|she|they|we|this|that)\b", re.I)

def _axis(text: str) -> str:
    if _FUTURE.search(text): return "future"
    if _PAST.search(text):   return "past"
    return "present"

def _tense_signal(text: str) -> str:
    if _COUNTERF.search(text): return "counterfactual"
    if _FUTURE.search(text):   return "future"
    if _PAST.search(text):     return "past_reference"
    return "present_trend"

def _epi_modality(text: str) -> str:
    if _COUNTERF.search(text): return "counterfactual"
    if _QMARK.search(text):    return "interrogative"
    if _HEDGES.search(text):   return "hedged"
    return "certain"

def _epi_force(text: str) -> str:
    if _COUNTERF.search(text): return "weak"
    if _QMARK.search(text):    return "weak"
    if _HEDGES.search(text):   return "moderate"
    return "strong"

def _scope(text: str) -> str:
    if _UNIV.search(text):  return "universal"
    if _LOCAL.search(text): return "general"
    if _INDIV.search(text): return "individual"
    return "unspecified"

def analyze(statements: List[Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for st in statements:
        s = st.model_dump() if hasattr(st, "model_dump") else st
        t = s.get("text", "")
        rows.append({
            "statement_id": s["id"],
            "Time_Axis": _axis(t),
            "Temporal_Horizon": "none",  # placeholder, add horizon heuristics later
            "Change_Tense_Signal": _tense_signal(t),
            "Epistemic_Modality": _epi_modality(t),
            "Epistemic_Force": _epi_force(t),
            "Scope_Type": _scope(t),
        })
    return rows
# --- compatibility alias for callers expecting analyze_time_modality ---
def analyze_time_modality(statements):
    return analyze(statements)
# --- compat shim: legacy callers expect analyze_time_modality(...)
def analyze_time_modality(statements, guides=None):
    return analyze(statements, guides=guides)
# --- robust shim (overrides any earlier one) ---
def analyze_time_modality(statements, guides=None):
    """
    Call the module's analyze(...) regardless of its signature.
    Tries (statements, guides=...), then (statements, guides), then (statements).
    """
    try:
        return analyze(statements, guides=guides)  # keyword
    except TypeError:
        try:
            return analyze(statements, guides)     # positional
        except TypeError:
            return analyze(statements)             # bare
# === tolerant adapters (EOF patch) ===
# Capture original analyze if present
try:
    _HDT_TM_ORIG_ANALYZE = analyze  # type: ignore[name-defined]
except Exception:
    _HDT_TM_ORIG_ANALYZE = None

def _hdt_tm_call(statements, guides=None):
    fn = _HDT_TM_ORIG_ANALYZE
    if callable(fn):
        try:
            return fn(statements, guides=guides)   # keyword
        except TypeError:
            try:
                return fn(statements, guides)      # positional
            except TypeError:
                return fn(statements)              # bare
    return []

def analyze_time_modality(statements, guides=None):  # tolerant entry
    return _hdt_tm_call(statements, guides)

# Also expose a tolerant "analyze" so callers importing analyze(...) work too
def analyze(statements, guides=None):  # type: ignore[override]
    return _hdt_tm_call(statements, guides)
