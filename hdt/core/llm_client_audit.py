from __future__ import annotations
import json, itertools, time
from pathlib import Path
from typing import Any, List, Dict, Optional

class AuditLLMClient:
    _counter = itertools.count(1)
    def __init__(self, base_client: Any, decisions_dir: Path,
                 phase_slug: Optional[str]=None, step_slug: Optional[str]=None,
                 system_prefix: str = ""):
        self._base = base_client
        # decisions_dir/_audit/<phase>/<step>/prompts or decisions_dir/_audit/prompts
        p = Path(decisions_dir)
        if phase_slug and step_slug:
            p = p / phase_slug / step_slug
        self._prompts_dir = p / "prompts"
        self._prompts_dir.mkdir(parents=True, exist_ok=True)
        self._system_prefix = system_prefix.strip()
        self._phase_slug = phase_slug or ""
        self._step_slug  = step_slug  or ""

    def __getattr__(self, name):
        return getattr(self._base, name)

    def _dump(self, api_name: str, kind: str, payload: dict) -> Path:
        idx = next(self._counter)
        slug = self._step_slug or "step"
        fp = self._prompts_dir / f"{slug}_{api_name}_{idx:03d}_{kind}.json"
        fp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return fp

    def complete(self, prompt: str, **kwargs):
        final_prompt = (self._system_prefix + "\n\n" + prompt) if self._system_prefix else prompt
        self._dump("complete", "request", {"prompt": final_prompt, "params": kwargs})
        t0 = time.time()
        resp = self._base.complete(final_prompt, **kwargs)
        self._dump("complete", "response", {"latency_sec": round(time.time()-t0,3), "result": resp})
        return resp

    def chat(self, messages: List[Dict[str, Any]], **kwargs):
        msgs = list(messages)
        if self._system_prefix:
            if not msgs or (msgs[0].get("role") != "system"):
                msgs = [{"role":"system","content": self._system_prefix}] + msgs
            else:
                msgs[0]["content"] = self._system_prefix + "\n\n" + msgs[0].get("content","")
        self._dump("chat", "request", {"messages": msgs, "params": kwargs})
        t0 = time.time()
        resp = self._base.chat(msgs, **kwargs)
        self._dump("chat", "response", {"latency_sec": round(time.time()-t0,3), "result": resp})
        return resp
