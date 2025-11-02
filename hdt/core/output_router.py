from __future__ import annotations
from pathlib import Path
import shutil, os

ROUTES = {
    # STRUCTURE
    "segments.jsonl":   ("p01_structure", "step_01_segmentation"),
    "statements.jsonl": ("p01_structure", "step_01_segmentation"),
    "canon.json":       ("p01_structure", "step_01_segmentation"),
    "amus.jsonl":       ("p01_structure", "step_02_amus"),
    "topics.jsonl":     ("p01_structure", "step_03_topic_map"),
    "threads.jsonl":    ("p01_structure", "step_04_threads_roles"),
    "links.jsonl":      ("p01_structure", "step_05_links"),

    # IS (3.1..3.8)
    "scaffold.jsonl":      ("p02_is", "step_31_scaffold"),
    "time_modality.jsonl": ("p02_is", "step_32_time_modality"),
    "evidential.jsonl":    ("p02_is", "step_33_evidential"),
    "causal.jsonl":        ("p02_is", "step_34_causal"),
    "claims_is.jsonl":     ("p02_is", "step_35_is_claims"),
    "ontology.jsonl":      ("p02_is", "step_36_ontology"),
    "retrieval.jsonl":     ("p02_is", "step_37_retrieval"),
    "accuracy.jsonl":      ("p02_is", "step_38_accuracy"),
    "is.json":             ("p02_is", "step_38_accuracy"),

    # OUGHT (3.1..3.6) -> Phase 3
    "deontic.jsonl":          ("p03_ought", "step_41_deontic"),
    "ends_means.jsonl":       ("p03_ought", "step_42_ends_means"),
    "wiring.jsonl":           ("p03_ought", "step_43_wiring_proportionality"),
    "pragmatics.jsonl":       ("p03_ought", "step_44_pragmatics_strength"),
    "stance_values.jsonl":    ("p03_ought", "step_45_stance_values"),
    "integrity_fusion.jsonl": ("p03_ought", "step_46_integrity_fusion"),
}

def _run_tag(out_root: Path, out_dir: Path) -> str | None:
    try:
        runs = (out_root / "runs").resolve()
        out_dir = Path(out_dir).resolve()
        if out_dir.is_relative_to(runs):
            return out_dir.relative_to(runs).parts[0]
    except Exception:
        pass
    return None

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def _try_symlink_or_copy(src: Path, dst: Path, mode: str="copy") -> None:
    if dst.exists(): return
    _ensure_dir(dst.parent)
    if mode in ("symlink","auto"):
        try:
            os.symlink(src, dst); return
        except Exception:
            if mode == "symlink": pass
    shutil.copy2(src, dst)

def mirror_artifacts(out_root: str|Path, out_dir: str|Path, artifacts: list[Path], mode: str="copy") -> None:
    out_root = Path(out_root); out_dir = Path(out_dir)
    tag = _run_tag(out_root, out_dir)
    for src in artifacts:
        route = ROUTES.get(src.name)
        if not route: continue
        phase, step = route
        base = out_root / "phases" / phase / "steps" / step
        _try_symlink_or_copy(src, base / "latest" / src.name, mode=mode)
        if tag:
            _try_symlink_or_copy(src, base / "runs" / tag / src.name, mode=mode)

# --- normalized routes (p02_is + p04_ought) ---
# --- normalized routes (p02_is + p04_ought) ---
try:
    ROUTES.update({
        # Phase 2 (IS)
        "scaffold.jsonl":          ("p02_is","step_01_scaffold"),
        "time_modality.jsonl":     ("p02_is","step_02_time_modality"),
        "evidential.jsonl":        ("p02_is","step_03_evidential"),
        "causal.jsonl":            ("p02_is","step_04_causal"),
        "claims_is.jsonl":         ("p02_is","step_05_is_claims"),
        "ontology.jsonl":          ("p02_is","step_06_ontology"),
        "retrieval.jsonl":         ("p02_is","step_07_retrieval"),
        "accuracy.jsonl":          ("p02_is","step_08_accuracy"),
        "analytic_integrity.jsonl":("p02_is","step_09_integrity_rollup"),
        "is.json":                 ("p02_is","step_09_integrity_rollup"),
        # Phase 4 (OUGHT)
        "deontic.jsonl":           ("p04_ought","step_01_deontic"),
        "ends_means.jsonl":        ("p04_ought","step_02_ends_means"),
        "wiring.jsonl":            ("p04_ought","step_03_wiring_proportionality"),
        "pragmatics.jsonl":        ("p04_ought","step_04_pragmatics_strength"),
        "stance_values.jsonl":     ("p04_ought","step_05_stance_values"),
        "integrity_fusion.jsonl":  ("p04_ought","step_06_integrity_fusion"),
        "ought.json":              ("p04_ought","step_06_integrity_fusion"),
        # Phase 5/6
        "canon_join.jsonl":        ("p05_canonization","step_01_canon_join"),
        "reports.jsonl":           ("p06_reporting","step_01_reports"),
    })
except Exception:
    pass
# --- normalized routes (p02_is + p03_ought + p04_entities) ---
try:
    ROUTES.update({
        # Phase 1 (structure) are already defined upstream (segments/statements/canon).
        # Phase 2 (IS)
        "scaffold.jsonl":           ("p02_is","step_01_scaffold"),
        "time_modality.jsonl":      ("p02_is","step_02_time_modality"),
        "evidential.jsonl":         ("p02_is","step_03_evidential"),
        "causal.jsonl":             ("p02_is","step_04_causal"),
        "claims_is.jsonl":          ("p02_is","step_05_is_claims"),
        "ontology.jsonl":           ("p02_is","step_06_ontology"),
        "retrieval.jsonl":          ("p02_is","step_07_retrieval"),
        "accuracy.jsonl":           ("p02_is","step_08_accuracy"),
        "analytic_integrity.jsonl": ("p02_is","step_09_integrity_rollup"),
        "is.json":                  ("p02_is","step_09_integrity_rollup"),
        # Phase 3 (OUGHT)
        "deontic.jsonl":            ("p03_ought","step_01_deontic"),
        "ends_means.jsonl":         ("p03_ought","step_02_ends_means"),
        "wiring.jsonl":             ("p03_ought","step_03_wiring_proportionality"),
        "pragmatics.jsonl":         ("p03_ought","step_04_pragmatics_strength"),
        "stance_values.jsonl":      ("p03_ought","step_05_stance_values"),
        "integrity_fusion.jsonl":   ("p03_ought","step_06_integrity_fusion"),
        "ought.json":               ("p03_ought","step_06_integrity_fusion"),
        # Phase 4 (Entities) — optional analytics
        "ner.jsonl":                ("p04_entities","step_01_ner"),
        "coref.jsonl":              ("p04_entities","step_02_coref"),
        # Phase 5/6
        "canon_join.jsonl":         ("p05_canonization","step_01_canon_join"),
        "reports.jsonl":            ("p06_reporting","step_01_reports"),
    })
except Exception:
    pass
