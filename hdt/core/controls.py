from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json, hashlib

def _read_json(p: Path) -> Any:
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

class ControlRegistry:
    """
    Loads JSON controls from:
      config/schemas/*.json   -> column definitions & enums per artifact
      config/guides/*.json    -> taxonomies/rules/aliases/etc
      config/prompts/*.md     -> optional step templates (used as system prefix)
    """
    def __init__(self, base: str | Path = "config"):
        self.base = Path(base)
        self.schemas: Dict[str, Any] = {}
        self.guides:  Dict[str, Any] = {}
        self.prompts: Dict[str, str] = {}
        self.fingerprints: List[Dict[str, Any]] = []
        self._load()

    def _load_dir(self, rel: str, accept_ext: Tuple[str,...]) -> List[Path]:
        d = self.base / rel
        if not d.exists(): return []
        return [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in accept_ext]

    def _load(self) -> None:
        # Schemas (*.json)
        for p in self._load_dir("schemas", (".json",)):
            key = p.stem
            self.schemas[key] = _read_json(p) or {}
            self.fingerprints.append({"kind":"schema","name":key,"path":str(p),"size":p.stat().st_size,"sha1":_sha1(p)})
        # Guides (*.json)
        for p in self._load_dir("guides", (".json",)):
            key = p.stem
            self.guides[key] = _read_json(p) or {}
            self.fingerprints.append({"kind":"guide","name":key,"path":str(p),"size":p.stat().st_size,"sha1":_sha1(p)})
        # Prompts (*.md)
        for p in self._load_dir("prompts", (".md",)):
            key = p.stem
            self.prompts[key] = p.read_text(encoding="utf-8", errors="ignore")
            self.fingerprints.append({"kind":"prompt","name":key,"path":str(p),"size":p.stat().st_size,"sha1":_sha1(p)})

    def get(self, path: str, default: Any=None) -> Any:
        """
        dotted path: 'schemas.time_modality' or 'guides.ontology_keywords'
        """
        root = {"schemas": self.schemas, "guides": self.guides, "prompts": self.prompts}
        cur: Any = root
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur: cur = cur[part]
            else: return default
        return cur

    def render_catalog_md(self) -> str:
        out = ["# Controls Catalog (schemas)\n"]
        for name, sch in sorted(self.schemas.items()):
            out.append(f"## {name}")
            file_name = sch.get("file", "")
            if file_name: out.append(f"- **Artifact**: `{file_name}`")
            cols = sch.get("columns", [])
            if cols:
                out.append("\n| Column | Type | Allowed | Default | Description |\n|---|---|---|---|---|")
                for c in cols:
                    allowed = ", ".join(c.get("allowed", [])) if c.get("type") == "enum" else ""
                    desc = (c.get("description") or "").replace("|","\\|")
                    out.append(f"| {c.get('name')} | {c.get('type','string')} | {allowed} | {c.get('default','')} | {desc} |")
            out.append("")
        return "\n".join(out)
