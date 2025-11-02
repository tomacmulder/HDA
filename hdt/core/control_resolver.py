from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json, hashlib

def _read_json(p: Path):
    if not p.exists(): return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        raw = p.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"): raw = raw[3:]
        return json.loads(raw.decode("utf-8"))

def _sha1(p: Path) -> str:
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(131072), b""):
            h.update(chunk)
    return h.hexdigest()

class _OneLevel:
    def __init__(self, base: Path):
        self.base = base
        self.schemas: Dict[str, Any] = {}
        self.guides:  Dict[str, Any] = {}
        self.prompts: Dict[str, str] = {}
        self.fps: List[Dict[str, Any]] = []
        self._load()

    def _load_dir(self, rel: str, exts: Tuple[str,...]) -> List[Path]:
        d = self.base / rel
        return [p for p in d.iterdir()] if d.exists() else []

    def _load(self):
        for p in self._load_dir("schemas", (".json",)):
            if p.suffix.lower() != ".json": continue
            self.schemas[p.stem] = _read_json(p) or {}
            self.fps.append({"kind":"schema","name":p.stem,"path":str(p),"size":p.stat().st_size,"sha1":_sha1(p)})
        for p in self._load_dir("guides", (".json",)):
            if p.suffix.lower() != ".json": continue
            self.guides[p.stem] = _read_json(p) or {}
            self.fps.append({"kind":"guide","name":p.stem,"path":str(p),"size":p.stat().st_size,"sha1":_sha1(p)})
        for p in self._load_dir("prompts", (".md",)):
            if p.suffix.lower() != ".md": continue
            self.prompts[p.stem] = p.read_text(encoding="utf-8", errors="ignore")
            self.fps.append({"kind":"prompt","name":p.stem,"path":str(p),"size":p.stat().st_size,"sha1":_sha1(p)})

class ControlResolver:
    """ Resolves controls with precedence: step -> global """
    def __init__(self, global_base: str | Path = "config"):
        self.global_level = _OneLevel(Path(global_base))
    def for_step(self, phase: str, step: str):
        step_dir = Path("config") / "phases" / phase / "steps" / step
        return ControlStack(_OneLevel(step_dir), self.global_level)

class ControlStack:
    def __init__(self, top: _OneLevel, bottom: _OneLevel):
        self.top = top
        self.bottom = bottom

    @property
    def fingerprints(self) -> List[Dict[str, Any]]:
        return self.top.fps + self.bottom.fps

    def _get(self, kind: str, name: str, default=None):
        top_map = getattr(self.top, kind, {})
        bot_map = getattr(self.bottom, kind, {})
        if name in top_map: return top_map[name]
        if name in bot_map: return bot_map[name]
        return default

    def get_schema(self, name: str, default=None): return self._get("schemas", name, default)
    def get_guide(self,  name: str, default=None): return self._get("guides",  name, default)
    def get_prompt(self, name: str, default=""):   return self._get("prompts", name, default)

    # NEW: dotted-path convenience to maintain backward compatibility
    def get(self, dotted: str, default=None):
        try:
            kind, name = dotted.split(".", 1)
        except ValueError:
            return default
        if kind == "schemas": return self.get_schema(name, default)
        if kind == "guides":  return self.get_guide(name,  default)
        if kind == "prompts": return self.get_prompt(name, default if isinstance(default, str) else "")
        return default
