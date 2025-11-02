from pathlib import Path
import orjson
from hdt.core.pipeline.run import run_all_for_path
from hdt.core.llm_client import LLMClient

# 1) Run existing structure pass
doc = r"data\ingest\INPUT.md"
res = run_all_for_path(doc)
statements = res["statements"]

# 2) Structured-output schema (every object sets additionalProperties: False)
schema = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "claims": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["text_span", "char_start", "char_end", "claim_type"],
        "properties": {
          "text_span":   {"type": "string"},
          "char_start":  {"type": "integer", "minimum": 0},
          "char_end":    {"type": "integer", "minimum": 0},
          "claim_type":  {"type": "string", "enum": [
              "descriptive","predictive","causal","counterfactual",
              "definition_taxonomy","attribution","self_report"
          ]}
        }
      }
    }
  },
  "required": ["claims"]
}

SYSTEM = (
  "Extract zero or more extractive IS claims as substrings of the text.\n"
  "Return STRICT JSON only, matching the schema. If none, return claims=[].\n"
  "Offsets are character indexes into the provided Text, Python-slice style."
)

def do_claims(s, llm):
    data = llm.json_structured(SYSTEM, f"Text:\\n{s['text']}", schema)
    out = []
    for i, c in enumerate(data.get("claims", []), 1):
        # defensive: keep only exact substrings
        span = s["text"][c["char_start"]:c["char_end"]]
        if span == c["text_span"]:
            out.append({
                "statement_id": s["id"],
                "claim_id": f"{s['id']}_C{i}",
                **c
            })
    return out

llm = LLMClient()  # model can be overridden via HDT_LLM_MODEL
claims = []
for st in statements:
    s = st.model_dump() if hasattr(st, "model_dump") else st
    claims.extend(do_claims(s, llm))

out = Path("out"); out.mkdir(exist_ok=True)
(out / "claims_is.jsonl").write_bytes(b"\\n".join(orjson.dumps(c) for c in claims))
print(f"Wrote {len(claims)} → out/claims_is.jsonl")
