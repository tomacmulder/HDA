param(
  [Parameter(ValueFromPipeline=$true)] [string[]]$Text,
  [switch]$FromClipboard,
  [string]$File
)
$ErrorActionPreference = "Stop"
$root   = (Get-Location).Path
$INPUT  = Join-Path $root "data\ingest\INPUT.md"
New-Item -ItemType Directory -Force (Split-Path $INPUT) | Out-Null

# Choose the source of text
if ($FromClipboard)      { $content = Get-Clipboard -Raw }
elseif ($File)           { $content = Get-Content -Raw -LiteralPath $File }
elseif ($Text)           { $content = ($Text -join "`n") }
else                     { $content = [Console]::In.ReadToEnd() }

# Write the canonical input file
Set-Content -Encoding UTF8 $INPUT $content

# Ensure out/ is a folder (not a stray file)
if (Test-Path .\out -PathType Leaf) { Remove-Item .\out -Force }

# Run the pipeline
hdt2-run $INPUT
