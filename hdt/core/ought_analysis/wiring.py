from __future__ import annotations
def analyze(ends_means_rows, claims, scm_rows, guides=None):
    rows = []
    for em in (ends_means_rows or []):
        rows.append({
            "Statement_Text_ID": (em or {}).get("Statement_Text_ID"),
            "Normative_Links": "[]",
            "EndsMeans_Balance": 0.5,
            "Proportionality_Type": "unspecified",
            "Harm_Benefit_Profile": "",
            "Rights_Constraint": "[]"
        })
    return rows
