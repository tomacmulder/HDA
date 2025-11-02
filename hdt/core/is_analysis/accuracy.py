from __future__ import annotations
from typing import Any, Dict, List, Optional

_DEFAULT_RULES: Dict[str, Any] = {
    "base_scores": {"none": 0.45, "citation": 0.70, "data": 0.85},
    "modality_adjustments": {"interrogative": -0.20, "certain": 0.0, "hedged": -0.05, "counterfactual": -0.30},
    "number_bonus": 0.05,
    "bounds": {"min": 0.05, "max": 0.95},
    "bullshit_index": "1 - Fact_Accuracy",
    "misinfo_threshold": 0.30
}

def get_rules(controls: Optional[Any]=None) -> Dict[str, Any]:
    if controls is None: return _DEFAULT_RULES
    rules = controls.get("guides.accuracy_rules")
    if isinstance(rules, dict): return rules
    return _DEFAULT_RULES

def _clip(x: float, rules: Dict[str, Any]) -> float:
    b = rules["bounds"]
    return max(b["min"], min(b["max"], x))

def _has_number(text: str) -> bool:
    return any(ch.isdigit() for ch in (text or ""))

def score_statements(statements: List[Any], evidential_rows: List[Any], tm_rows: List[Any], controls: Optional[Any]=None) -> List[Dict[str, Any]]:
    rules = get_rules(controls)
    ev_by_id = {r.get("statement_id"): r for r in evidential_rows}
    tm_by_id = {r.get("statement_id"): r for r in tm_rows}
    rows: List[Dict[str, Any]] = []
    for st in statements:
        s = st.model_dump() if hasattr(st, "model_dump") else st
        sid = s.get("id") or s.get("statement_id")
        txt = s.get("text","")
        ev = (ev_by_id.get(sid) or {}).get("Evidential_Basis", "none")
        tm = (tm_by_id.get(sid) or {}).get("Epistemic_Modality", "certain")
        base = rules["base_scores"].get(ev, rules["base_scores"]["none"])
        adj  = rules["modality_adjustments"].get(tm, 0.0)
        score = _clip(base + adj + (rules["number_bonus"] if _has_number(txt) else 0.0), rules)
        out = {
            "statement_id": sid,
            "Fact_Accuracy": round(score, 2),
            "Evidence_Match_Type": "text+features",
            "Bullshit_Index": round(1.0 - score, 2),
            "Accuracy_Notes": f"basis={ev}, force={tm if tm else 'unknown'}, has_number={_has_number(txt)}",
            "Flag_Potential_Misinfo": score <= rules["misinfo_threshold"],
            "Misinformation_Tags": (["low_evidence"] if score <= rules["misinfo_threshold"] else []),
        }
        rows.append(out)
    return rows
# === tolerant adapters (EOF patch) ===
try:
    _HDT_ACC_ORIG_SCORE = score_statements  # type: ignore[name-defined]
except Exception:
    try:
        _HDT_ACC_ORIG_SCORE = score  # sometimes called score(...)
    except Exception:
        _HDT_ACC_ORIG_SCORE = None

def score_statements(statements, evidential, time_modality, controls=None, guides=None):  # tolerant entry
    fn = _HDT_ACC_ORIG_SCORE
    if callable(fn):
        try:
            return fn(statements, evidential, time_modality, controls=controls)
        except TypeError:
            try:
                return fn(statements, evidential, time_modality, guides=guides)
            except TypeError:
                try:
                    return fn(statements, evidential, time_modality)
                except TypeError:
                    pass
    # Fallback: minimal zeros row per statement
    rows = []
    for i, st in enumerate(statements):
        sid = getattr(st, "id", None) or getattr(st, "statement_id", None) or getattr(st, "Statement_Text_ID", None) or f"S{i+1}"
        rows.append({
            "Statement_Text_ID": sid,
            "Fact_Accuracy": 0.0,
            "Evidence_Match_Type": "",
            "Bullshit_Index": 0.0,
            "Accuracy_Notes": "",
            "Flag_Potential_Misinfo": "false",
            "Misinformation_Tags": "",
            "Analytic_Integrity": 0.0
        })
    return rows
