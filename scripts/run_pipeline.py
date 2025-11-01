#!/usr/bin/env python
from __future__ import annotations
import argparse, json, pathlib, sys

try:
    import orjson as _json
    def dumps(obj): return _json.dumps(obj).decode("utf-8")
except Exception:
    def dumps(obj): return json.dumps(obj, ensure_ascii=False)

from hdt.core.pipeline.run import run_all_for_path
from adapters.core_to_chart import to_bubble_chart

def _write_json(path: pathlib.Path, obj):
    path.write_text(dumps(obj), encoding="utf-8")

def _write_jsonl(path: pathlib.Path, seq):
    with path.open("w", encoding="utf-8") as f:
        for item in seq:
            # Prefer Pydantic model_dump if present
            if hasattr(item, "model_dump"):
                f.write(dumps(item.model_dump()) + "\n")
            else:
                try:
                    f.write(dumps(item) + "\n")
                except TypeError:
                    # Fallback for pydantic v1-like: .dict()
                    f.write(dumps(item.dict()) + "\n")

def main():
    p = argparse.ArgumentParser(description="Run HDA v2 pipeline on a file")
    p.add_argument("path", help="Input file (.txt/.md/.srt)")
    p.add_argument("--encoding", default="utf-8")
    p.add_argument("--out", default="out", help="Output folder")
    args = p.parse_args()

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = run_all_for_path(args.path, encoding=args.encoding)

    # Canonical doc
    canon = results["canonical"]
    if hasattr(canon, "model_dump"):
        _write_json(out_dir / "canon.json", canon.model_dump())
    else:
        _write_json(out_dir / "canon.json", canon.dict())

    # Rows
    _write_jsonl(out_dir / "statements.jsonl", results["statements"])
    _write_jsonl(out_dir / "threads.jsonl", results["threads"])
    _write_jsonl(out_dir / "links.jsonl", results["links"])
    _write_jsonl(out_dir / "is_time_modality.jsonl", results["modal"])
    _write_jsonl(out_dir / "is_evidential.jsonl", results["evidential"])
    _write_jsonl(out_dir / "is_causal.jsonl", results["causal"])

    # Chart data
    chart = to_bubble_chart(results["statements"], results["threads"], results["links"])
    _write_json(out_dir / "chart_data.json", chart)

    print(f"Wrote outputs to: {out_dir}")

if __name__ == "__main__":
    sys.exit(main())
