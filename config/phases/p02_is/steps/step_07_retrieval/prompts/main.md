Role/Goal: Perform the IS step contract; return strict JSON only.
Inputs: Prior tables as specified; read-only.
Controlled Vocab: Use enums; clamp floats [0,1], round 2 decimals.
Decision Guide: Deterministic order: Statement_Text_ID then Char_Start.
Edge Cases/Fallbacks: Emit defaults when evidence absent.
Validation: One row per required unit; references must resolve; no self loops.
Confidence: Calibrate per rubric; default 0.50.
Idempotency: Stable IDs Claim_ID=S#_C#, Path_ID=Claim_ID_P{index}.
Return: JSONL conforming to schema.
