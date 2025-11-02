from __future__ import annotations
def analyze(statements, guides=None):
    rows = []
    for i, st in enumerate(statements):
        sid = getattr(st, "id", None) or getattr(st, "statement_id", None) or getattr(st, "Statement_Text_ID", None) or f"S{i+1}"
        rows.append({
            "Statement_Text_ID": sid,
            "Deontic_Modality": "P",
            "Direction_Of_Fit": "word->world",  # ASCII to avoid console encoding on Windows
            "Norm_Component": "means",
            "Target_Ref": "statement",
            "Norm_System": "unspecified",
            "Agent_STIT": "",
            "Violation_Status": "none"
        })
    return rows
