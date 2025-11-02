from __future__ import annotations
from typing import List, Dict, Any

SYSTEM = (
    "You are an extraction model. "
    "Return STRICT JSON matching the provided JSON Schema. "
    "Task: Extract zero or more IS-claims as exact substrings of the input text. "
    "Only return spans that appear verbatim in the text with correct char_start/char_end. "
    "Prefer propositions (descriptive, predictive, causal, definition, attribution). "
    "Do NOT paraphrase. If nothing extractable, return an empty array."
)

def _schema() -> Dict[str, Any]:
    return {
        "type":"object",
        "additionalProperties": False,
        "properties":{
            "claims":{
                "type":"array",
                "items":{
                    "type":"object",
                    "additionalProperties": False,
                    "required":["text_span","char_start","char_end","claim_type"],
                    "properties":{
                        "text_span":{"type":"string"},
                        "char_start":{"type":"integer","minimum":0},
                        "char_end":{"type":"integer","minimum":0},
                        "claim_type":{"type":"string"}
                    }
                }
            }
        },
        "required":["claims"]
    }

_TERMINAL_PUNCT = {".","!","…"}
def _seems_declarative(t: str) -> bool:
    tt = t.strip()
    return (len(tt) > 2) and (tt[-1] in _TERMINAL_PUNCT) and ("?" not in tt)

def extract_claims_llm(statements: List[Any], llm, use_fallback: bool=True) -> List[Dict[str, Any]]:
    """
    LLM-first extractive claims. If none returned and the statement looks declarative,
    optionally fall back to taking the WHOLE sentence as a single descriptive claim.
    """
    out: List[Dict[str, Any]] = []
    schema = _schema()
    for st in statements:
        s = st.model_dump() if hasattr(st, "model_dump") else st
        text = s.get("text","")
        data = llm.json_structured(SYSTEM, f"Text:\\n{text}", schema)
        kept = 0
        for i, c in enumerate(data.get("claims", []), 1):
            start, end = int(c["char_start"]), int(c["char_end"])
            if 0 <= start <= end <= len(text):
                span = text[start:end]
                if span == c["text_span"]:
                    out.append({
                        "statement_id": s["id"],
                        "claim_id": f"{s['id']}_C{i}",
                        "text_span": span,
                        "char_start": start,
                        "char_end": end,
                        "claim_type": c["claim_type"],
                    })
                    kept += 1
        # Deterministic fallback for visibility
        if kept == 0 and use_fallback and _seems_declarative(text):
            out.append({
                "statement_id": s["id"],
                "claim_id": f"{s['id']}_C1",
                "text_span": text,
                "char_start": 0,
                "char_end": len(text),
                "claim_type": "descriptive",
                "fallback": True
            })
    return out
