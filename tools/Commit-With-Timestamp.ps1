param(
  [string]$RepoPath = ".",
  [string]$RemoteUrl = "https://github.com/tomacmulder/HDA.git",
  [string]$TagPrefix = "v",
  [string]$TagFormat = "yyyy.MM.dd-HHmmss",
  [switch]$AllowEmpty,

  # Optional automation
  [switch]$CreateFeatureBranch,        # new branch like feat/20251102-123456-snapshot
  [string]$BranchPrefix = "feat",
  [switch]$OpenPR,                     # requires GitHub CLI (run: gh auth login)
  [switch]$AutoMerge,                  # auto-merge the PR (merge commit)
  [switch]$CreateRelease,              # create a GitHub Release for the tag
  [switch]$Cleanup                     # delete feature branch (local + remote) after merge
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

function Test-Gh { return [bool](Get-Command gh -ErrorAction SilentlyContinue) }

function Test-RemoteBranchExists($git, $branch) {
  & $git ls-remote --exit-code --heads origin $branch 1>$null 2>$null
  return ($LASTEXITCODE -eq 0)
}

# 0) Enter repo and resolve tools
Set-Location -LiteralPath $RepoPath
$git   = Get-Git
$hasGh = Test-Gh

# 1) Ensure repo exists; help with long OneDrive paths
& $git rev-parse --is-inside-work-tree 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Initializing new git repository..."
  & $git init | Out-Null
  & $git config core.longpaths true
}

# 2) Choose branch
if ($CreateFeatureBranch) {
  $slug = (Get-Date -Format 'yyyyMMdd-HHmmss') + "-snapshot"
  $branch = "$BranchPrefix/$slug"
  & $git checkout -B $branch
} else {
  $branch = (& $git rev-parse --abbrev-ref HEAD).Trim()
  if (-not $branch -or $branch -eq "HEAD") { $branch = "main"; & $git checkout -B $branch }
}

# 3) Ensure 'origin' is your repo
$currRemote = ""; try { $currRemote = (& $git remote get-url origin).Trim() } catch {}
if (-not $currRemote) { & $git remote add origin $RemoteUrl; Write-Host "Added remote 'origin' -> $RemoteUrl" }
elseif ($currRemote -ne $RemoteUrl) { & $git remote set-url origin $RemoteUrl; Write-Host "Updated remote 'origin' -> $RemoteUrl" }

# 4) Pull only if this branch exists on origin (avoids 'remote ref' fatal)
if (Test-RemoteBranchExists $git $branch) {
  try { & $git pull --ff-only origin $branch } catch {}
}

# 5) Stage and commit with timestamp
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
& $git add -A
& $git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  if ($AllowEmpty) { & $git commit -m "chore(snapshot): $ts" --allow-empty }
  else { Write-Host "No changes to commit (use -AllowEmpty to force a checkpoint)."; return }
} else {
  & $git commit -m "chore(snapshot): $ts"
}

# 6) Unique timestamp tag (avoid collisions if run multiple times in the same second)
$base = "$TagPrefix$(Get-Date -Format $TagFormat)"
$version = $base
$idx = 1
& $git rev-parse -q --verify "refs/tags/$version" 1>$null 2>$null
while ($LASTEXITCODE -eq 0) {
  $version = "$base-$idx"
  $idx++
  & $git rev-parse -q --verify "refs/tags/$version" 1>$null 2>$null
}
& $git tag -a $version -m "Release $version"

# 7) Push branch (set upstream) and tag
& $git push -u origin $branch
& $git push origin $version
Write-Host "Pushed branch '$branch' and tag '$version' to $RemoteUrl"

# 8) Optional: open PR / auto-merge / create release
$merged = $false
if ($OpenPR -and $hasGh -and $branch -ne "main") {
  try {
    gh pr create --base main --head $branch --title "chore(snapshot): $ts" --body "Automated snapshot. Tag: $version" 2>$null
    if ($AutoMerge) { gh pr merge --merge --delete-branch --auto 2>$null }
  } catch { Write-Host "Note: gh CLI action failed. Run 'gh auth login' and try again." }
  # Recheck merge state (best-effort)
  try {
    $state = (gh pr view --json merged --jq .merged 2>$null)
    if ($state -eq "true") { $merged = $true }
  } catch {}
} elseif ($OpenPR -and -not $hasGh) {
  Write-Host "Note: gh CLI not found. Install: winget install GitHub.cli"
}

# 9) Optional cleanup: delete the feature branch after it's merged into main (safe)
if ($Cleanup -and $branch -ne "main") {
  & $git fetch origin --prune
  # Consider merged if PR merged OR branch is ancestor of main on origin
  if (-not $merged) {
    & $git merge-base --is-ancestor "origin/$branch" "origin/main"
    if ($LASTEXITCODE -eq 0) { $merged = $true }
  }
  if ($merged) {
    try {
      & $git checkout main
      try { & $git pull --ff-only origin main } catch {}
      & $git branch -D $branch 2>$null
      & $git push origin --delete $branch 2>$null
      & $git fetch -p
      Write-Host "Cleaned up feature branch '$branch' (local + remote)."
    } catch { Write-Host "Cleanup skipped: unable to delete '$branch' safely." }
  } else {
    Write-Host "Cleanup skipped: '$branch' is not merged into main."
  }
}

# 10) Optional: create a Release from the tag
if ($CreateRelease -and $hasGh) {
  try { gh release create $version --generate-notes -t $version 2>$null } catch { Write-Host "Note: release creation failed." }
}
