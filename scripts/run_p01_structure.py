from __future__ import annotations
import argparse, orjson, datetime as dt, hashlib, os
from pathlib import Path

from hdt.core.control_resolver import ControlResolver
from hdt.core.schema_ops import apply_schema
from hdt.core.schema_validate import validate_rows
from hdt.core.structure.segmentation import segment_path
from hdt.core.output_router import mirror_artifacts

def dump_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        for r in (rows or []):
            f.write(orjson.dumps(r)); f.write(b"\n")

def main():
    ap = argparse.ArgumentParser(description="Phase 1 / Step 01: Segmentation")
    ap.add_argument("-i","--in",  dest="inp", default=r"data\ingest\INPUT.md")
    ap.add_argument("-o","--out", dest="out", default="out")
    ap.add_argument("--run-tag", default=None)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--no-mirror", action="store_true")
    ap.add_argument("--mirror-mode", default=os.getenv("OUT_MIRROR_MODE","copy"),
                    choices=["copy","symlink","auto"])
    args = ap.parse_args()

    inp = Path(args.inp); out_root = Path(args.out)
    out_dir = (out_root / "runs" / args.run_tag) if args.run_tag else out_root
    out_dir.mkdir(parents=True, exist_ok=True)

    resolver = ControlResolver("config")
    stack = resolver.for_step("p01_structure","step_01_segmentation")

    print(f"[1/1] Segmentation on {inp} \u2192 {out_dir}")
    rows = segment_path(inp, controls=stack)

    # schema normalize + validate
    sch = stack.get_schema("segments", {})
    rows = apply_schema(rows, sch) if sch else rows
    dump_jsonl(out_dir / "segments.jsonl", rows)
    validation = validate_rows(rows, sch)
    (out_dir / "validation_p01.json").write_text(orjson.dumps({"segments.jsonl": validation}).decode("utf-8"), encoding="utf-8")

    print("Done. Created:")
    print(f"  - {out_dir / 'segments.jsonl'}  ({(out_dir / 'segments.jsonl').stat().st_size} bytes)")
    print(f"  - {out_dir / 'validation_p01.json'}  ({(out_dir / 'validation_p01.json').stat().st_size} bytes)")

    if not args.no_mirror:
        try:
            mirror_artifacts(out_root, out_dir, [out_dir / "segments.jsonl"], mode=args.mirror_mode)
        except Exception as e:
            print(f"[mirror] WARN: {e}")

    if args.show:
        head = out_dir / "segments.jsonl"
        if head.exists():
            print("\\n--- segments.jsonl (head) ---")
            with head.open("rb") as f:
                for i, line in enumerate(f):
                    print(line.decode("utf-8").rstrip())
                    if i >= 9: break

if __name__ == "__main__":
    main()
