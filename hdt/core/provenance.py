from __future__ import annotations
from pathlib import Path
import hashlib, datetime as dt

def _to_dict(x):
    if isinstance(x, dict): return x
    for a in ("model_dump","dict"):
        fn = getattr(x, a, None)
        if callable(fn):
            try:
                d = fn()
                if isinstance(d, dict): return d
            except Exception: pass
    return {}

def _round01(x, nd=2):
    try:
        v = float(x)
    except Exception:
        return 0.0
    if v < 0: v = 0.0
    if v > 1: v = 1.0
    return round(v, nd)

def file_sha256(p: str|Path) -> str:
    p = Path(p)
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def stamp_rows(rows, panel: dict, source_path: str|Path, step_name: str, step_version: str="v1"):
    rows = rows or []
    p = panel or {}
    io = p.get("io", {})
    provd = p.get("provenance_defaults", {})
    lang   = io.get("lang", "auto")
    script = io.get("script", "auto")
    span_indexing = io.get("span_indexing", "unicode_codepoint")
    annotator       = provd.get("Annotator", "model")
    annotator_id    = provd.get("Annotator_ID", "HDT.default")
    annotator_conf  = _round01(provd.get("Annotator_Confidence", 0.5))
    review_status   = provd.get("Review_Status", "unreviewed")
    sv              = str(provd.get("Schema_Version", "1.1"))
    src = Path(source_path)
    ts  = dt.datetime.now(dt.timezone.utc).isoformat()
    sha = file_sha256(source_path) if Path(source_path).exists() else ""
    steps = [{"name": step_name, "version": step_version}]
    out = []
    for r in rows:
        d = _to_dict(r)
        d["Schema_Version"] = sv
        d["Lang"] = lang if lang != "auto" else d.get("Lang","unknown")
        d["Script"] = script if script != "auto" else d.get("Script","unknown")
        d["Span_Indexing"] = span_indexing
        d["Annotator"] = annotator
        d["Annotator_ID"] = annotator_id
        d["Annotator_Confidence"] = annotator_conf
        d["Review_Status"] = review_status
        d["Provenance"] = {
            "Source_ID": src.name,
            "Source_Kind": "file",
            "Ingested_At_ISO": ts,
            "Pipeline_Steps": steps,
            "Hash_SHA256": sha
        }
        out.append(d)
    return out
