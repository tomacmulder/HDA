from __future__ import annotations
import json, os, sys, platform, subprocess, hashlib, datetime as dt, shutil
from pathlib import Path
from typing import Any, Dict, List
from .controls import ControlRegistry, _sha1 as file_sha1

def _safe_run(cmd: List[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
    except Exception as e:
        return f"ERR: {e}"

def snapshot_env() -> Dict[str, Any]:
    import sys as _sys
    d = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "python": _sys.version,
        "platform": platform.platform(),
        "executable": _sys.executable,
        "cwd": str(Path.cwd()),
        "env": {k:v for k,v in os.environ.items() if k.startswith("HDT_")},
    }
    d["git_head"] = _safe_run(["git","rev-parse","--verify","HEAD"])
    d["git_status"] = _safe_run(["git","status","--porcelain"])
    d["git_remote"] = _safe_run(["git","remote","-v"])
    d["pip_freeze"] = _safe_run([_sys.executable,"-m","pip","freeze"]).splitlines()
    return d

def _hash_dir(root: Path) -> str:
    h = hashlib.sha1()
    for p in sorted([x for x in root.rglob("*") if x.is_file()]):
        h.update(str(p.relative_to(root)).encode("utf-8"))
        h.update(file_sha1(p).encode("utf-8"))
    return h.hexdigest()

def snapshot_controls(controls: ControlRegistry, dest: Path) -> Dict[str, Any]:
    outdir = dest / "controls"
    (outdir / "schemas").mkdir(parents=True, exist_ok=True)
    (outdir / "guides").mkdir(parents=True, exist_ok=True)
    (outdir / "prompts").mkdir(parents=True, exist_ok=True)

    index = {"schemas":{}, "guides":{}, "prompts":{}}
    for name,obj in controls.schemas.items():
        p = outdir/"schemas"/f"{name}.json"
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        index["schemas"][name] = {"rel": str(p.relative_to(dest)), "sha1": file_sha1(p)}
    for name,obj in controls.guides.items():
        p = outdir/"guides"/f"{name}.json"
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        index["guides"][name] = {"rel": str(p.relative_to(dest)), "sha1": file_sha1(p)}
    for name,text in controls.prompts.items():
        p = outdir/"prompts"/f"{name}.md"
        p.write_text(text, encoding="utf-8")
        index["prompts"][name] = {"rel": str(p.relative_to(dest)), "sha1": file_sha1(p)}

    # Full mirror of the controls directory (captures phases/steps)
    full_dir = dest / "controls_full"
    if full_dir.exists():
        shutil.rmtree(full_dir)
    shutil.copytree(controls.base, full_dir)
    index["controls_full_root"] = str(full_dir.relative_to(dest))
    index["controls_full_digest"] = _hash_dir(full_dir)

    (outdir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index

def snapshot_input(inp: Path, dest: Path) -> Dict[str, Any]:
    outdir = dest / "input"
    outdir.mkdir(parents=True, exist_ok=True)
    tgt = outdir / inp.name
    import shutil as _sh
    _sh.copy2(inp, tgt)
    meta = {"rel": str(tgt.relative_to(dest)), "sha1": file_sha1(tgt), "size": tgt.stat().st_size}
    (outdir / "index.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta

def index_outputs(paths: List[Path], dest: Path) -> Dict[str, Any]:
    out = []
    for p in paths:
        out.append({"rel": str(p.name), "sha1": file_sha1(p), "size": p.stat().st_size})
    import hashlib as _hh
    h = _hh.sha1()
    for e in sorted(out, key=lambda x: x["rel"]):
        h.update(e["rel"].encode("utf-8")); h.update(e["sha1"].encode("utf-8"))
    idx = {"artifacts": out, "aggregate_sha1": h.hexdigest()}
    (dest / "outputs_index.json").write_text(json.dumps(idx, indent=2), encoding="utf-8")
    return idx

def write_replay_scripts(audit_dir: Path, inp_meta: Dict[str,Any], run_tag: str|None, out_dir: Path):
    ps = audit_dir / "replay.ps1"
    sh = audit_dir / "replay.sh"
    ctrl_dir = (audit_dir / "controls_full").resolve()
    input_rel = inp_meta["rel"].replace("/", "\\")
    run_tag_arg = (f' --run-tag "{run_tag}"' if run_tag else "")
    ps.write_text(f'''# Repro script (pinned to snapshot controls tree)
$env:HDT_CONTROLS_DIR = "{ctrl_dir}"
python scripts\\run_is.py -i "{audit_dir}\\{input_rel}" -o "{out_dir}"{run_tag_arg} --show --audit
''', encoding="utf-8")
    sh.write_text(f'''#!/usr/bin/env bash
export HDT_CONTROLS_DIR="{ctrl_dir}"
python scripts/run_is.py -i "{audit_dir}/{inp_meta["rel"]}" -o "{out_dir}"{run_tag_arg} --show --audit
''', encoding="utf-8")

def write_manifest(audit_dir: Path, env: Dict[str,Any], controls_idx: Dict[str,Any], inp_meta: Dict[str,Any], out_idx: Dict[str,Any]) -> Dict[str,Any]:
    manifest = {
        "spec": "audit-pack/0.2",
        "env": env,
        "controls": controls_idx,
        "input": inp_meta,
        "outputs": out_idx,
        "created_ts": dt.datetime.now(dt.timezone.utc).isoformat()
    }
    (audit_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest

def write_audit_pack(out_dir: Path, controls: ControlRegistry, inp: Path, created_paths: List[Path], run_tag: str|None):
    audit_dir = out_dir / "_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    env = snapshot_env()
    controls_idx = snapshot_controls(controls, audit_dir)
    inp_meta = snapshot_input(inp, audit_dir)
    out_idx = index_outputs(created_paths, audit_dir)
    write_replay_scripts(audit_dir, inp_meta, run_tag, out_dir)
    return write_manifest(audit_dir, env, controls_idx, inp_meta, out_idx)
