param(
  [string]$RepoPath = ".",
  [string]$RemoteUrl = "https://github.com/tomacmulder/HDA.git",
  [string]$TagPrefix = "v",
  [string]$TagFormat = "yyyy.MM.dd-HHmmss",
  [switch]$AllowEmpty
)

$ErrorActionPreference = "Stop"

function Get-Git {
  $cmd = Get-Command git -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $candidates = @(
    "C:\Program Files\Git\cmd\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe",
    "C:\Program Files\Git\bin\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe"
  )
  foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
  throw "git.exe not found. Install Git or add it to PATH."
}

# 0) Enter repo and resolve git
Set-Location -LiteralPath $RepoPath
$git = Get-Git

# 1) Ensure repo exists; help with long OneDrive paths
& $git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Initializing new git repository..."
  & $git init | Out-Null
  & $git config core.longpaths true
}

# 2) Ensure we're on a branch (fallback to 'main' if detached)
$branch = (& $git rev-parse --abbrev-ref HEAD).Trim()
if (-not $branch -or $branch -eq "HEAD") {
  $branch = "main"
  & $git checkout -B $branch
}

# 3) Ensure 'origin' is wired to YOUR repo
$currRemote = ""
try { $currRemote = (& $git remote get-url origin).Trim() } catch {}
if (-not $currRemote) {
  & $git remote add origin $RemoteUrl
  Write-Host "Added remote 'origin' -> $RemoteUrl"
} elseif ($currRemote -ne $RemoteUrl) {
  & $git remote set-url origin $RemoteUrl
  Write-Host "Updated remote 'origin' -> $RemoteUrl"
}

# 4) Try a fast-forward pull (ignore errors if branch doesn't exist remotely yet)
try { & $git pull --ff-only origin $branch } catch {}

# 5) Stage and commit with timestamp
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
& $git add -A
& $git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  if ($AllowEmpty) {
    & $git commit -m "chore(snapshot): $ts" --allow-empty
  } else {
    Write-Host "No changes to commit (use -AllowEmpty to force a checkpoint)."
    return
  }
} else {
  & $git commit -m "chore(snapshot): $ts"
}

# 6) Create timestamp tag and push (e.g., v2025.11.02-145932)
$version = "$TagPrefix$(Get-Date -Format $TagFormat)"
& $git tag -a $version -m "Release $version"

# 7) Push commit (set upstream every time; harmless if already set) and push tag
& $git push -u origin $branch
& $git push origin $version

Write-Host "Pushed branch '$branch' and tag '$version' to $RemoteUrl"
