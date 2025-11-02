from __future__ import annotations
import argparse, sys, json, glob
from pathlib import Path

from hdt.core.pipeline.run import run_all_for_path
from hdt.core.pipeline.batch import run_many

def main(argv=None):
    ap = argparse.ArgumentParser(description="HDT2 pipeline runner")
    ap.add_argument("inputs", nargs="+", help="File(s), directory(ies), or globs (*.txt, *.md)")
    ap.add_argument("-o", "--out-dir", default="out", help="Output directory (default: out)")
    args = ap.parse_args(argv)

    # Expand globs and directories
    expanded = []
    for s in args.inputs:
        p = Path(s)
        if p.is_dir():
            expanded.extend([str(x) for x in p.glob("*.txt")])
            expanded.extend([str(x) for x in p.glob("*.md")])
        elif any(ch in s for ch in "*?[]"):
            expanded.extend(glob.glob(s))
        else:
            expanded.append(str(p))

    # De-dup while preserving order
    seen, files = set(), []
    for f in expanded:
        if f not in seen:
            seen.add(f); files.append(f)

    if len(files) == 0:
        print("No inputs matched.", file=sys.stderr)
        return 2

    if len(files) == 1 and Path(files[0]).is_file():
        res = run_all_for_path(files[0])
        print("Wrote outputs to:", args.out_dir)
        print(json.dumps({
            "doc_id": getattr(res["canonical"], "doc_id", "unknown"),
            "out_dir": str(Path(args.out_dir).resolve())
        }))
        return 0
    else:
        idx = run_many(files, out_dir=args.out_dir)
        print(f"Processed {len(idx)} document(s). Index at {Path(args.out_dir,'index.json').resolve()}")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
