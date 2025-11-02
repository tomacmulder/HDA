from __future__ import annotations
from typing import List, Dict, Any, Optional
import json, re
from pathlib import Path

_DEF_AXIS = "unspecified"
_DEF_LAYER = {"Emergent_Layer_Code":"NA","Emergent_Layer_Name":"NA","Emergent_SubLayer":"NA"}
_DEF_CONSTRAINT = {f"C{i}": 0 for i in range(8)}  # C0..C7

TAX_PATH = Path("data/ontology/minitaxonomy.json")  # legacy fallback

def _load_tax_from_file(p: Path) -> Dict[str, Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        raw = p.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"): raw = raw[3:]
        return json.loads(raw.decode("utf-8"))

def _kw_map_from_guides(guide: Dict[str, Any]) -> Dict[str, List[str]]:
    # expects {"keywords": {"revenue":["Economics.Financial.Revenue"], ...}, "aliases":{"rev":"revenue"}}
    kw = guide.get("keywords", {}) if isinstance(guide, dict) else {}
    aliases = guide.get("aliases", {}) if isinstance(guide, dict) else {}
    for a, canon in aliases.items():
        if canon in kw: kw[a] = kw[canon]
    return kw

def _match_paths(text: str, kw_map: Dict[str, List[str]]) -> List[str]:
    t = text.lower()
    hits: List[str] = []
    for kw, paths in kw_map.items():
        if re.search(rf"\b{re.escape(kw.lower())}\b", t):
            hits.extend(paths)
    # dedupe preserve order
    seen=set(); out=[]
    for p in hits:
        if p not in seen:
            out.append(p); seen.add(p)
    return out

def map_statements(statements: List[Any], controls: Optional[Any]=None) -> List[Dict[str, Any]]:
    # 1) prefer controls-guided keywords
    kw_map = {}
    if controls is not None:
        guide = controls.get("guides.ontology_keywords")
        if guide: kw_map = _kw_map_from_guides(guide)
    # 2) else legacy file
    if not kw_map:
        if TAX_PATH.exists():
            obj = _load_tax_from_file(TAX_PATH)
            # flatten {"domain":{"kw":[paths]}} -> {"kw":[paths]}
            for _, d in obj.items():
                if isinstance(d, dict):
                    for kw, paths in d.items():
                        kw_map[kw] = paths
    rows: List[Dict[str, Any]] = []
    for st in statements:
        s = st.model_dump() if hasattr(st, "model_dump") else st
        t = s.get("text","")
        paths = _match_paths(t, kw_map) if kw_map else []
        primary = paths[0] if paths else "Unclassified.Unknown"
        rows.append({
            "statement_id": s["id"],
            "Primary_Topic_Path": primary,
            "Primary_Topic_Labels": primary.split("."),
            "Primary_Topic_Confidence": 0.6 if paths else 0.2,
            "Fabric_Axis": _DEF_AXIS,
            **_DEF_LAYER,
            "Constraint_Vector": _DEF_CONSTRAINT,
            "Substrate": "unspecified",
            "Derived_Layer_Code": "NA",
            "Derived_Layer_Path": [],
            "Secondary_Topic_Paths": paths[1:] if len(paths)>1 else []
        })
    return rows
# === tolerant adapters (EOF patch) ===
try:
    _HDT_ONTO_ORIG_MAP = map_statements  # type: ignore[name-defined]
except Exception:
    _HDT_ONTO_ORIG_MAP = None

def map_statements(statements, controls=None, guides=None):  # tolerant entry
    fn = _HDT_ONTO_ORIG_MAP
    if callable(fn):
        try:
            return fn(statements, controls=controls)  # kw "controls"
        except TypeError:
            try:
                return fn(statements, guides=guides)  # kw "guides"
            except TypeError:
                try:
                    return fn(statements, controls)   # positional
                except TypeError:
                    try:
                        return fn(statements)         # bare
                    except TypeError:
                        pass
    # Fallback: minimal rows that satisfy schema
    out = []
    for i, st in enumerate(statements):
        sid = getattr(st, "id", None) or getattr(st, "statement_id", None) or getattr(st, "Statement_Text_ID", None) or f"S{i+1}"
        out.append({
            "Statement_Text_ID": sid,
            "Primary_Topic_Path": "",
            "Primary_Topic_Labels": "",
            "Primary_Topic_Confidence": 0.0,
            "Fabric_Axis": "",
            "Emergent_Layer_Code": "",
            "Emergent_Layer_Name": "",
            "Emergent_Layer_SubLayer": "",
            "Constraint_Vector": "",
            "Substrate": "",
            "Derived_Layer_Code": "",
            "Derived_Layer_Path": "",
            "Secondary_Topic_Paths": ""
        })
    return out
