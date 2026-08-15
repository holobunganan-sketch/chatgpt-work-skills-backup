[CmdletBinding()]
param(
    [ValidateSet('All', 'Plan', 'CloudToLocal', 'LocalToCloud', 'Repository', 'SkillContract')]
    [string]$TestGroup = 'All'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:passed = 0
$script:failed = 0
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$engine = Join-Path $repoRoot 'skills\codex\syncing-codex-skills-and-plugins\scripts\sync-codex-assets.ps1'
$fixtureRoot = Join-Path $PSScriptRoot 'fixtures'

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

function Assert-Equal {
    param(
        $Actual,
        $Expected,
        [string]$Message
    )
    if ($Actual -ne $Expected) {
        throw "$Message. Expected [$Expected], got [$Actual]."
    }
}

function Invoke-Test {
    param(
        [string]$Name,
        [scriptblock]$Body
    )
    try {
        & $Body
        $script:passed++
        Write-Host "[pass] $Name" -ForegroundColor Green
    }
    catch {
        $script:failed++
        Write-Host "[fail] $Name`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function New-TestRoot {
    $path = Join-Path ([IO.Path]::GetTempPath()) ("codex-sync-test-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $path -Force | Out-Null
    return $path
}

function Write-Utf8File {
    param(
        [string]$Path,
        [string]$Content
    )
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    [IO.File]::WriteAllText($Path, $Content, [Text.UTF8Encoding]::new($false))
}

function New-TestSkill {
    param(
        [string]$Root,
        [string]$Name,
        [string]$Marker
    )
    $skillRoot = Join-Path $Root $Name
    New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
    Write-Utf8File -Path (Join-Path $skillRoot 'SKILL.md') -Content "---`nname: $Name`ndescription: Use when testing $Name.`n---`n`n# $Name`n`n$Marker`n"
    return $skillRoot
}

function Copy-TestTree {
    param(
        [string]$Source,
        [string]$Destination
    )
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Get-ChildItem -LiteralPath $Source -Force | Copy-Item -Destination $Destination -Recurse -Force
}

function New-TestPackage {
    param([string]$Root)

    $codex = Join-Path $Root 'skills\codex'
    $agents = Join-Path $Root 'skills\agents'
    New-Item -ItemType Directory -Path $codex, $agents -Force | Out-Null
    New-TestSkill -Root $codex -Name 'identical-skill' -Marker 'same' | Out-Null
    New-TestSkill -Root $codex -Name 'conflict-skill' -Marker 'source' | Out-Null
    New-TestSkill -Root $codex -Name 'missing-skill' -Marker 'source-only' | Out-Null
    Write-Utf8File -Path (Join-Path $codex 'identical-skill\scripts\__pycache__\ignored.pyc') -Content 'cache'

    $plugin = Join-Path $Root 'plugins\medical-manuscript-workflow'
    Write-Utf8File -Path (Join-Path $plugin '.codex-plugin\plugin.json') -Content '{"name":"medical-manuscript-workflow","version":"test"}'
    Write-Utf8File -Path (Join-Path $plugin 'SKILL.md') -Content "---`nname: plugin-test`ndescription: Use when testing.`n---`n"
    New-Item -ItemType Directory -Path (Join-Path $Root 'marketplace') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $fixtureRoot 'marketplace-incoming.json') -Destination (Join-Path $Root 'marketplace\marketplace.json')

    return $Root
}

function New-TestUserRoot {
    param(
        [string]$Root,
        [string]$PackageRoot
    )

    $codex = Join-Path $Root '.codex\skills'
    New-TestSkill -Root $codex -Name 'identical-skill' -Marker 'same' | Out-Null
    New-TestSkill -Root $codex -Name 'conflict-skill' -Marker 'target' | Out-Null
    New-TestSkill -Root $codex -Name 'extra-skill' -Marker 'target-only' | Out-Null
    Copy-TestTree -Source (Join-Path $PackageRoot 'plugins\medical-manuscript-workflow') -Destination (Join-Path $Root 'plugins\medical-manuscript-workflow')
    New-Item -ItemType Directory -Path (Join-Path $Root '.agents\plugins') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $fixtureRoot 'marketplace-existing.json') -Destination (Join-Path $Root '.agents\plugins\marketplace.json')
    return $Root
}

function Invoke-Engine {
    param(
        [string[]]$Arguments,
        [int]$ExpectedExitCode = 0
    )
    $output = & pwsh -NoProfile -File $engine @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne $ExpectedExitCode) {
        throw "Engine exit code $exitCode; expected $ExpectedExitCode. Output: $($output -join ' | ')"
    }
    return @($output)
}

function Get-PlanItem {
    param(
        $Plan,
        [string]$Identity
    )
    return @($Plan.items | Where-Object { $_.identity -eq $Identity }) | Select-Object -First 1
}

