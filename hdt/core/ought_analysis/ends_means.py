from __future__ import annotations
def analyze(deontic_rows, statements, guides=None):
    rows = []
    for i, dr in enumerate(deontic_rows or []):
        sid = (dr or {}).get("Statement_Text_ID")
        rows.append({
            "Statement_Text_ID": sid,
            "End_State_Label": "",
            "Value_Kind": "prudential",
            "End_Scope": "individual",
            "Priority_Rank": 1,
            "Instrumental_Action_Schema": "",
            "Agent_Role": "unspecified",
            "Means_Cost_Risk_Hint": "low",
            "Feasibility_Cue": "none",
            "Value_Theory": "unspecified",
            "Sacred_Value": "false",
            "Tradeoff_Acceptance": "unknown"
        })
    return rows
