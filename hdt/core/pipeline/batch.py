from __future__ import annotations
from typing import List, Dict, Any, Iterable
from pathlib import Path
import json, glob

from .run import run_all_for_path

def _asdict(x):
    return x.model_dump() if hasattr(x, "model_dump") else x

def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _write_jsonl(path: Path, rows: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            json.dump(_asdict(r), f, ensure_ascii=False)
            f.write("\n")

def _doc_id_from_result(res: Dict[str, Any]) -> str:
    can = res.get("canonical")
    if can is None:
        return "unknown"
    return getattr(can, "doc_id", None) or _asdict(can).get("doc_id", "unknown")

def write_outputs_per_doc(out_dir: Path, res: Dict[str, Any]) -> None:
    """Write a minimal but complete set of artifacts into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "canon.json", _asdict(res["canonical"]))
    for key, fname in [
        ("statements", "statements.jsonl"),
        ("threads", "threads.jsonl"),
        ("links", "links.jsonl"),
        ("modal", "is_time_modality.jsonl"),
        ("evidential", "is_evidential.jsonl"),
        ("causal", "is_causal.jsonl"),
    ]:
        if key in res:
            _write_jsonl(out_dir / fname, res[key])

def _expand_inputs(inputs: List[str]) -> List[str]:
    """Expand directories and globs into concrete file paths (.txt, .md)."""
    paths: List[str] = []
    for a in inputs:
        p = Path(a)
        if p.is_dir():
            paths.extend([str(x) for x in p.glob("*.txt")])
            paths.extend([str(x) for x in p.glob("*.md")])
        elif any(ch in a for ch in "*?[]"):
            paths.extend(glob.glob(a))
        else:
            paths.append(str(p))
    # de-duplicate while preserving order
    seen = set()
    uniq = []
    for x in paths:
        if x not in seen:
            seen.add(x); uniq.append(x)
    return uniq

def run_many(inputs: List[str], out_dir: str = "out") -> List[Dict[str, Any]]:
    """
    Process many inputs (files, dirs, or globs) and write per-document outputs to out/<doc_id>/.
    Returns an index list and writes out/index.json.
    """
    files = _expand_inputs(inputs)
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)

    index: List[Dict[str, Any]] = []
    for inp in files:
        res = run_all_for_path(inp)
        doc_id = _doc_id_from_result(res)
        od = root / doc_id
        write_outputs_per_doc(od, res)
        index.append({"input": str(inp), "doc_id": doc_id, "out_dir": str(od)})

    _write_json(root / "index.json", index)
    return index
