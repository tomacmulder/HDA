from __future__ import annotations
from hdt.core.pipeline.run import run_all_for_path
from pathlib import Path

def test_pipeline_smoke(tmp_path: Path):
    p = Path("data/ingest/links_demo.txt")
    res = run_all_for_path(str(p))
    # essential keys exist
    for k in ["canonical","statements","amus","topics","threads","links","modal","evidential","causal"]:
        assert k in res
    # non-empty on our demo
    assert len(res["statements"]) >= 3
    assert len(res["links"]) >= 1
