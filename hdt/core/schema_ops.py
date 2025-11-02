from __future__ import annotations
from typing import Any, Dict, List

def _lc(x): return (x or "").strip().lower()

def apply_schema(rows: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Enforces enum sets, defaults, aliases, and basic coercions defined in the schema JSON.
    Supported types: enum, string, int, float, bool, list[string]
    """
    if not rows or not schema: return rows
    rules = {c["name"]: c for c in schema.get("columns", []) if isinstance(c, dict) and "name" in c}
    if not rules: return rows

    def _coerce_bool(val, rule):
        if isinstance(val, bool): return val
        if isinstance(val, (int,float)): return bool(val)
        if isinstance(val, str):
            v = _lc(val)
            if v in ("true","1","yes","y"): return True
            if v in ("false","0","no","n"): return False
        return rule.get("default", False)

    def _coerce_list_str(val, rule):
        if isinstance(val, list): return [str(x) for x in val]
        if isinstance(val, str):
            parts = [s.strip() for s in val.split(",")]
            return [p for p in parts if p]
        if "default" in rule: return rule["default"]
        return []

    for r in rows:
        for col, rule in rules.items():
            typ = rule.get("type", "string")

            if typ == "enum":
                allowed = list(rule.get("allowed", []))
                allowed_lower = [a.lower() for a in allowed]
                aliases = {k.lower(): v for k,v in (rule.get("aliases", {}) or {}).items()}
                default = rule.get("default")
                cur = r.get(col)
                canon = None
                if isinstance(cur, str):
                    lc = _lc(cur)
                    if lc in allowed_lower:
                        canon = next(a for a in allowed if a.lower()==lc)
                    elif lc in aliases:
                        canon = aliases[lc]
                else:
                    if cur in allowed:
                        canon = cur
                if canon is None and default is not None:
                    canon = default
                if canon is not None:
                    r[col] = canon

            elif typ == "bool":
                r[col] = _coerce_bool(r.get(col), rule)

            elif typ == "list[string]":
                r[col] = _coerce_list_str(r.get(col), rule)

            elif typ == "float":
                if r.get(col) is None and "default" in rule: r[col] = rule["default"]

            elif typ == "int":
                if r.get(col) is None and "default" in rule: r[col] = rule["default"]

            elif typ == "string":
                if (r.get(col) is None or r.get(col) == "") and "default" in rule:
                    r[col] = rule["default"]

    return rows
