from __future__ import annotations
def analyze(statements, guides=None):
    rows = []
    for i, st in enumerate(statements):
        sid = getattr(st, "id", None) or getattr(st, "statement_id", None) or getattr(st, "Statement_Text_ID", None) or f"S{i+1}"
        rows.append({
            "Statement_Text_ID": sid,
            "Rhetorical_Function": "prescriptive",
            "Speech_Act_Type": "directive",
            "Deontic_Strength": 0.3,
            "Consensus_Friction": "medium",
            "Illocution_Force": ""
        })
    return rows
