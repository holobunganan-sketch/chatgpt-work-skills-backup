[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$errors = [System.Collections.Generic.List[string]]::new()

function Add-CheckError {
    param([string]$Message)
    $errors.Add($Message)
    Write-Host "[failed] $Message" -ForegroundColor Red
}

function Test-SkillRoot {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        Add-CheckError "Missing skill root: $Path"
        return
    }
    Get-ChildItem -LiteralPath $Path -Directory -Force | ForEach-Object {
        if ($_.Name -eq '.shared') {
            return
        }
        $hasFiles = Get-ChildItem -LiteralPath $_.FullName -File -Recurse -Force | Select-Object -First 1
        if ($null -eq $hasFiles) {
            return
        }
        $skillFile = Join-Path $_.FullName 'SKILL.md'
        if (-not (Test-Path -LiteralPath $skillFile)) {
            Add-CheckError "Missing SKILL.md: $($_.FullName)"
        }
    }
}

Test-SkillRoot -Path (Join-Path $repoRoot 'skills\codex')
Test-SkillRoot -Path (Join-Path $repoRoot 'skills\agents')

$sharedReferenceRoot = Join-Path $repoRoot 'skills\codex\.shared\submission-grade-research-core\references'
@('execution-contract.md', 'workflow-core.md', 'language-and-integrity.md', 'submission-assets.md', 'manuscript-gate.md') | ForEach-Object {
    $sharedFile = Join-Path $sharedReferenceRoot $_
    if (-not (Test-Path -LiteralPath $sharedFile)) {
        Add-CheckError "Missing shared reference: $sharedFile"
    }
}

$pluginRoot = Join-Path $repoRoot 'plugins\medical-manuscript-workflow'
$pluginManifest = Join-Path $pluginRoot '.codex-plugin\plugin.json'
if (-not (Test-Path -LiteralPath $pluginManifest)) {
    Add-CheckError "Missing plugin manifest: $pluginManifest"
}
else {
    $plugin = Get-Content -Raw -LiteralPath $pluginManifest | ConvertFrom-Json
    if ($plugin.name -ne 'medical-manuscript-workflow') {
        Add-CheckError "Unexpected plugin name: $($plugin.name)"
    }
}

$marketplacePath = Join-Path $repoRoot 'marketplace\marketplace.json'
if (-not (Test-Path -LiteralPath $marketplacePath)) {
    Add-CheckError "Missing marketplace: $marketplacePath"
}
else {
    $marketplace = Get-Content -Raw -LiteralPath $marketplacePath | ConvertFrom-Json
    if (-not ($marketplace.plugins | Where-Object { $_.name -eq 'medical-manuscript-workflow' })) {
        Add-CheckError 'Marketplace entry for medical-manuscript-workflow was not found.'
    }
}

$hashPath = Join-Path $repoRoot 'SHA256SUMS.txt'
if (Test-Path -LiteralPath $hashPath) {
    Get-Content -LiteralPath $hashPath | ForEach-Object {
        if ($_ -match '^([A-Fa-f0-9]{64}) \*(.+)$') {
            $expected = $Matches[1].ToUpperInvariant()
            $relativePath = $Matches[2].Replace('/', [IO.Path]::DirectorySeparatorChar)
            $filePath = Join-Path $repoRoot $relativePath
            if (-not (Test-Path -LiteralPath $filePath)) {
                Add-CheckError "Missing hashed file: $relativePath"
            }
            else {
                $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $filePath).Hash
                if ($actual -ne $expected) {
                    Add-CheckError "Hash mismatch: $relativePath"
                }
            }
        }
        elseif (-not [string]::IsNullOrWhiteSpace($_)) {
            Add-CheckError "Invalid hash line: $_"
        }
    }
}
else {
    Add-CheckError "Missing hash manifest: $hashPath"
}

if ($errors.Count -gt 0) {
    Write-Host "Verification failed with $($errors.Count) error(s)." -ForegroundColor Red
    exit 1
}

$skillCount = (Get-ChildItem -LiteralPath (Join-Path $repoRoot 'skills') -Filter 'SKILL.md' -File -Recurse -Force).Count
$fileCount = (Get-ChildItem -LiteralPath $repoRoot -File -Recurse -Force | Where-Object { $_.FullName -notmatch '\\.git\\' }).Count
Write-Host "Verification passed: $skillCount skills, $fileCount package files."
exit 0
