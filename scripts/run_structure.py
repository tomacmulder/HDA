from __future__ import annotations
import os, argparse, orjson, hashlib, json
from pathlib import Path

from hdt.core.pipeline.run import run_all_for_path
from hdt.core.schema_ops import apply_schema
from hdt.core.schema_validate import validate_rows
from hdt.core.control_resolver import ControlResolver
from hdt.core.prompt_audit import persist_prompt_policy
from hdt.core.amu import amuize
from hdt.core.topic import assign_topics
from hdt.core.threads import form_threads
from hdt.core.output_router import mirror_artifacts
from hdt.core.provenance import stamp_rows

try:
    from hdt.core.links import build_links as _build_links
except Exception:
    _build_links = None

def _rowify(r): return r.model_dump() if hasattr(r, "model_dump") else r
def dump_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        for r in (rows or []):
            f.write(orjson.dumps(_rowify(r))); f.write(b"\n")

def dump_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orjson.dumps(obj))

def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
    return h.hexdigest()

def list_created(out_dir: Path):
    names = ["segments.jsonl","statements.jsonl","canon.json",
             "amus.jsonl","topics.jsonl","threads.jsonl","links.jsonl",
             "structural_summary.json","_controls_catalog.md","validation_structure.json"]
    return [out_dir / n for n in names if (out_dir / n).exists()]

def _project_to_schema(rows, schema):
    if not schema: return rows
    cols = [c.get("name") for c in (schema.get("columns") or [])]
    if not cols: return rows
    out = []
    for r in (rows or []):
        d = r if isinstance(r, dict) else (_rowify(r) if r else {})
        out.append({k: d.get(k) for k in cols if k in d})
    return out

