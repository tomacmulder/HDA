from __future__ import annotations
import os, argparse, orjson, json, datetime as dt, hashlib
from pathlib import Path
from typing import Iterable, Optional

from hdt.core.control_resolver import ControlResolver
from hdt.core.schema_ops import apply_schema  # kept for compatibility
from hdt.core.schema_validate import validate_rows
from hdt.core.prompt_audit import persist_prompt_policy
from hdt.core.output_router import mirror_artifacts
from hdt.core.provenance import stamp_rows

from hdt.core.ought_analysis.deontic        import analyze as deontic_analyze
from hdt.core.ought_analysis.ends_means     import analyze as ends_means_analyze
from hdt.core.ought_analysis.wiring         import analyze as wiring_analyze
from hdt.core.ought_analysis.pragmatics     import analyze as prag_analyze
from hdt.core.ought_analysis.stance_values  import analyze as stance_analyze
from hdt.core.ought_analysis.integrity      import analyze as fusion_analyze

# ---------- small utils ----------
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
    names = [
        "deontic.jsonl","ends_means.jsonl","wiring.jsonl","pragmatics.jsonl",
        "stance_values.jsonl","integrity_fusion.jsonl","ought.json",
        "validation_ought.json","_controls_catalog.md"
    ]
    return [out_dir / n for n in names if (out_dir / n).exists()]

def _print_head(path: Path, n: int):
    try:
        with path.open("rb") as f:
            for i, line in enumerate(f):
                try:
                    print(line.decode("utf-8", "replace").rstrip())
                except Exception:
                    print(str(line)[:200])
                if i >= max(n - 1, 0):
                    break
    except Exception as e:
        print(f"    [head] WARN: {e}")

def _confirm_gate(args, title: str, files: Iterable[Path] = ()):
    """
    If --confirm (or HDT_CONFIRM_STEPS=1) is set, show sizes + heads then wait for user input.
    Enter -> continue; 'q' -> abort; 's' -> skip remaining gates.
    """
    env_confirm = str(os.getenv("HDT_CONFIRM_STEPS", "0")).lower() in ("1","true","yes","on")
    if not (getattr(args, "confirm", False) or env_confirm):
        return
    head_env = os.getenv("HDT_HEAD", "")
    head_n = int(getattr(args, "head", 5) if getattr(args, "head", None) is not None else (int(head_env) if head_env else 5))
    print(f"\n[confirm] {title}")
    for p in (files or []):
        try:
            p = Path(p)
            if p.exists():
                print(f"  - {p}  ({p.stat().st_size} bytes)")
                if head_n > 0:
                    _print_head(p, head_n)
            else:
                print(f"  - MISSING: {p}")
        except Exception as e:
            print(f"  - [WARN] could not preview {p}: {e}")
    try:
        resp = input("\n↩️  Press Enter to continue, 'q' to abort, 's' to skip further confirms: ").strip().lower()
    except EOFError:
        resp = ""
    if resp == "q":
        print("[confirm] Aborted by user."); raise SystemExit(2)
    if resp == "s":
        args.confirm = False

# ---------- input discovery (prefer latest IS outputs) ----------
def _latest_run_subdir(root: Path) -> Optional[Path]:
    """
    Returns most recent subdir in root/runs/* that contains files.
    """
    runs = []
    d = root / "runs"
    if d.exists():
        for p in d.iterdir():
            try:
                if p.is_dir():
                    runs.append((p.stat().st_mtime, p))
            except Exception:
                pass
    runs.sort(reverse=True)
    return runs[0][1] if runs else None

def _first_existing(paths: Iterable[Path]) -> Optional[Path]:
    for p in paths:
        if p and p.exists() and p.stat().st_size > 0:
            return p
    return None

