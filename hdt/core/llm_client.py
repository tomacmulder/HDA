from __future__ import annotations
from typing import Any, Dict, Optional
import os, orjson
from openai import OpenAI

# Default model per tier; can be overridden via env:
#   HDT_LLM_BEST, HDT_LLM_BALANCED, HDT_LLM_FRUGAL
_DEF_MODEL_BY_TIER = {
    "best":     os.getenv("HDT_LLM_BEST",     "gpt-4.1"),       # highest quality
    "balanced": os.getenv("HDT_LLM_BALANCED", "gpt-4.1-mini"),  # quality/cost balance
    "frugal":   os.getenv("HDT_LLM_FRUGAL",   "gpt-4o-mini"),   # very low cost
}

def _pick_model(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    tier = (os.getenv("HDT_LLM_TIER") or "best").lower()
    return _DEF_MODEL_BY_TIER.get(tier, _DEF_MODEL_BY_TIER["best"])

def _get_key() -> str:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("HDT_OPENAI_KEY") or ""
    if not key or key.startswith("<") or "NEW-KEY" in key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing or looks like a placeholder. "
            "Set a real key (env OPENAI_API_KEY) and retry."
        )
    return key

class LLMClient:
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        max_output_tokens: int = int(os.getenv("HDT_MAX_OUTPUT_TOKENS", "2000")),
    ):
        self.model = _pick_model(model)
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key or _get_key())
        self.max_output_tokens = max_output_tokens

    def json_structured(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return a dict validated by OpenAI structured outputs using Chat Completions.
        Uses response_format={type:'json_schema', ...}. Falls back to JSON parsing.
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "hdt_schema", "schema": schema, "strict": True},
            },
            max_tokens=self.max_output_tokens,
        )
        msg = resp.choices[0].message
        parsed = getattr(msg, "parsed", None)
        if parsed is not None:
            return parsed
        content = msg.content or "{}"
        try:
            return orjson.loads(content)
        except Exception as e:
            raise RuntimeError(f"Expected JSON but got: {content!r}") from e
