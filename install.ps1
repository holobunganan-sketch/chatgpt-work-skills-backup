[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$TargetUserRoot = [Environment]::GetFolderPath('UserProfile')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$engine = Join-Path $repoRoot 'skills\codex\syncing-codex-skills-and-plugins\scripts\sync-codex-assets.ps1'
$verifyScript = Join-Path $repoRoot 'verify.ps1'
$targetRoot = [IO.Path]::GetFullPath($TargetUserRoot)
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$workspace = Join-Path $targetRoot '.codex\sync-workspaces'
$planPath = Join-Path $workspace "install-plan-$timestamp.json"
$reportPath = Join-Path $targetRoot ".codex\sync-reports\install-$timestamp.json"

function Write-Step {
    param([string]$Message)
    Write-Host "[migration] $Message"
}

if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) {
    throw "Missing sync engine: $engine"
}
if (-not (Test-Path -LiteralPath $verifyScript -PathType Leaf)) {
    throw "Missing verification script: $verifyScript"
}

Write-Step 'Verifying the migration package.'
& $verifyScript
if ($LASTEXITCODE -ne 0) {
    throw 'Package verification failed. Installation stopped.'
}

Write-Step 'Building an idempotent cloud-to-local plan.'
& $engine `
    -Mode Plan `
    -Direction CloudToLocal `
    -RepoRoot $repoRoot `
    -TargetUserRoot $targetRoot `
    -WorkspaceRoot $workspace `
    -PlanPath $planPath `
    -ReportPath $reportPath
if ($LASTEXITCODE -ne 0) {
    throw 'Installation planning failed.'
}

$plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
Write-Step "Plan: add=$($plan.summary.add), identical=$($plan.summary.identical), conflict=$($plan.summary.conflict), extra=$($plan.summary.extra)."
if ($plan.summary.conflict -gt 0) {
    Write-Step 'Conflicting local items will be preserved. Invoke the sync skill for a source-wins confirmation.'
}

if ($DryRun) {
    Write-Step "Dry run completed. No target files were changed. Plan: $planPath"
    exit 0
}

Write-Step 'Applying missing items and skipping identical or conflicting targets.'
& $engine `
    -Mode Apply `
    -Direction CloudToLocal `
    -Decision KeepTarget `
    -RepoRoot $repoRoot `
    -TargetUserRoot $targetRoot `
    -WorkspaceRoot $workspace `
    -PlanPath $planPath `
    -ReportPath $reportPath
$applyExit = $LASTEXITCODE
if ($applyExit -ne 0) {
    throw "Installation stopped with sync exit code $applyExit. Report: $reportPath"
}

Write-Step "Installation completed. Report: $reportPath"
Write-Step 'Restart Codex so restored skills and plugin metadata are discovered in a new task.'
exit 0