def main():
    ap = argparse.ArgumentParser(description="STRUCTURE runner (00..06)")
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
    panel = json.loads(Path("config/panel/global.json").read_text(encoding="utf-8"))

    # 00 Preflight (provenance is stamped on every artifact we write)
    s0 = resolver.for_step("p01_structure","step_00_preflight_provenance")
    persist_prompt_policy(out_dir, "p01_structure", "step_00_preflight_provenance", s0.get_prompt("main",""))

    # 01 Segmentation (reuse legacy)
    s1 = resolver.for_step("p01_structure","step_01_segmentation")
    persist_prompt_policy(out_dir, "p01_structure", "step_01_segmentation", s1.get_prompt("main",""))
    print(f"[STRUCTURE/01] Segmentation on {inp} -> {out_dir}")
    res = run_all_for_path(str(inp))
    statements = res.get("statements", [])
    segments   = res.get("segments",   []) or [{"Document_Title":"", "Order_Index":i+1, "Statement_Text_ID": st.get("id") or f"S{i+1}",
                 "Statement_Text": getattr(st,"text",None) or st.get("text",""), "Speaker_ID":"unknown","Timestamp_Start":"","Timestamp_End":""}
                 for i,st in enumerate(statements)]
    canon = res.get("canon", {}) or {"note":"no_canon","counts":{"statements":len(statements)}}

    sc_schema = s1.get_schema("segments", {})
    segments  = _project_to_schema(segments, sc_schema)
    segments  = stamp_rows(segments, panel, inp, "p01_structure.step_01_segmentation")
    dump_jsonl(out_dir / "segments.jsonl", segments)
    dump_jsonl(out_dir / "statements.jsonl", stamp_rows(statements, panel, inp, "p01_structure.step_01_segmentation"))
    dump_json(out_dir  / "canon.json", canon)

    # 02 AMUs
    s2 = resolver.for_step("p01_structure","step_02_amus")
    persist_prompt_policy(out_dir, "p01_structure", "step_02_amus", s2.get_prompt("main",""))
    print("[STRUCTURE/02] AMUs")
    guide_amu = s2.get_guide("amu_rules", {}) or {}
    schema_amu = s2.get_schema("amus", {}) or {}
    amus = amuize(statements, guides=guide_amu)
    # Fill Frontier addendum defaults
    for r in amus:
        r.setdefault("AMU_Gloss",""); r.setdefault("AMU_Illocution",""); r.setdefault("Coref_Links","")
        r.setdefault("Numerical_Spans",""); r.setdefault("Confidence",0.6)
    amus = _project_to_schema(amus, schema_amu)
    amus = stamp_rows(amus, panel, inp, "p01_structure.step_02_amus")
    dump_jsonl(out_dir / "amus.jsonl", amus)

    # 03 Topic-first mapping
    s3 = resolver.for_step("p01_structure","step_03_topic_map")
    persist_prompt_policy(out_dir, "p01_structure", "step_03_topic_map", s3.get_prompt("main",""))
    print("[STRUCTURE/03] Topic map")
    schema_topics = s3.get_schema("topics", {}) or {}
    topics = assign_topics(amus, guides=s3.get_guide("topic_keywords", {}) or {})
    for r in topics:
        r.setdefault("Topic_Path_Preview",""); r.setdefault("Topic_Granularity","broad")
    topics = _project_to_schema(topics, schema_topics)
    topics = stamp_rows(topics, panel, inp, "p01_structure.step_03_topic_map")
    dump_jsonl(out_dir / "topics.jsonl", topics)

    # 04 Threads & roles
    s4 = resolver.for_step("p01_structure","step_04_threads_roles")
    persist_prompt_policy(out_dir, "p01_structure", "step_04_threads_roles", s4.get_prompt("main",""))
    print("[STRUCTURE/04] Threads & roles")
    schema_thr = s4.get_schema("threads", {}) or {}
    trows = form_threads(statements, guides=s4.get_guide("threads_heuristics", {}) or {})
    for r in trows:
        r.setdefault("Role_Confidence", 0.7); r.setdefault("RST_Relation","")
    trows = _project_to_schema(trows, schema_thr)
    trows = stamp_rows(trows, panel, inp, "p01_structure.step_04_threads_roles")
    dump_jsonl(out_dir / "threads.jsonl", trows)

    # 05 Links (if builder exists)
    s5 = resolver.for_step("p01_structure","step_05_links")
    persist_prompt_policy(out_dir, "p01_structure", "step_05_links", s5.get_prompt("main",""))
    print("[STRUCTURE/05] Links")
    schema_links = s5.get_schema("links", {}) or {}
    if _build_links:
        lrows = _build_links(statements, trows)
    else:
        lrows = [{"Statement_Text_ID": _rowify(st).get("id") or f"S{i+1}",
                  "Supports_IDs":"[]","Opposes_IDs":"[]","References_IDs":"[]",
                  "Relation_Cues":"[]","Relation_Strength":"weak",
                  "Link_Type":"","Reasoning_Scheme":"","Link_Confidence":0.0}
                 for i, st in enumerate(statements)]
    lrows = _project_to_schema(lrows, schema_links)
    lrows = stamp_rows(lrows, panel, inp, "p01_structure.step_05_links")
    dump_jsonl(out_dir / "links.jsonl", lrows)

    # 06 Structural validation & summary
    s6 = resolver.for_step("p01_structure","step_06_structural_validation")
    persist_prompt_policy(out_dir, "p01_structure", "step_06_structural_validation", s6.get_prompt("main",""))
    print("[STRUCTURE/06] Structural validation")
    # validation — combine all schema validations we know
    val = {
        "segments.jsonl": validate_rows(segments, sc_schema or {}),
        "amus.jsonl": validate_rows(amus, schema_amu or {}),
        "topics.jsonl": validate_rows(topics, schema_topics or {}),
        "threads.jsonl": validate_rows(trows, schema_thr or {}),
        "links.jsonl": validate_rows(lrows, schema_links or {})
    }
    (out_dir / "validation_structure.json").write_text(orjson.dumps(val).decode("utf-8"), encoding="utf-8")

    # Contiguity checks & quick graph skeleton
    def _tid_num(t): 
        import re
        m = re.search(r"(\d+)", str(t or ""))
        return int(m.group(1)) if m else 0
    tids = sorted({_rowify(r).get("Thread_ID") for r in trows}, key=_tid_num)
    contiguous = tids == [f"T{i+1}" for i in range(len(tids))]
    nodes = [{"type":"S","id":_rowify(s).get("id") or f"S{i+1}"} for i,s in enumerate(statements)]
    # amu nodes:
    nodes += [{"type":"A","id":_rowify(a).get("AMU_ID")} for a in amus]
    edges = []
    for r in lrows:
        d = _rowify(r)
        sid = d.get("Statement_Text_ID")
        import json as _j
        def _ids(x):
            try:
                arr = _j.loads(x) if isinstance(x, str) else (x or [])
                return [z for z in arr if z]
            except Exception: return []
        for k in _ids(d.get("Supports_IDs","[]")): edges.append({"from":sid,"to":k,"kind":"supports"})
        for k in _ids(d.get("Opposes_IDs","[]")): edges.append({"from":sid,"to":k,"kind":"opposes"})
        for k in _ids(d.get("References_IDs","[]")): edges.append({"from":sid,"to":k,"kind":"references"})
    summary_rows = [
        {"type":"check","key":"threads_contiguous","value":str(contiguous)},
        {"type":"count","key":"statements","value":str(len(statements))},
        {"type":"count","key":"amus","value":str(len(amus))},
        {"type":"count","key":"links","value":str(len(lrows))}
    ]
    summary_rows = stamp_rows(summary_rows, panel, inp, "p01_structure.step_06_structural_validation")
    dump_jsonl(out_dir / "structural_summary.json", summary_rows)

    # Catalog
    cat = ["# Controls Catalog (STRUCTURE steps)"]
    for title, stack in [
      ("p01_structure / step_00_preflight_provenance", s0),
      ("p01_structure / step_01_segmentation", s1),
      ("p01_structure / step_02_amus", s2),
      ("p01_structure / step_03_topic_map", s3),
      ("p01_structure / step_04_threads_roles", s4),
      ("p01_structure / step_05_links", s5),
      ("p01_structure / step_06_structural_validation", s6),
    ]:
        cat.append(f"\n## {title}")
        for fp in stack.fingerprints:
            cat.append(f"- {fp['kind']}: **{fp['name']}** — `{fp['path']}` (sha1: {fp['sha1']})")
    (out_dir / "_controls_catalog.md").write_text("\n".join(cat), encoding="utf-8")

    # Mirror
    if not args.no_mirror:
        try:
            mirror_artifacts(out_root, out_dir, list_created(out_dir), mode=args.mirror_mode)
        except Exception as e:
            print(f"[mirror] WARN: {e}")

    print("[DONE] Created:")
    for p in list_created(out_dir):
        print(f"  - {p} ({p.stat().st_size} bytes)")
    if args.show:
        for fname in ["segments.jsonl","amus.jsonl","topics.jsonl","threads.jsonl","links.jsonl","structural_summary.json"]:
            head = out_dir / fname
            if head.exists():
                print(f"\n--- {fname} (head) ---")
                with head.open("rb") as f:
                    for i, line in enumerate(f):
                        print(line.decode("utf-8").rstrip())
                        if i >= 9: break

if __name__ == "__main__":
    main()
