param(
  [string]$InputPath = "data\ingest\INPUT.md",
  [string]$OutDir    = "out"
)

$fullIn  = Join-Path (Get-Location) $InputPath
$fullOut = Join-Path (Get-Location) $OutDir

if (-not (Test-Path $fullIn)) {
  Write-Error "Missing input file: $fullIn. Create it and try again."
  exit 1
}

$py = @"
import orjson
from pathlib import Path
from hdt.core.pipeline.run import run_all_for_path

inp = r"$fullIn"
out_dir = Path(r"$fullOut")
out_dir.mkdir(exist_ok=True)

res = run_all_for_path(inp)

def plain(x):
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    return x

def dump_jsonl(path, items):
    with open(path, "wb") as f:
        for obj in (items or []):
            f.write(orjson.dumps(plain(obj)))
            f.write(b"\n")

dump_jsonl(out_dir / "statements.jsonl", res.get("statements"))
dump_jsonl(out_dir / "links.jsonl",      res.get("links"))
dump_jsonl(out_dir / "threads.jsonl",    res.get("threads"))

canon = plain(res.get("canonical") or {})
(out_dir / "canon.json").write_bytes(orjson.dumps(canon))

print("Saved to:", out_dir.resolve())
"@

$py | python -

Write-Host "`n--- out/ ---`n"
Get-ChildItem -Force $OutDir

Write-Host "`n--- statements (first 10 lines) ---"
Get-Content -TotalCount 10 (Join-Path $OutDir "statements.jsonl") -ErrorAction SilentlyContinue
