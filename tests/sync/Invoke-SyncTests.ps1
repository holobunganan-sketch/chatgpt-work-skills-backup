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

function Get-TestTreeSha256 {
    param([Parameter(Mandatory)][string]$Root)

    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($file in Get-ChildItem -LiteralPath $Root -File -Recurse -Force) {
        $relative = [IO.Path]::GetRelativePath($Root, $file.FullName).Replace('\', '/')
        $segments = @($relative.Split('/', [StringSplitOptions]::RemoveEmptyEntries))
        if ($segments -contains '.git' -or $segments -contains '.system' -or $segments -contains '__pycache__') {
            continue
        }
        if ($file.Name -eq 'config.toml' -or $file.Name -like '.env*' -or $file.Extension.ToLowerInvariant() -in @('.pyc', '.pyo', '.tmp', '.temp')) {
            continue
        }
        $lines.Add("$relative`t$((Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash)")
    }
    $ordered = $lines.ToArray()
    [Array]::Sort($ordered, [StringComparer]::Ordinal)
    $payload = if ($ordered.Count -gt 0) { ($ordered -join "`n") + "`n" } else { '' }
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($payload)))
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

function Initialize-TestGitRemote {
    param(
        [Parameter(Mandatory)][string]$RepositoryRoot,
        [Parameter(Mandatory)][string]$BareRemoteRoot
    )

    & git -C $RepositoryRoot init -b main | Out-Null
    & git -C $RepositoryRoot config user.name 'Codex Sync Test'
    & git -C $RepositoryRoot config user.email 'codex-sync-test@example.invalid'
    & git -C $RepositoryRoot add --all
    & git -C $RepositoryRoot commit -m 'Initial package' | Out-Null
    & git init --bare $BareRemoteRoot | Out-Null
    & git -C $RepositoryRoot remote add origin $BareRemoteRoot
    & git -C $RepositoryRoot push -u origin main | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to initialize the temporary Git remote.'
    }
    & git --git-dir $BareRemoteRoot symbolic-ref HEAD refs/heads/main
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to set the temporary remote default branch.'
    }
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

