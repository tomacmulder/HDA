from __future__ import annotations
from pathlib import Path
import json, hashlib, datetime as dt

def persist_prompt_policy(out_dir: Path, phase: str, step: str, prompt_text: str) -> None:
    if not prompt_text: return
    d = Path(out_dir) / "_decisions" / "prompts" / phase / step
    d.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    h = hashlib.sha1(prompt_text.encode("utf-8")).hexdigest()
    payload = {"phase": phase, "step": step, "ts": ts, "sha1": h, "prompt": prompt_text}
    (d / "main.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