def _resolve_is_artifact(name: str) -> Optional[Path]:
    """
    Try to locate an IS artifact by common locations (root, latest run, phases).
    `name` is like 'statements.jsonl' or 'analytic_integrity.jsonl'
    """
    # 1) out\name
    p1 = Path("out") / name
    # 2) latest out\runs\*\name
    latest = _latest_run_subdir(Path("out"))
    p2 = (latest / name) if latest else None
    # 3) legacy phases paths
    legacy_map = {
        "statements.jsonl": Path(r"out/phases/p01_structure/steps/step_01_segmentation/latest/statements.jsonl"),
        "analytic_integrity.jsonl": Path(r"out/phases/p02_is/steps/step_39_integrity_rollup/latest/analytic_integrity.jsonl"),
    }
    p3 = legacy_map.get(name)
    return _first_existing([p1, p2, p3])

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="OUGHT runner — 4.1..4.6")
    # Default inputs now auto-resolve from IS outputs; flags let you override
    ap.add_argument("-s","--statements", dest="stm", default=None,
                    help="Path to statements.jsonl (defaults to latest IS output)")
    ap.add_argument("-i","--integrity", dest="integ", default=None,
                    help="Path to analytic_integrity.jsonl (defaults to latest IS output if present)")
    ap.add_argument("-o","--out", dest="out", default="out_ought")
    ap.add_argument("--run-tag", default=None)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--confirm", action="store_true",
                    help="Pause after each step and show heads; Enter to continue")
    ap.add_argument("--head", type=int, default=int(os.getenv("HDT_HEAD", "5")),
                    help="Lines to preview per file at confirm gates (default: 5)")
    ap.add_argument("--no-mirror", action="store_true")
    ap.add_argument("--mirror-mode", default=os.getenv("OUT_MIRROR_MODE","copy"),
                    choices=["copy","symlink","auto"])
    args = ap.parse_args()

    out_root = Path(args.out)
    out_dir = (out_root / "runs" / args.run_tag) if args.run_tag else out_root
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Load prior results we need ----
    integ_path = Path(args.integ) if args.integ else _resolve_is_artifact("analytic_integrity.jsonl")
    stm_path   = Path(args.stm)   if args.stm   else _resolve_is_artifact("statements.jsonl")

    integ = []
    if integ_path and integ_path.exists():
        with integ_path.open("rb") as f:
            integ = [orjson.loads(l) for l in f]

    statements = []
    if stm_path and stm_path.exists():
        with stm_path.open("rb") as f:
            statements = [orjson.loads(l) for l in f]

    resolver = ControlResolver("config")
    panel = json.loads(Path("config/panel/global.json").read_text(encoding="utf-8"))

    validation = {}

    # 4.1 Deontic
    s41 = resolver.for_step("p03_ought","step_01_deontic")
    persist_prompt_policy(out_dir, "p03_ought","step_01_deontic", s41.get_prompt("main",""))
    de_schema = s41.get_schema("deontic", {})
    de_rows = deontic_analyze(statements, guides=s41)
    de_rows = stamp_rows(de_rows, panel, stm_path or Path("."), "p03_ought.step_01_deontic")
    dump_jsonl(out_dir / "deontic.jsonl", de_rows)
    validation["deontic.jsonl"] = validate_rows(de_rows, de_schema)

    _confirm_gate(args, "After 4.1 Deontic", [out_dir / "deontic.jsonl"])

    # 4.2 Ends & Means
    s42 = resolver.for_step("p03_ought","step_02_ends_means")
    persist_prompt_policy(out_dir, "p03_ought","step_02_ends_means", s42.get_prompt("main",""))
    em_schema = s42.get_schema("ends_means", {})
    em_rows = ends_means_analyze(de_rows, statements, guides=s42)
    em_rows = stamp_rows(em_rows, panel, stm_path or Path("."), "p03_ought.step_02_ends_means")
    dump_jsonl(out_dir / "ends_means.jsonl", em_rows)
    validation["ends_means.jsonl"] = validate_rows(em_rows, em_schema)

    _confirm_gate(args, "After 4.2 Ends & Means", [out_dir / "ends_means.jsonl"])

    # 4.3 Wiring / Proportionality
    s43 = resolver.for_step("p03_ought","step_03_wiring_proportionality")
    persist_prompt_policy(out_dir, "p03_ought","step_03_wiring_proportionality", s43.get_prompt("main",""))
    wr_schema = s43.get_schema("wiring", {})
    # For now, pass empty claims/scm (can be wired to IS outputs later)
    wr_rows = wiring_analyze(em_rows, claims=[], scm_rows=[], guides=s43)
    wr_rows = stamp_rows(wr_rows, panel, stm_path or Path("."), "p03_ought.step_03_wiring_proportionality")
    dump_jsonl(out_dir / "wiring.jsonl", wr_rows)
    validation["wiring.jsonl"] = validate_rows(wr_rows, wr_schema)

    _confirm_gate(args, "After 4.3 Wiring / Proportionality", [out_dir / "wiring.jsonl"])

    # 4.4 Pragmatics
    s44 = resolver.for_step("p03_ought","step_04_pragmatics_strength")
    persist_prompt_policy(out_dir, "p03_ought","step_04_pragmatics_strength", s44.get_prompt("main",""))
    pr_schema = s44.get_schema("pragmatics", {})
    pr_rows = prag_analyze(statements, guides=s44)
    pr_rows = stamp_rows(pr_rows, panel, stm_path or Path("."), "p03_ought.step_04_pragmatics_strength")
    dump_jsonl(out_dir / "pragmatics.jsonl", pr_rows)
    validation["pragmatics.jsonl"] = validate_rows(pr_rows, pr_schema)

    _confirm_gate(args, "After 4.4 Pragmatics", [out_dir / "pragmatics.jsonl"])

    # 4.5 Stance & Values
    s45 = resolver.for_step("p03_ought","step_05_stance_values")
    persist_prompt_policy(out_dir, "p03_ought","step_05_stance_values", s45.get_prompt("main",""))
    st_schema = s45.get_schema("stance_values", {})
    st_rows = stance_analyze(statements, guides=s45)
    st_rows = stamp_rows(st_rows, panel, stm_path or Path("."), "p03_ought.step_05_stance_values")
    dump_jsonl(out_dir / "stance_values.jsonl", st_rows)
    validation["stance_values.jsonl"] = validate_rows(st_rows, st_schema)

    _confirm_gate(args, "After 4.5 Stance & Values", [out_dir / "stance_values.jsonl"])

    # 4.6 Integrity & Fusion
    s46 = resolver.for_step("p03_ought","step_06_integrity_fusion")
    persist_prompt_policy(out_dir, "p03_ought","step_06_integrity_fusion", s46.get_prompt("main",""))
    fu_schema = s46.get_schema("integrity_fusion", {})
    fu_rows = fusion_analyze(integ or [], st_rows, pr_rows, guides=s46)
    fu_rows = stamp_rows(fu_rows, panel, stm_path or Path("."), "p03_ought.step_06_integrity_fusion")
    dump_jsonl(out_dir / "integrity_fusion.jsonl", fu_rows)
    validation["integrity_fusion.jsonl"] = validate_rows(fu_rows, fu_schema)

    _confirm_gate(args, "After 4.6 Integrity & Fusion", [out_dir / "integrity_fusion.jsonl"])

    # Validation + rollup
    (out_dir / "validation_ought.json").write_text(orjson.dumps(validation).decode("utf-8"), encoding="utf-8")

    rollup = {"counts":{
       "deontic":len(de_rows),"ends_means":len(em_rows),"wiring":len(wr_rows),
       "pragmatics":len(pr_rows),"stance_values":len(st_rows),"integrity_fusion":len(fu_rows)},
       "input_statements": str(stm_path) if stm_path else "",
       "input_integrity":  str(integ_path) if integ_path else "",
       "ts": dt.datetime.now(dt.timezone.utc).isoformat()}
    dump_json(out_dir / "ought.json", rollup)

    if not args.no_mirror:
        try:
            mirror_artifacts(out_root, out_dir, list_created(out_dir), mode=args.mirror_mode)
        except Exception as e:
            print(f"[mirror] WARN: {e}")

    print("[DONE] OUGHT Created:")
    for p in list_created(out_dir):
        print(f"  - {p} ({p.stat().st_size} bytes)")

    if args.show:
        for fname in ["deontic.jsonl","ends_means.jsonl","wiring.jsonl","pragmatics.jsonl","stance_values.jsonl","integrity_fusion.jsonl"]:
            head = out_dir / fname
            if head.exists():
                print(f"\n--- {fname} (head) ---")
                with head.open("rb") as f:
                    for i, line in enumerate(f):
                        print(line.decode("utf-8").rstrip())
                        if i >= 9: break

if __name__ == "__main__":
    main()
