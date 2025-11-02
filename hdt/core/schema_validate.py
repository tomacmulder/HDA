from __future__ import annotations
from typing import Any, Dict, List

def validate_rows(rows: List[dict], schema: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if not schema: return {"ok": True, "issues": []}
    cols = schema.get("columns", [])
    want = {c["name"]: c for c in cols if isinstance(c, dict) and "name" in c}
    want_names = set(want.keys())

    for i, r in enumerate(rows or []):
        have = set(r.keys())
        missing = sorted(list(want_names - have))
        extra   = sorted(list(have - want_names))
        enum_bad = []
        for k, rule in want.items():
            if rule.get("type") == "enum" and k in r and r[k] is not None:
                allowed = set(rule.get("allowed", []))
                v = r[k]
                # allow bools represented as strings in schemas that define true/false
                if isinstance(v, bool): v = str(v).lower()
                if allowed and v not in allowed:
                    enum_bad.append({"col": k, "value": v, "allowed": sorted(list(allowed))})
        if missing or extra or enum_bad:
            issues.append({"row": i, "missing": missing, "extra": extra, "enum": enum_bad})
    return {"ok": len(issues) == 0, "issues": issues}
