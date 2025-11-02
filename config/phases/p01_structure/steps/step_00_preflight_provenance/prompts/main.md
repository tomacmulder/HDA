Role/Goal: Perform the step exactly as specified; return strict JSON only.
Inputs: See step controls; do not mutate text content.
Controlled Vocab: Use enums from the schema and guides exactly.
Decision Guide: Follow priority rules, clamp floats [0,1], round 2 decimals.
Edge Cases: If span cannot be indexed, set Char_Start=Char_End=-1 and note SPAN_NOINDEX in a local notes key (not emitted).
Validation: One row per required unit; IDs must resolve; Thread_IDs contiguous.
Confidence: Calibrate per guide; default 0.50 if uncertain.
Idempotency: Sort by Statement_Text_ID then Char_Start; ID format per spec.
Return: STRICT JSON LINES conforming to schema — no explanations.
