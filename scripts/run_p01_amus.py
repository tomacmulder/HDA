from __future__ import annotations
import argparse, orjson, os
from pathlib import Path

from hdt.core.control_resolver import ControlResolver
from hdt.core.schema_ops import apply_schema
from hdt.core.schema_validate import validate_rows
from hdt.core.structure.amu import amuize
from hdt.core.output_router import mirror_artifacts

def _read_jsonl(p: Path):
    if not p.exists(): return []
    out = []
    with p.open("rb") as f:
        for line in f:
            if line.strip():
                out.append(orjson.loads(line))
    return out

def _dump_jsonl(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("wb") as f:
        for r in rows or []:
            f.write(orjson.dumps(r)); f.write(b"\\n")

def main():
    ap = argparse.ArgumentParser(description="Phase 1 / Step 02: AMUs")
    ap.add_argument("-s","--segments", default=r"out\\segments.jsonl")
    ap.add_argument("-o","--out",      default="out")
    ap.add_argument("--run-tag",       default=None)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--no-mirror", action="store_true")
    ap.add_argument("--mirror-mode", default=os.getenv("OUT_MIRROR_MODE","copy"),
                    choices=["copy","symlink","auto"])
    args = ap.parse_args()

    out_root = Path(args.out)
    out_dir  = (out_root / "runs" / args.run_tag) if args.run_tag else out_root
    out_dir.mkdir(parents=True, exist_ok=True)

    seg_path = Path(args.segments)
    segs = _read_jsonl(seg_path)

    resolver = ControlResolver("config")
    stack = resolver.for_step("p01_structure","step_02_amus")

    rows = amuize(segs, controls=stack)
    sch = stack.get_schema("amus", {})
    rows = apply_schema(rows, sch) if sch else rows
    _dump_jsonl(out_dir / "amus.jsonl", rows)

    validation = validate_rows(rows, sch)
    (out_dir / "validation_p01_amus.json").write_text(orjson.dumps({"amus.jsonl": validation}).decode("utf-8"), encoding="utf-8")

    print("[1/1] AMUization complete.")
    print(f"  - {out_dir / 'amus.jsonl'}")
    print(f"  - {out_dir / 'validation_p01_amus.json'}")

    if not args.no_mirror:
        try:
            mirror_artifacts(out_root, out_dir, [out_dir / "amus.jsonl"], mode=args.mirror_mode)
        except Exception as e:
            print(f"[mirror] WARN: {e}")

    if args.show:
        head = out_dir / "amus.jsonl"
        if head.exists():
            print("\\n--- amus.jsonl (head) ---")
            with head.open("rb") as f:
                for i, line in enumerate(f):
                    print(line.decode("utf-8").rstrip())
                    if i >= 9: break

if __name__ == "__main__":
    main()
