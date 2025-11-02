from __future__ import annotations
def analyze(analytic_integrity_rows, stance_rows, prag_rows, guides=None):
    rows = []
    by_stmt = { (r or {}).get("Statement_Text_ID"): (r or {}) for r in (analytic_integrity_rows or []) }
    for sr in (stance_rows or []):
        sid = (sr or {}).get("Statement_Text_ID")
        ai  = float(by_stmt.get(sid, {}).get("Analytic_Integrity", 0.0))
        rel = float((sr or {}).get("Empathy_Index", 0.5))
        tr  = 0.5  # proxy
        overall = round(0.4*ai + 0.3*rel + 0.3*tr, 2)
        rows.append({
            "Statement_Text_ID": sid,
            "Relational_Integrity": round(rel, 2),
            "Transformative_Integrity": round(tr, 2),
            "Overall_Integrity_Score": overall,
            "Dominant_Dimension": "Analytic" if ai >= max(rel, tr) else ("Relational" if rel >= tr else "Transformative"),
            "Malice_Vector": '{"Analytic_Malice": ' + str(round(1-ai,2)) + ', "Relational_Malice": ' + str(round(1-rel,2)) + ', "Transformative_Malice": ' + str(round(1-tr,2)) + '}'
        })
    return rows