function Test-PlanClassification {
    $testRoot = New-TestRoot
    try {
        $package = New-TestPackage -Root (Join-Path $testRoot 'package')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $package
        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'
        $targetBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $userRoot '.codex\skills\conflict-skill\SKILL.md')).Hash

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null

        Assert-True (Test-Path -LiteralPath $planPath) 'Plan file was not created.'
        $plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
        Assert-Equal (Get-PlanItem -Plan $plan -Identity 'codex/identical-skill').classification 'identical' 'Identical skill classification'
        Assert-Equal (Get-PlanItem -Plan $plan -Identity 'codex/conflict-skill').classification 'conflict' 'Conflict skill classification'
        Assert-Equal (Get-PlanItem -Plan $plan -Identity 'codex/missing-skill').classification 'add' 'Missing skill classification'
        Assert-Equal (Get-PlanItem -Plan $plan -Identity 'codex/extra-skill').classification 'extra' 'Extra skill classification'
        Assert-True ($plan.planSha256 -match '^[A-F0-9]{64}$') 'Plan hash is missing or malformed.'
        $targetAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $userRoot '.codex\skills\conflict-skill\SKILL.md')).Hash
        Assert-Equal $targetAfter $targetBefore 'Plan mode changed a target file'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-CloudKeepTarget {
    $testRoot = New-TestRoot
    try {
        $package = New-TestPackage -Root (Join-Path $testRoot 'package')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $package
        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'
        $conflictPath = Join-Path $userRoot '.codex\skills\conflict-skill\SKILL.md'
        $conflictBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $conflictPath).Hash

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null
        Invoke-Engine -Arguments @('-Mode','Apply','-Direction','CloudToLocal','-Decision','KeepTarget','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null

        Assert-True (Test-Path -LiteralPath (Join-Path $userRoot '.codex\skills\missing-skill\SKILL.md')) 'Missing skill was not installed.'
        Assert-Equal (Get-FileHash -Algorithm SHA256 -LiteralPath $conflictPath).Hash $conflictBefore 'KeepTarget replaced a conflict.'
        Assert-True (Test-Path -LiteralPath (Join-Path $userRoot '.codex\skills\extra-skill\SKILL.md')) 'Extra target was removed.'
        $marketplace = Get-Content -Raw -LiteralPath (Join-Path $userRoot '.agents\plugins\marketplace.json') | ConvertFrom-Json
        Assert-True (@($marketplace.plugins | Where-Object { $_.name -eq 'unrelated-plugin' }).Count -eq 1) 'Marketplace merge removed unrelated entry.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-RepositoryContract {
    Assert-True (Test-Path -LiteralPath (Join-Path $repoRoot 'restore-map.json')) 'restore-map.json must exist.'
    $physical = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'skills'), (Join-Path $repoRoot 'plugins\medical-manuscript-workflow\skills') -Filter 'SKILL.md' -File -Recurse -Force)
    Assert-Equal $physical.Count 49 'Physical skill directory count'
}

function Test-SkillContract {
    $skillRoot = Join-Path $repoRoot 'skills\codex\syncing-codex-skills-and-plugins'
    Assert-True (Test-Path -LiteralPath (Join-Path $skillRoot 'SKILL.md')) 'SKILL.md must exist.'
    Assert-True (Test-Path -LiteralPath (Join-Path $skillRoot 'agents\openai.yaml')) 'agents/openai.yaml must exist.'
    Assert-True (Test-Path -LiteralPath (Join-Path $skillRoot 'references\SYNC_CONTRACT.md')) 'SYNC_CONTRACT.md must exist.'
}

if (-not (Test-Path -LiteralPath $engine)) {
    Write-Host '[fail] Sync engine must exist.' -ForegroundColor Red
    exit 1
}

if ($TestGroup -in @('All', 'Plan')) {
    Invoke-Test -Name 'plan classifies identical, conflict, add, and extra without writes' -Body { Test-PlanClassification }
}
if ($TestGroup -in @('All', 'CloudToLocal')) {
    Invoke-Test -Name 'cloud-to-local keep-target installs missing and preserves conflicts' -Body { Test-CloudKeepTarget }
}
if ($TestGroup -in @('All', 'LocalToCloud')) {
    Invoke-Test -Name 'local-to-cloud rejects an unimplemented safe upload path' -Body { throw 'LocalToCloud behavior is not implemented.' }
}
if ($TestGroup -in @('All', 'Repository')) {
    Invoke-Test -Name 'repository is deduplicated and mapped' -Body { Test-RepositoryContract }
}
if ($TestGroup -in @('All', 'SkillContract')) {
    Invoke-Test -Name 'skill package contains required files' -Body { Test-SkillContract }
}

Write-Host "Sync tests: $script:passed passed, $script:failed failed."
if ($script:failed -gt 0) {
    exit 1
}
exit 0
