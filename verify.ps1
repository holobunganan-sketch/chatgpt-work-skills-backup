[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$errors = [System.Collections.Generic.List[string]]::new()
$engine = Join-Path $repoRoot 'skills\codex\syncing-codex-skills-and-plugins\scripts\sync-codex-assets.ps1'
$engineSummary = $null

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

if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) {
    Add-CheckError "Missing sync engine: $engine"
}
else {
    $verifyTempRoot = Join-Path ([IO.Path]::GetTempPath()) ("codex-package-verify-" + [guid]::NewGuid().ToString('N'))
    $verifyReport = Join-Path $verifyTempRoot 'verify-report.json'
    try {
        New-Item -ItemType Directory -Path $verifyTempRoot -Force | Out-Null
        & pwsh -NoProfile -File $engine `
            -Mode Verify `
            -Direction CloudToLocal `
            -RepoRoot $repoRoot `
            -TargetUserRoot $verifyTempRoot `
            -WorkspaceRoot (Join-Path $verifyTempRoot 'workspace') `
            -ReportPath $verifyReport | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $engineErrors = if (Test-Path -LiteralPath $verifyReport) {
                @((Get-Content -Raw -LiteralPath $verifyReport | ConvertFrom-Json).errors) -join '; '
            }
            else {
                'No engine report was created.'
            }
            Add-CheckError "Sync-engine verification failed: $engineErrors"
        }
        else {
            $engineSummary = (Get-Content -Raw -LiteralPath $verifyReport | ConvertFrom-Json).summary
        }
    }
    finally {
        $resolvedTemp = [IO.Path]::GetFullPath($verifyTempRoot)
        $resolvedSystemTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
        if ($resolvedTemp.StartsWith($resolvedSystemTemp, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $resolvedTemp)) {
            Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
        }
    }
}

$inventoryPath = Join-Path $repoRoot 'inventory.json'
if (-not (Test-Path -LiteralPath $inventoryPath -PathType Leaf)) {
    Add-CheckError "Missing inventory: $inventoryPath"
}
elseif ($null -ne $engineSummary) {
    $inventory = Get-Content -Raw -LiteralPath $inventoryPath | ConvertFrom-Json
    foreach ($comparison in @(
        [pscustomobject]@{ name = 'physicalSkillSources'; actual = $engineSummary.physicalSkills }
        [pscustomobject]@{ name = 'restoreTargets'; actual = $engineSummary.restoreTargets }
        [pscustomobject]@{ name = 'logicalCodexSkills'; actual = $engineSummary.logicalCodexSkills }
        [pscustomobject]@{ name = 'logicalAgentSkills'; actual = $engineSummary.logicalAgentSkills }
    )) {
        if ($inventory.counts.($comparison.name) -ne $comparison.actual) {
            Add-CheckError "Inventory count mismatch for $($comparison.name): expected $($inventory.counts.($comparison.name)), actual $($comparison.actual)"
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
    $hashedPaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    Get-Content -LiteralPath $hashPath | ForEach-Object {
        if ($_ -match '^([A-Fa-f0-9]{64}) \*(.+)$') {
            $expected = $Matches[1].ToUpperInvariant()
            $manifestPath = $Matches[2].Replace('\', '/')
            if (-not $hashedPaths.Add($manifestPath)) {
                Add-CheckError "Duplicate hash entry: $manifestPath"
            }
            $relativePath = $manifestPath.Replace('/', [IO.Path]::DirectorySeparatorChar)
            $filePath = Join-Path $repoRoot $relativePath
            if (-not (Test-Path -LiteralPath $filePath)) {
                Add-CheckError "Missing hashed file: $relativePath"
            }
            else {
                $actual = [Convert]::ToHexString(
                    [Security.Cryptography.SHA256]::HashData(
                        [IO.File]::ReadAllBytes($filePath)
                    )
                )
                if ($actual -ne $expected) {
                    Add-CheckError "Hash mismatch: $relativePath"
                }
            }
        }
        elseif (-not [string]::IsNullOrWhiteSpace($_)) {
            Add-CheckError "Invalid hash line: $_"
        }
    }
    Get-ChildItem -LiteralPath $repoRoot -File -Recurse -Force | Where-Object {
        $_.FullName -notmatch '\\.git\\' -and $_.FullName -ne $hashPath
    } | ForEach-Object {
        $relative = [IO.Path]::GetRelativePath($repoRoot, $_.FullName).Replace('\', '/')
        if (-not $hashedPaths.Contains($relative)) {
            Add-CheckError "Unhashed package file: $relative"
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

$fileCount = (Get-ChildItem -LiteralPath $repoRoot -File -Recurse -Force | Where-Object { $_.FullName -notmatch '\\.git\\' }).Count
Write-Host "Verification passed: $($engineSummary.physicalSkills) physical skills, $($engineSummary.restoreTargets) restore targets, $($engineSummary.logicalCodexSkills) logical Codex skills, $($engineSummary.logicalAgentSkills) logical Agent skills, $fileCount package files."
exit 0
