from __future__ import annotations
from pathlib import Path
from hdt.core.pipeline.batch import run_many

def test_run_many_creates_per_doc_outputs(tmp_path: Path):
    d = tmp_path / "in"; d.mkdir()
    (d/"a.txt").write_bytes(b"Demand grew.\r\nTherefore, revenue increased.")
    (d/"b.md").write_bytes("# Title\r\n\r\nHowever, costs rose.".encode("utf-8"))

    out = tmp_path / "out"
    idx = run_many([str(d)], out_dir=str(out))  # directory input expands to two files
    assert len(idx) == 2
    # each entry has a per-doc folder with statements.jsonl
    for entry in idx:
        od = Path(entry["out_dir"])
        assert (od / "statements.jsonl").exists()
        assert (od / "canon.json").exists()
    # index.json exists
    assert (out / "index.json").exists()
