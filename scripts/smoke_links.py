from __future__ import annotations
import argparse, pathlib, json, sys

# --- add project root to sys.path so "adapters" is importable ---
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ---------------------------------------------------------------

from hdt.core.ingest.parsers import parse_auto
from hdt.core.segment.rules import segment_document
from hdt.core.amu.extract import extract_amus
from hdt.core.topic.assign import assign_topics
from hdt.core.threads.build import build_threads
from hdt.core.links.extract import extract_links
from adapters.core_to_chart import to_bubble_chart

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()

    data = pathlib.Path(args.path).read_bytes()
    _, can, _ = parse_auto(data, path=args.path)
    stmts = segment_document(can)
    amus = extract_amus(stmts)
    topics = assign_topics(amus)
    threads = build_threads(stmts, amus, topics)
    links = extract_links(stmts, threads)

    chart = to_bubble_chart(stmts, threads, links, meta={"doc_id": can.doc_id})
    outdir = pathlib.Path("out"); outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "chart_data.json").write_text(json.dumps(chart, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote out/chart_data.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