function Test-CloudSourceWinsAndIdempotence {
    $testRoot = New-TestRoot
    try {
        $package = New-TestPackage -Root (Join-Path $testRoot 'package')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $package
        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'
        $conflictSource = Join-Path $package 'skills\codex\conflict-skill'
        $conflictTarget = Join-Path $userRoot '.codex\skills\conflict-skill'

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null
        $plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
        Invoke-Engine -Arguments @('-Mode','Apply','-Direction','CloudToLocal','-Decision','SourceWins','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null

        Assert-Equal (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $conflictTarget 'SKILL.md')).Hash (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $conflictSource 'SKILL.md')).Hash 'SourceWins did not replace the conflict.'
        $backupPath = Join-Path $userRoot ".codex\sync-backups\$($plan.runId)\.codex\skills\conflict-skill\SKILL.md"
        Assert-True (Test-Path -LiteralPath $backupPath) 'SourceWins did not create a conflict backup.'
        $marketplace = Get-Content -Raw -LiteralPath (Join-Path $userRoot '.agents\plugins\marketplace.json') | ConvertFrom-Json
        Assert-True (@($marketplace.plugins | Where-Object { $_.name -eq 'unrelated-plugin' }).Count -eq 1) 'SourceWins marketplace merge removed unrelated entry.'
        $medicalEntry = @($marketplace.plugins | Where-Object { $_.name -eq 'medical-manuscript-workflow' }) | Select-Object -First 1
        Assert-Equal -Actual $medicalEntry.source -Expected '../../plugins/medical-manuscript-workflow' -Message 'SourceWins did not update the marketplace entry.'

        $secondPlanPath = Join-Path $testRoot 'second-plan.json'
        $secondReportPath = Join-Path $testRoot 'second-report.json'
        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$secondPlanPath,'-ReportPath',$secondReportPath) | Out-Null
        $secondPlan = Get-Content -Raw -LiteralPath $secondPlanPath | ConvertFrom-Json
        Assert-Equal $secondPlan.summary.add 0 'Second run still has additions.'
        Assert-Equal $secondPlan.summary.conflict 0 'Second run still has conflicts.'
        Invoke-Engine -Arguments @('-Mode','Apply','-Direction','CloudToLocal','-Decision','KeepTarget','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$secondPlanPath,'-ReportPath',$secondReportPath) | Out-Null
        $secondReport = Get-Content -Raw -LiteralPath $secondReportPath | ConvertFrom-Json
        Assert-Equal $secondReport.summary.written 0 'Second run performed writes.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-CloudRejectsStalePlan {
    $testRoot = New-TestRoot
    try {
        $package = New-TestPackage -Root (Join-Path $testRoot 'package')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $package
        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null
        Add-Content -LiteralPath (Join-Path $userRoot '.codex\skills\conflict-skill\SKILL.md') -Value 'changed-after-plan'
        Invoke-Engine -Arguments @('-Mode','Apply','-Direction','CloudToLocal','-Decision','KeepTarget','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) -ExpectedExitCode 3 | Out-Null
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $userRoot '.codex\skills\missing-skill'))) 'Stale plan wrote a missing skill before stopping.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-RootInstallerDryRun {
    $testRoot = New-TestRoot
    try {
        $package = New-TestPackage -Root (Join-Path $testRoot 'package')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $package
        Copy-Item -LiteralPath (Join-Path $repoRoot 'install.ps1') -Destination (Join-Path $package 'install.ps1')
        Write-Utf8File -Path (Join-Path $package 'verify.ps1') -Content "exit 0`n"
        $engineDestination = Join-Path $package 'skills\codex\syncing-codex-skills-and-plugins\scripts\sync-codex-assets.ps1'
        New-Item -ItemType Directory -Path (Split-Path -Parent $engineDestination) -Force | Out-Null
        Copy-Item -LiteralPath $engine -Destination $engineDestination

        $output = & pwsh -NoProfile -File (Join-Path $package 'install.ps1') -DryRun -TargetUserRoot $userRoot 2>&1
        Assert-Equal $LASTEXITCODE 0 "Root installer dry run failed: $($output -join ' | ')"
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $userRoot '.codex\skills\missing-skill'))) 'Dry run installed a missing skill.'
        Assert-True (@(Get-ChildItem -LiteralPath (Join-Path $userRoot '.codex\sync-workspaces') -Filter 'install-plan-*.json' -File -ErrorAction SilentlyContinue).Count -eq 1) 'Dry run did not create one plan.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-CloudRestoresMappedDuplicate {
    $testRoot = New-TestRoot
    try {
        $package = New-TestPackage -Root (Join-Path $testRoot 'package')
        New-TestSkill -Root (Join-Path $package 'skills\codex') -Name 'duplicated-skill' -Marker 'mapped canonical copy' | Out-Null
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $package
        $hashPlanPath = Join-Path $testRoot 'hash-plan.json'
        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$hashPlanPath,'-ReportPath',(Join-Path $testRoot 'hash-report.json')) | Out-Null
        $hashPlan = Get-Content -Raw -LiteralPath $hashPlanPath | ConvertFrom-Json
        $canonical = Get-PlanItem -Plan $hashPlan -Identity 'codex/duplicated-skill'
        $map = [ordered]@{
            schemaVersion = 1
            entries = @([ordered]@{
                source = 'skills/codex/duplicated-skill'
                destinationRoot = 'agents'
                skillName = 'duplicated-skill'
                sourceTreeHash = $canonical.sourceHash
            })
        }
        Write-Utf8File -Path (Join-Path $package 'restore-map.json') -Content (($map | ConvertTo-Json -Depth 10) + "`n")

        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'
        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null
        $plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
        $mapped = Get-PlanItem -Plan $plan -Identity 'agents/duplicated-skill'
        Assert-Equal $mapped.classification 'add' 'Mapped Agent skill classification'
        Assert-Equal $mapped.sourcePath $canonical.sourcePath 'Mapped Agent skill did not reuse the canonical source.'
        Assert-Equal $plan.summary.'deduplicated-source' 1 'Cloud plan did not report its mapped duplicate.'

        Invoke-Engine -Arguments @('-Mode','Apply','-Direction','CloudToLocal','-Decision','KeepTarget','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null
        Assert-Equal (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $userRoot '.agents\skills\duplicated-skill\SKILL.md')).Hash (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $package 'skills\codex\duplicated-skill\SKILL.md')).Hash 'Mapped Agent skill content differs from the canonical source.'

        $secondPlanPath = Join-Path $testRoot 'second-plan.json'
        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$secondPlanPath,'-ReportPath',(Join-Path $testRoot 'second-report.json')) | Out-Null
        $secondPlan = Get-Content -Raw -LiteralPath $secondPlanPath | ConvertFrom-Json
        Assert-Equal (Get-PlanItem -Plan $secondPlan -Identity 'agents/duplicated-skill').classification 'identical' 'Mapped Agent skill was not idempotent.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-LocalToCloudSourceWins {
    $testRoot = New-TestRoot
    try {
        $repository = New-TestPackage -Root (Join-Path $testRoot 'repository')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $repository
        $remote = Join-Path $testRoot 'remote.git'
        Initialize-TestGitRemote -RepositoryRoot $repository -BareRemoteRoot $remote
        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','LocalToCloud','-RepoUrl',$remote,'-RepoRoot',$repository,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null
        $plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
        Assert-Equal (Get-PlanItem -Plan $plan -Identity 'codex/identical-skill').classification 'identical' 'LocalToCloud identical classification'
        Assert-Equal (Get-PlanItem -Plan $plan -Identity 'codex/conflict-skill').classification 'conflict' 'LocalToCloud conflict classification'
        Assert-Equal (Get-PlanItem -Plan $plan -Identity 'codex/extra-skill').classification 'add' 'LocalToCloud add classification'
        Assert-Equal (Get-PlanItem -Plan $plan -Identity 'codex/missing-skill').classification 'extra' 'LocalToCloud extra classification'

        Invoke-Engine -Arguments @('-Mode','Apply','-Direction','LocalToCloud','-Decision','SourceWins','-RepoUrl',$remote,'-RepoRoot',$repository,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null
        Assert-Equal (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repository 'skills\codex\conflict-skill\SKILL.md')).Hash (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $userRoot '.codex\skills\conflict-skill\SKILL.md')).Hash 'LocalToCloud SourceWins did not update conflict.'
        Assert-True (Test-Path -LiteralPath (Join-Path $repository 'skills\codex\extra-skill\SKILL.md')) 'LocalToCloud did not add a local-only skill.'
        $report = Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
        Assert-True ($report.gitCommit -match '^[a-f0-9]{40}$') 'LocalToCloud report lacks a Git commit.'
        Assert-Equal (& git --git-dir $remote rev-parse refs/heads/main) $report.gitCommit 'Temporary remote was not pushed to the reported commit.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-LocalToCloudBlocksSensitiveContent {
    $testRoot = New-TestRoot
    try {
        $repository = New-TestPackage -Root (Join-Path $testRoot 'repository')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $repository
        Copy-TestTree -Source (Join-Path $fixtureRoot 'fake-secret-skill') -Destination (Join-Path $userRoot '.codex\skills\fake-secret-skill')
        Write-Utf8File -Path (Join-Path $userRoot '.codex\skills\fake-secret-skill\config.toml') -Content 'excluded = true'
        $remote = Join-Path $testRoot 'remote.git'
        Initialize-TestGitRemote -RepositoryRoot $repository -BareRemoteRoot $remote
        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','LocalToCloud','-RepoUrl',$remote,'-RepoRoot',$repository,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) -ExpectedExitCode 2 | Out-Null
        $plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
        Assert-True (@($plan.blockers | Where-Object { $_.ruleId -eq 'SENSITIVE_CONTENT' }).Count -ge 1) 'Token-like content was not blocked.'
        Assert-True (@($plan.blockers | Where-Object { $_.ruleId -eq 'EXCLUDED_CONFIG' }).Count -eq 1) 'Nested config.toml was not blocked.'
        Assert-True (($plan.blockers | ConvertTo-Json -Depth 10) -notmatch 'github_pat_TESTONLY') 'Blocker report leaked the token-like value.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-LocalToCloudDeduplicatesExactSkills {
    $testRoot = New-TestRoot
    try {
        $repository = New-TestPackage -Root (Join-Path $testRoot 'repository')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $repository
        $duplicateSource = New-TestSkill -Root (Join-Path $userRoot '.codex\skills') -Name 'duplicated-skill' -Marker 'exact duplicate'
        Copy-TestTree -Source $duplicateSource -Destination (Join-Path $userRoot '.agents\skills\duplicated-skill')
        $remote = Join-Path $testRoot 'remote.git'
        Initialize-TestGitRemote -RepositoryRoot $repository -BareRemoteRoot $remote
        $planPath = Join-Path $testRoot 'plan.json'

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','LocalToCloud','-RepoUrl',$remote,'-RepoRoot',$repository,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',(Join-Path $testRoot 'report.json')) | Out-Null
        $plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
        Assert-Equal $plan.summary.'deduplicated-source' 1 'Exact Codex/Agent duplicate was not deduplicated.'
        Assert-True (@($plan.restoreEntries | Where-Object { $_.destinationRoot -eq 'agents' -and $_.skillName -eq 'duplicated-skill' }).Count -eq 1) 'Restore mapping for exact Agent duplicate is missing.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-LocalToCloudRejectsRemoteChange {
    $testRoot = New-TestRoot
    try {
        $repository = New-TestPackage -Root (Join-Path $testRoot 'repository')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $repository
        $remote = Join-Path $testRoot 'remote.git'
        Initialize-TestGitRemote -RepositoryRoot $repository -BareRemoteRoot $remote
        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'
        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','LocalToCloud','-RepoUrl',$remote,'-RepoRoot',$repository,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null

        $otherClone = Join-Path $testRoot 'other-clone'
        & git clone $remote $otherClone | Out-Null
        & git -C $otherClone config user.name 'Concurrent Test'
        & git -C $otherClone config user.email 'concurrent@example.invalid'
        Write-Utf8File -Path (Join-Path $otherClone 'concurrent.txt') -Content 'remote advanced'
        & git -C $otherClone add concurrent.txt
        & git -C $otherClone commit -m 'Concurrent change' | Out-Null
        & git -C $otherClone push origin main | Out-Null

        Invoke-Engine -Arguments @('-Mode','Apply','-Direction','LocalToCloud','-Decision','SourceWins','-RepoUrl',$remote,'-RepoRoot',$repository,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) -ExpectedExitCode 3 | Out-Null
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $repository 'skills\codex\extra-skill'))) 'Stale remote plan wrote local-only content.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-ManagedWorkspaceClone {
    $testRoot = New-TestRoot
    try {
        $seedRepository = New-TestPackage -Root (Join-Path $testRoot 'seed-repository')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $seedRepository
        $remote = Join-Path $testRoot 'remote.git'
        Initialize-TestGitRemote -RepositoryRoot $seedRepository -BareRemoteRoot $remote
        $workspace = Join-Path $testRoot 'workspace'
        $planPath = Join-Path $testRoot 'plan.json'

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','LocalToCloud','-RepoUrl',$remote,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',$workspace,'-PlanPath',$planPath,'-ReportPath',(Join-Path $testRoot 'report.json')) | Out-Null
        $managedRepository = Join-Path $workspace 'chatgpt-work-skills-backup'
        Assert-True (Test-Path -LiteralPath (Join-Path $managedRepository '.git')) 'Managed workspace was not cloned.'
        $plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
        Assert-True ($plan.remoteCommit -match '^[a-f0-9]{40}$') 'Managed workspace plan lacks the remote commit.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-LocalToCloudRetainsCommitWhenPushRejected {
    $testRoot = New-TestRoot
    try {
        $repository = New-TestPackage -Root (Join-Path $testRoot 'repository')
        $userRoot = New-TestUserRoot -Root (Join-Path $testRoot 'user') -PackageRoot $repository
        $remote = Join-Path $testRoot 'remote.git'
        Initialize-TestGitRemote -RepositoryRoot $repository -BareRemoteRoot $remote
        $remoteBefore = (& git --git-dir $remote rev-parse refs/heads/main).Trim()
        $planPath = Join-Path $testRoot 'plan.json'
        $reportPath = Join-Path $testRoot 'report.json'

        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','LocalToCloud','-RepoUrl',$remote,'-RepoRoot',$repository,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) | Out-Null
        Write-Utf8File -Path (Join-Path $remote 'hooks\pre-receive') -Content "#!/bin/sh`nexit 1`n"

        Invoke-Engine -Arguments @('-Mode','Apply','-Direction','LocalToCloud','-Decision','SourceWins','-RepoUrl',$remote,'-RepoRoot',$repository,'-TargetUserRoot',$userRoot,'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',$reportPath) -ExpectedExitCode 4 | Out-Null
        $report = Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
        $localHead = (& git -C $repository rev-parse HEAD).Trim()
        Assert-Equal $report.state 'failed' 'Rejected push report state'
        Assert-Equal $report.gitCommit $localHead 'Rejected push report did not retain the local commit identity'
        Assert-True (Test-Path -LiteralPath (Join-Path $repository 'skills\codex\extra-skill\SKILL.md')) 'Rejected push rolled back files from the retained commit.'
        Assert-Equal @($report.rollback).Count 0 'Rejected push performed a file rollback after committing.'
        Assert-Equal (& git --git-dir $remote rev-parse refs/heads/main) $remoteBefore 'Rejected push changed the remote branch.'
        Assert-Equal @(& git -C $repository status --porcelain).Count 0 'Rejected push left the repository dirty.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-RepositoryContract {
    Assert-True (Test-Path -LiteralPath (Join-Path $repoRoot 'restore-map.json')) 'restore-map.json must exist.'
    $restoreMap = Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'restore-map.json') | ConvertFrom-Json
    Assert-Equal $restoreMap.schemaVersion 1 'Restore-map schema version'
    Assert-Equal @($restoreMap.entries).Count 26 'Restore-map entry count'
    $identities = @($restoreMap.entries | ForEach-Object { "$($_.destinationRoot)/$($_.skillName)" })
    Assert-Equal @($identities | Sort-Object -Unique).Count 26 'Restore-map unique destination count'
    foreach ($entry in $restoreMap.entries) {
        $physicalTarget = if ($entry.destinationRoot -eq 'codex') {
            Join-Path $repoRoot "skills\codex\$($entry.skillName)"
        }
        else {
            Join-Path $repoRoot "skills\agents\$($entry.skillName)"
        }
        Assert-True (-not (Test-Path -LiteralPath $physicalTarget)) "Mapped duplicate still exists physically: $($entry.destinationRoot)/$($entry.skillName)"
    }
    $physical = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'skills'), (Join-Path $repoRoot 'plugins\medical-manuscript-workflow\skills') -Filter 'SKILL.md' -File -Recurse -Force)
    Assert-Equal $physical.Count 49 'Physical skill directory count'
    $physicalUnits = @($physical | ForEach-Object {
        [pscustomobject]@{
            name = $_.Directory.Name
            hash = Get-TestTreeSha256 -Root $_.Directory.FullName
        }
    })
    $exactDuplicateGroups = @($physicalUnits | Group-Object name | Where-Object {
        $_.Count -gt 1 -and @($_.Group.hash | Sort-Object -Unique).Count -eq 1
    })
    Assert-Equal $exactDuplicateGroups.Count 0 'Exact physical duplicate group count'

    $testRoot = New-TestRoot
    try {
        $planPath = Join-Path $testRoot 'repository-plan.json'
        Invoke-Engine -Arguments @('-Mode','Plan','-Direction','CloudToLocal','-RepoRoot',$repoRoot,'-TargetUserRoot',(Join-Path $testRoot 'empty-user'),'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-PlanPath',$planPath,'-ReportPath',(Join-Path $testRoot 'report.json')) | Out-Null
        $plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
        Assert-Equal $plan.summary.'deduplicated-source' 26 'Repository plan mapped duplicate count'
        Assert-Equal @($plan.items | Where-Object destinationRoot -eq 'codex').Count 37 'Logical Codex skill count'
        Assert-Equal @($plan.items | Where-Object destinationRoot -eq 'agents').Count 26 'Logical Agent skill count'
        Assert-Equal @($plan.items.identity | Sort-Object -Unique).Count @($plan.items).Count 'Repository plan contains duplicate identities'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-EngineVerifyRepository {
    $testRoot = New-TestRoot
    try {
        $reportPath = Join-Path $testRoot 'verify-report.json'
        Invoke-Engine -Arguments @('-Mode','Verify','-Direction','CloudToLocal','-RepoRoot',$repoRoot,'-TargetUserRoot',(Join-Path $testRoot 'user'),'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-ReportPath',$reportPath) | Out-Null
        $report = Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
        Assert-Equal $report.state 'verified' 'Repository verify state'
        Assert-Equal $report.summary.physicalSkills 49 'Repository verify physical skill count'
        Assert-Equal $report.summary.restoreTargets 26 'Repository verify restore target count'
        Assert-Equal $report.summary.logicalCodexSkills 37 'Repository verify logical Codex count'
        Assert-Equal $report.summary.logicalAgentSkills 26 'Repository verify logical Agent count'
        Assert-True (Test-Path -LiteralPath (Join-Path $testRoot "user\.codex\sync-reports\$($report.runId).json")) 'Repository verify did not archive a run-id report.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
}

function Test-EngineVerifyRejectsInvalidRestoreMap {
    $testRoot = New-TestRoot
    try {
        $package = New-TestPackage -Root (Join-Path $testRoot 'package')
        $map = [ordered]@{
            schemaVersion = 1
            entries = @([ordered]@{
                source = 'skills/codex/identical-skill'
                destinationRoot = 'agents'
                skillName = 'mapped-skill'
                sourceTreeHash = ('0' * 64)
            })
        }
        Write-Utf8File -Path (Join-Path $package 'restore-map.json') -Content (($map | ConvertTo-Json -Depth 10) + "`n")
        $reportPath = Join-Path $testRoot 'verify-report.json'
        Invoke-Engine -Arguments @('-Mode','Verify','-Direction','CloudToLocal','-RepoRoot',$package,'-TargetUserRoot',(Join-Path $testRoot 'user'),'-WorkspaceRoot',(Join-Path $testRoot 'workspace'),'-ReportPath',$reportPath) -ExpectedExitCode 2 | Out-Null
        $report = Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
        Assert-Equal $report.state 'blocked' 'Invalid restore-map verify state'
        Assert-True (@($report.errors | Where-Object { $_ -match 'hash mismatch' }).Count -eq 1) 'Invalid restore-map hash was not reported.'
    }
    finally {
        if (Test-Path -LiteralPath $testRoot) {
            Remove-Item -LiteralPath $testRoot -Recurse -Force
        }
    }
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
    Invoke-Test -Name 'cloud-to-local source-wins backs up conflicts and is idempotent' -Body { Test-CloudSourceWinsAndIdempotence }
    Invoke-Test -Name 'cloud-to-local rejects a stale plan before writing' -Body { Test-CloudRejectsStalePlan }
    Invoke-Test -Name 'root installer dry run delegates without writing targets' -Body { Test-RootInstallerDryRun }
    Invoke-Test -Name 'cloud-to-local restores mapped duplicates from one canonical source' -Body { Test-CloudRestoresMappedDuplicate }
}
if ($TestGroup -in @('All', 'LocalToCloud')) {
    Invoke-Test -Name 'local-to-cloud source-wins commits and pushes through a temporary remote' -Body { Test-LocalToCloudSourceWins }
    Invoke-Test -Name 'local-to-cloud blocks token-like content and excluded configuration' -Body { Test-LocalToCloudBlocksSensitiveContent }
    Invoke-Test -Name 'local-to-cloud creates a restore map for exact skill duplicates' -Body { Test-LocalToCloudDeduplicatesExactSkills }
    Invoke-Test -Name 'local-to-cloud rejects a plan after the remote advances' -Body { Test-LocalToCloudRejectsRemoteChange }
    Invoke-Test -Name 'local-to-cloud clones a managed workspace when RepoRoot is omitted' -Body { Test-ManagedWorkspaceClone }
    Invoke-Test -Name 'local-to-cloud retains its commit when the remote rejects a push' -Body { Test-LocalToCloudRetainsCommitWhenPushRejected }
}
if ($TestGroup -in @('All', 'Repository')) {
    Invoke-Test -Name 'repository is deduplicated and mapped' -Body { Test-RepositoryContract }
    Invoke-Test -Name 'engine verify reports repository physical and logical counts' -Body { Test-EngineVerifyRepository }
    Invoke-Test -Name 'engine verify rejects an invalid restore-map hash' -Body { Test-EngineVerifyRejectsInvalidRestoreMap }
}
if ($TestGroup -in @('All', 'SkillContract')) {
    Invoke-Test -Name 'skill package contains required files' -Body { Test-SkillContract }
}

Write-Host "Sync tests: $script:passed passed, $script:failed failed."
if ($script:failed -gt 0) {
    exit 1
}
exit 0
