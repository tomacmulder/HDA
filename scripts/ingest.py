#!/usr/bin/env python
from __future__ import annotations
import argparse, pathlib, sys, json
from hdt.core.ingest.parsers import parse_auto
from hdt.core.ingest.alignment import compute_byte_starts, AlignmentIndex

def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", help="Path to a text/markdown/srt file")
    p.add_argument("--encoding", default="utf-8")
    args = p.parse_args()

    data = pathlib.Path(args.path).read_bytes()
    raw, can, orig = parse_auto(data, encoding=args.encoding, path=str(args.path))
    idx = AlignmentIndex(can.alignment, compute_byte_starts(orig, raw.encoding))
    left, right = idx.inverse_bytes((0, len(can.canonical_text)))

    print(json.dumps({
        "doc_id": can.doc_id,
        "media_type": raw.media_type,
        "orig_bytes_len": raw.bytes_len,
        "canon_len": len(can.canonical_text),
        "inverse_first_slice_bytes": [left, right],
        "preview": can.canonical_text[:80]
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
