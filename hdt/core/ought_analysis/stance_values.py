from __future__ import annotations
def analyze(statements, guides=None):
    rows = []
    for i, st in enumerate(statements):
        sid = getattr(st, "id", None) or getattr(st, "statement_id", None) or getattr(st, "Statement_Text_ID", None) or f"S{i+1}"
        rows.append({
            "Statement_Text_ID": sid,
            "Identity_Framework": "unspecified",
            "Perspective_Level": "personal",
            "Group_Referents": "[]",
            "Intergroup_Attitude": "neutral",
            "Empathy_Index": 0.5,
            "Polarization_Level": 0.5,
            "Value_Orientation": "pragmatic",
            "Moral_Priorities": "[]",
            "Ideological_Cluster": "unspecified"
        })
    return rows
