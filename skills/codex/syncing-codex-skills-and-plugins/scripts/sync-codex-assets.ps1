[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Plan', 'Apply', 'Verify')]
    [string]$Mode,

    [Parameter(Mandatory)]
    [ValidateSet('CloudToLocal', 'LocalToCloud')]
    [string]$Direction,

    [ValidateSet('KeepTarget', 'SourceWins', 'Cancel')]
    [string]$Decision = 'KeepTarget',

    [string]$RepoUrl = 'https://github.com/holobunganan-sketch/chatgpt-work-skills-backup.git',
    [string]$RepoRoot,
    [string]$TargetUserRoot,
    [string]$WorkspaceRoot,
    [string]$PlanPath,
    [string]$ReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:Utf8NoBom = [Text.UTF8Encoding]::new($false)
$script:ExcludedDirectoryNames = @('.git', '.system', '__pycache__')
$script:ExcludedFileNames = @('config.toml')
$script:ExcludedExtensions = @('.pyc', '.pyo', '.tmp', '.temp')

function Get-NormalizedRelativePath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Path
    )
    return [IO.Path]::GetRelativePath(
        [IO.Path]::GetFullPath($Root),
        [IO.Path]::GetFullPath($Path)
    ).Replace('\', '/')
}

function Test-ExcludedPath {
    param([Parameter(Mandatory)][string]$RelativePath)

    $normalized = $RelativePath.Replace('\', '/')
    $segments = @($normalized.Split('/', [StringSplitOptions]::RemoveEmptyEntries))
    foreach ($segment in $segments) {
        if ($script:ExcludedDirectoryNames -contains $segment) {
            return $true
        }
    }

    $leaf = if ($segments.Count -gt 0) { $segments[-1] } else { $normalized }
    if ($script:ExcludedFileNames -contains $leaf) {
        return $true
    }
    if ($leaf -like '.env*') {
        return $true
    }
    if ($script:ExcludedExtensions -contains [IO.Path]::GetExtension($leaf).ToLowerInvariant()) {
        return $true
    }
    return $false
}

function Get-BytesSha256 {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))
}

function Get-TextSha256 {
    param([AllowEmptyString()][string]$Text)
    return Get-BytesSha256 -Bytes $script:Utf8NoBom.GetBytes($Text)
}

function Get-FileSha256 {
    param([Parameter(Mandatory)][string]$Path)
    return Get-BytesSha256 -Bytes ([IO.File]::ReadAllBytes($Path))
}

function Get-TreeSha256 {
    param([Parameter(Mandatory)][string]$Root)

    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        return $null
    }

    $pathMap = @{}
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($file in Get-ChildItem -LiteralPath $Root -File -Recurse -Force) {
        $relative = Get-NormalizedRelativePath -Root $Root -Path $file.FullName
        if (Test-ExcludedPath -RelativePath $relative) {
            continue
        }
        $folded = $relative.ToUpperInvariant()
        if ($pathMap.ContainsKey($folded) -and $pathMap[$folded] -cne $relative) {
            throw "Case-only path collision in $Root`: $($pathMap[$folded]) and $relative"
        }
        $pathMap[$folded] = $relative
        $lines.Add("$relative`t$(Get-FileSha256 -Path $file.FullName)")
    }

    $ordered = $lines.ToArray()
    [Array]::Sort($ordered, [StringComparer]::Ordinal)
    $payload = if ($ordered.Count -gt 0) { ($ordered -join "`n") + "`n" } else { '' }
    return Get-TextSha256 -Text $payload
}

function Get-MarketplaceEntry {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    $marketplace = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    return @($marketplace.plugins | Where-Object { $_.name -eq 'medical-manuscript-workflow' }) | Select-Object -First 1
}

function Get-MarketplaceEntrySha256 {
    param([Parameter(Mandatory)][string]$Path)

    $entry = Get-MarketplaceEntry -Path $Path
    if ($null -eq $entry) {
        return $null
    }
    $normalized = [ordered]@{
        name = [string]$entry.name
        source = [string]$entry.source
    } | ConvertTo-Json -Compress
    return Get-TextSha256 -Text $normalized
}

function New-SyncUnit {
    param(
        [Parameter(Mandatory)][string]$Identity,
        [Parameter(Mandatory)][string]$DestinationRoot,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Path,
        [ValidateSet('directory', 'marketplace')][string]$Kind = 'directory'
    )

    $hash = if ($Kind -eq 'marketplace') {
        Get-MarketplaceEntrySha256 -Path $Path
    }
    else {
        Get-TreeSha256 -Root $Path
    }

    return [pscustomobject][ordered]@{
        identity = $Identity
        destinationRoot = $DestinationRoot
        name = $Name
        kind = $Kind
        path = [IO.Path]::GetFullPath($Path)
        hash = $hash
    }
}

function Get-DirectoryUnits {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$DestinationRoot,
        [switch]$RequireSkillManifest
    )

    $units = [System.Collections.Generic.List[object]]::new()
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        return @()
    }
    foreach ($directory in Get-ChildItem -LiteralPath $Root -Directory -Force) {
        if ($directory.Name -in @('.shared', '.system')) {
            continue
        }
        if ($RequireSkillManifest -and -not (Test-Path -LiteralPath (Join-Path $directory.FullName 'SKILL.md') -PathType Leaf)) {
            continue
        }
        $units.Add((New-SyncUnit -Identity "$DestinationRoot/$($directory.Name)" -DestinationRoot $DestinationRoot -Name $directory.Name -Path $directory.FullName))
    }
    return @($units)
}

function Get-CloudSourceUnits {
    param([Parameter(Mandatory)][string]$PackageRoot)

    $units = [System.Collections.Generic.List[object]]::new()
    foreach ($unit in Get-DirectoryUnits -Root (Join-Path $PackageRoot 'skills\codex') -DestinationRoot 'codex' -RequireSkillManifest) {
        $units.Add($unit)
    }
    foreach ($unit in Get-DirectoryUnits -Root (Join-Path $PackageRoot 'skills\agents') -DestinationRoot 'agents' -RequireSkillManifest) {
        $units.Add($unit)
    }

    $shared = Join-Path $PackageRoot 'skills\codex\.shared'
    if (Test-Path -LiteralPath $shared -PathType Container) {
        $units.Add((New-SyncUnit -Identity 'shared/.shared' -DestinationRoot 'shared' -Name '.shared' -Path $shared))
    }

    $plugin = Join-Path $PackageRoot 'plugins\medical-manuscript-workflow'
    if (Test-Path -LiteralPath $plugin -PathType Container) {
        $units.Add((New-SyncUnit -Identity 'plugin/medical-manuscript-workflow' -DestinationRoot 'plugin' -Name 'medical-manuscript-workflow' -Path $plugin))
    }

    $marketplace = Join-Path $PackageRoot 'marketplace\marketplace.json'
    if ($null -ne (Get-MarketplaceEntry -Path $marketplace)) {
        $units.Add((New-SyncUnit -Identity 'marketplace/medical-manuscript-workflow' -DestinationRoot 'marketplace' -Name 'medical-manuscript-workflow' -Path $marketplace -Kind 'marketplace'))
    }
    return @($units)
}

function Get-LocalTargetUnits {
    param([Parameter(Mandatory)][string]$UserRoot)

    $units = [System.Collections.Generic.List[object]]::new()
    foreach ($unit in Get-DirectoryUnits -Root (Join-Path $UserRoot '.codex\skills') -DestinationRoot 'codex' -RequireSkillManifest) {
        $units.Add($unit)
    }
    foreach ($unit in Get-DirectoryUnits -Root (Join-Path $UserRoot '.agents\skills') -DestinationRoot 'agents' -RequireSkillManifest) {
        $units.Add($unit)
    }

    $shared = Join-Path $UserRoot '.codex\skills\.shared'
    if (Test-Path -LiteralPath $shared -PathType Container) {
        $units.Add((New-SyncUnit -Identity 'shared/.shared' -DestinationRoot 'shared' -Name '.shared' -Path $shared))
    }

    $plugin = Join-Path $UserRoot 'plugins\medical-manuscript-workflow'
    if (Test-Path -LiteralPath $plugin -PathType Container) {
        $units.Add((New-SyncUnit -Identity 'plugin/medical-manuscript-workflow' -DestinationRoot 'plugin' -Name 'medical-manuscript-workflow' -Path $plugin))
    }

    $marketplace = Join-Path $UserRoot '.agents\plugins\marketplace.json'
    if ($null -ne (Get-MarketplaceEntry -Path $marketplace)) {
        $units.Add((New-SyncUnit -Identity 'marketplace/medical-manuscript-workflow' -DestinationRoot 'marketplace' -Name 'medical-manuscript-workflow' -Path $marketplace -Kind 'marketplace'))
    }
    return @($units)
}

function Get-SensitiveContentBlockers {
    param(
        [Parameter(Mandatory)][object[]]$Units,
        [Parameter(Mandatory)][string]$UserRoot
    )

    $blockers = [System.Collections.Generic.List[object]]::new()
    $secretPattern = '(?i)(github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)'
    $textExtensions = @('', '.cfg', '.env', '.ini', '.js', '.json', '.md', '.ps1', '.py', '.sh', '.toml', '.ts', '.txt', '.xml', '.yaml', '.yml')
    $visited = @{}

    foreach ($unit in $Units) {
        if ($unit.kind -eq 'marketplace' -or -not (Test-Path -LiteralPath $unit.path -PathType Container)) {
            continue
        }
        foreach ($file in Get-ChildItem -LiteralPath $unit.path -File -Recurse -Force) {
            $fullPath = [IO.Path]::GetFullPath($file.FullName)
            if ($visited.ContainsKey($fullPath)) {
                continue
            }
            $visited[$fullPath] = $true
            $relativeToUnit = Get-NormalizedRelativePath -Root $unit.path -Path $fullPath
            $reportPath = Get-NormalizedRelativePath -Root $UserRoot -Path $fullPath
            if ([IO.Path]::GetFileName($fullPath) -ieq 'config.toml') {
                $blockers.Add([pscustomobject][ordered]@{
                    ruleId = 'EXCLUDED_CONFIG'
                    path = $reportPath
                    message = 'Excluded configuration exists inside a synchronized unit.'
                })
                continue
            }
            if (Test-ExcludedPath -RelativePath $relativeToUnit) {
                continue
            }
            if ($file.Length -gt 95MB) {
                $blockers.Add([pscustomobject][ordered]@{
                    ruleId = 'FILE_TOO_LARGE'
                    path = $reportPath
                    message = 'File exceeds the 95 MiB synchronization limit.'
                })
                continue
            }
            $extension = [IO.Path]::GetExtension($file.Name).ToLowerInvariant()
            if ($textExtensions -notcontains $extension -or $file.Length -gt 5MB) {
                continue
            }
            try {
                $content = [IO.File]::ReadAllText($fullPath)
                if ($content -match $secretPattern) {
                    $blockers.Add([pscustomobject][ordered]@{
                        ruleId = 'SENSITIVE_CONTENT'
                        path = $reportPath
                        message = 'Token-like or private-key content detected.'
                    })
                }
            }
            catch {
                $blockers.Add([pscustomobject][ordered]@{
                    ruleId = 'UNREADABLE_TEXT'
                    path = $reportPath
                    message = 'Text-like file could not be inspected safely.'
                })
            }
        }
    }
    return @($blockers)
}

function Get-LocalRestoreEntries {
    param(
        [Parameter(Mandatory)][object[]]$LocalUnits,
        [Parameter(Mandatory)][string]$UserRoot
    )

    $entries = [System.Collections.Generic.List[object]]::new()
    $byIdentity = @{}
    foreach ($unit in $LocalUnits) {
        $byIdentity[$unit.identity] = $unit
    }

    $pluginSkillsRoot = Join-Path $UserRoot 'plugins\medical-manuscript-workflow\skills'
    $pluginSkills = @{}
    if (Test-Path -LiteralPath $pluginSkillsRoot -PathType Container) {
        foreach ($directory in Get-ChildItem -LiteralPath $pluginSkillsRoot -Directory -Force) {
            if (Test-Path -LiteralPath (Join-Path $directory.FullName 'SKILL.md') -PathType Leaf) {
                $pluginSkills[$directory.Name] = [pscustomobject]@{
                    path = $directory.FullName
                    hash = Get-TreeSha256 -Root $directory.FullName
                }
            }
        }
    }

    $mapped = @{}
    foreach ($destinationRoot in @('codex', 'agents')) {
        foreach ($identity in @($byIdentity.Keys | Where-Object { $_ -like "$destinationRoot/*" })) {
            $unit = $byIdentity[$identity]
            if ($pluginSkills.ContainsKey($unit.name) -and $pluginSkills[$unit.name].hash -eq $unit.hash) {
                $entries.Add([pscustomobject][ordered]@{
                    source = "plugins/medical-manuscript-workflow/skills/$($unit.name)"
                    destinationRoot = $destinationRoot
                    skillName = $unit.name
                    sourceTreeHash = $unit.hash
                })
                $mapped[$identity] = $true
            }
        }
    }

    foreach ($codexIdentity in @($byIdentity.Keys | Where-Object { $_ -like 'codex/*' })) {
        $codexUnit = $byIdentity[$codexIdentity]
        $agentIdentity = "agents/$($codexUnit.name)"
        if ($mapped.ContainsKey($agentIdentity) -or -not $byIdentity.ContainsKey($agentIdentity)) {
            continue
        }
        $agentUnit = $byIdentity[$agentIdentity]
        if ($codexUnit.hash -eq $agentUnit.hash) {
            $entries.Add([pscustomobject][ordered]@{
                source = "skills/codex/$($codexUnit.name)"
                destinationRoot = 'agents'
                skillName = $codexUnit.name
                sourceTreeHash = $codexUnit.hash
            })
            $mapped[$agentIdentity] = $true
        }
    }
    return @($entries | Sort-Object destinationRoot, skillName)
}

function Get-GitRemoteCommit {
    param([Parameter(Mandatory)][string]$RepositoryRoot)

    if (-not (Test-Path -LiteralPath (Join-Path $RepositoryRoot '.git'))) {
        return $null
    }
    & git -C $RepositoryRoot fetch origin main --quiet 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to fetch origin/main.'
    }
    $sha = (& git -C $RepositoryRoot rev-parse origin/main).Trim()
    if ($LASTEXITCODE -ne 0 -or $sha -notmatch '^[a-f0-9]{40}$') {
        throw 'Unable to resolve origin/main.'
    }
    return $sha
}

function Get-TargetPath {
    param(
        [Parameter(Mandatory)][string]$UserRoot,
        [Parameter(Mandatory)][string]$DestinationRoot,
        [Parameter(Mandatory)][string]$Name
    )

    switch ($DestinationRoot) {
        'codex' { return Join-Path $UserRoot ".codex\skills\$Name" }
        'agents' { return Join-Path $UserRoot ".agents\skills\$Name" }
        'shared' { return Join-Path $UserRoot '.codex\skills\.shared' }
        'plugin' { return Join-Path $UserRoot "plugins\$Name" }
        'marketplace' { return Join-Path $UserRoot '.agents\plugins\marketplace.json' }
        default { throw "Unsupported destination root: $DestinationRoot" }
    }
}

function Get-CloudTargetPath {
    param(
        [Parameter(Mandatory)][string]$PackageRoot,
        [Parameter(Mandatory)][string]$DestinationRoot,
        [Parameter(Mandatory)][string]$Name
    )

    switch ($DestinationRoot) {
        'codex' { return Join-Path $PackageRoot "skills\codex\$Name" }
        'agents' { return Join-Path $PackageRoot "skills\agents\$Name" }
        'shared' { return Join-Path $PackageRoot 'skills\codex\.shared' }
        'plugin' { return Join-Path $PackageRoot "plugins\$Name" }
        'marketplace' { return Join-Path $PackageRoot 'marketplace\marketplace.json' }
        default { throw "Unsupported destination root: $DestinationRoot" }
    }
}

function Get-UnitsFingerprint {
    param([object[]]$Units)

    $lines = @($Units | ForEach-Object { "$($_.identity)`t$($_.hash)" })
    [Array]::Sort($lines, [StringComparer]::Ordinal)
    $payload = if ($lines.Count -gt 0) { ($lines -join "`n") + "`n" } else { '' }
    return Get-TextSha256 -Text $payload
}

function Get-PlanIntegritySha256 {
    param([Parameter(Mandatory)]$Plan)

    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($name in @('schemaVersion', 'runId', 'state', 'direction', 'generatedAt', 'repository', 'sourceFingerprint', 'targetFingerprint', 'remoteCommit', 'rulesVersion')) {
        $lines.Add("$name`t$($Plan.$name)")
    }
    foreach ($item in @($Plan.items | Sort-Object identity)) {
        $lines.Add("item`t$($item.identity)`t$($item.destinationRoot)`t$($item.name)`t$($item.kind)`t$($item.classification)`t$($item.sourcePath)`t$($item.targetPath)`t$($item.sourceHash)`t$($item.targetHash)")
    }
    foreach ($name in @('add', 'identical', 'conflict', 'extra', 'deduplicated-source', 'blocked')) {
        $lines.Add("summary.$name`t$($Plan.summary.$name)")
    }
    foreach ($entry in @($Plan.restoreEntries | Sort-Object destinationRoot, skillName)) {
        $lines.Add("restore`t$($entry.source)`t$($entry.destinationRoot)`t$($entry.skillName)`t$($entry.sourceTreeHash)")
    }
    foreach ($blocker in @($Plan.blockers | Sort-Object ruleId, path)) {
        $lines.Add("blocker`t$($blocker.ruleId)`t$($blocker.path)`t$($blocker.message)")
    }
    return Get-TextSha256 -Text (($lines -join "`n") + "`n")
}

function New-SyncPlan {
    param(
        [Parameter(Mandatory)][string]$PlanDirection,
        [Parameter(Mandatory)][object[]]$SourceUnits,
        [Parameter(Mandatory)][object[]]$TargetUnits,
        [Parameter(Mandatory)][string]$UserRoot,
        [Parameter(Mandatory)][string]$RepositoryUrl
    )

    $sourceByIdentity = @{}
    $targetByIdentity = @{}
    foreach ($unit in $SourceUnits) { $sourceByIdentity[$unit.identity] = $unit }
    foreach ($unit in $TargetUnits) { $targetByIdentity[$unit.identity] = $unit }
    $identities = @($sourceByIdentity.Keys + $targetByIdentity.Keys | Sort-Object -Unique)

    $items = [System.Collections.Generic.List[object]]::new()
    foreach ($identity in $identities) {
        $source = if ($sourceByIdentity.ContainsKey($identity)) { $sourceByIdentity[$identity] } else { $null }
        $target = if ($targetByIdentity.ContainsKey($identity)) { $targetByIdentity[$identity] } else { $null }
        $classification = if ($null -eq $source) {
            'extra'
        }
        elseif ($null -eq $target) {
            'add'
        }
        elseif ($source.hash -eq $target.hash) {
            'identical'
        }
        else {
            'conflict'
        }

        $reference = if ($null -ne $source) { $source } else { $target }
        $items.Add([pscustomobject][ordered]@{
            identity = $identity
            destinationRoot = $reference.destinationRoot
            name = $reference.name
            kind = $reference.kind
            classification = $classification
            sourcePath = if ($null -ne $source) { $source.path } else { $null }
            targetPath = if ($null -ne $target) { $target.path } else { Get-TargetPath -UserRoot $UserRoot -DestinationRoot $reference.destinationRoot -Name $reference.name }
            sourceHash = if ($null -ne $source) { $source.hash } else { $null }
            targetHash = if ($null -ne $target) { $target.hash } else { $null }
        })
    }

    $summary = [ordered]@{
        add = @($items | Where-Object classification -eq 'add').Count
        identical = @($items | Where-Object classification -eq 'identical').Count
        conflict = @($items | Where-Object classification -eq 'conflict').Count
        extra = @($items | Where-Object classification -eq 'extra').Count
        'deduplicated-source' = 0
        blocked = 0
    }

    $plan = [pscustomobject][ordered]@{
        schemaVersion = 1
        runId = [guid]::NewGuid().ToString('N')
        state = 'planned'
        direction = $PlanDirection
        generatedAt = [DateTimeOffset]::UtcNow.ToString('o')
        repository = $RepositoryUrl
        sourceFingerprint = Get-UnitsFingerprint -Units $SourceUnits
        targetFingerprint = Get-UnitsFingerprint -Units $TargetUnits
        remoteCommit = $null
        rulesVersion = 1
        items = @($items)
        summary = [pscustomobject]$summary
        restoreEntries = @()
        blockers = @()
        planSha256 = ''
    }
    return $plan
}

function Write-JsonUtf8 {
    param(
        [Parameter(Mandatory)]$Value,
        [Parameter(Mandatory)][string]$Path
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $parent = Split-Path -Parent $fullPath
    if ($parent) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    [IO.File]::WriteAllText($fullPath, (($Value | ConvertTo-Json -Depth 50) + "`n"), $script:Utf8NoBom)
}

function Write-FinalizedPlan {
    param(
        [Parameter(Mandatory)]$Plan,
        [Parameter(Mandatory)][string]$Path
    )

    $Plan.planSha256 = ''
    Write-JsonUtf8 -Value $Plan -Path $Path
    $roundTripped = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    $roundTripped.planSha256 = Get-PlanIntegritySha256 -Plan $roundTripped
    Write-JsonUtf8 -Value $roundTripped -Path $Path
    return $roundTripped
}

function Read-AndValidatePlan {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Plan file not found: $Path"
    }
    $plan = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ($plan.schemaVersion -ne 1) {
        throw "Unsupported plan schema: $($plan.schemaVersion)"
    }
    if ($plan.planSha256 -notmatch '^[A-F0-9]{64}$') {
        throw 'Plan hash is missing or malformed.'
    }
    $expected = $plan.planSha256
    $actual = Get-PlanIntegritySha256 -Plan $plan
    if ($actual -ne $expected) {
        throw "Plan hash validation failed. Expected $expected, got $actual."
    }
    return $plan
}

function Get-CurrentItemHash {
    param(
        [Parameter(Mandatory)]$Item,
        [ValidateSet('Source', 'Target')][string]$Side
    )

    $path = if ($Side -eq 'Source') { $Item.sourcePath } else { $Item.targetPath }
    if ([string]::IsNullOrWhiteSpace([string]$path)) {
        return $null
    }
    if ($Item.kind -eq 'marketplace') {
        return Get-MarketplaceEntrySha256 -Path $path
    }
    return Get-TreeSha256 -Root $path
}

function Get-StalePlanReasons {
    param([Parameter(Mandatory)]$Plan)

    $reasons = [System.Collections.Generic.List[string]]::new()
    foreach ($item in $Plan.items) {
        $currentSource = Get-CurrentItemHash -Item $item -Side Source
        $currentTarget = Get-CurrentItemHash -Item $item -Side Target
        if ($currentSource -ne $item.sourceHash) {
            $reasons.Add("source:$($item.identity)")
        }
        if ($currentTarget -ne $item.targetHash) {
            $reasons.Add("target:$($item.identity)")
        }
    }
    return @($reasons)
}

function Assert-PathWithinUserRoot {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$UserRoot
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullRoot = [IO.Path]::GetFullPath($UserRoot).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $fullPath.StartsWith($fullRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escapes user root: $fullPath"
    }
    return $fullPath
}

function Assert-PathWithinRoot {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Root
    )
    return Assert-PathWithinUserRoot -Path $Path -UserRoot $Root
}

function Copy-PathExact {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    $parent = Split-Path -Parent $Destination
    if ($parent) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    if (Test-Path -LiteralPath $Source -PathType Container) {
        Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
    }
    else {
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
    }
}

function Remove-PathExact {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$UserRoot
    )

    $safePath = Assert-PathWithinUserRoot -Path $Path -UserRoot $UserRoot
    if (Test-Path -LiteralPath $safePath) {
        Remove-Item -LiteralPath $safePath -Recurse -Force
    }
}

function Backup-Target {
    param(
        [Parameter(Mandatory)][string]$TargetPath,
        [Parameter(Mandatory)][string]$UserRoot,
        [Parameter(Mandatory)][string]$BackupRoot
    )

    $safeTarget = Assert-PathWithinUserRoot -Path $TargetPath -UserRoot $UserRoot
    if (-not (Test-Path -LiteralPath $safeTarget)) {
        return $null
    }
    $relative = [IO.Path]::GetRelativePath([IO.Path]::GetFullPath($UserRoot), $safeTarget)
    if ($relative.StartsWith('..')) {
        throw "Cannot back up path outside user root: $safeTarget"
    }
    $backupPath = Join-Path $BackupRoot $relative
    Copy-PathExact -Source $safeTarget -Destination $backupPath
    return $backupPath
}

function Merge-MarketplaceEntry {
    param(
        [Parameter(Mandatory)][string]$SourcePath,
        [Parameter(Mandatory)][string]$TargetPath
    )

    $incoming = Get-MarketplaceEntry -Path $SourcePath
    if ($null -eq $incoming) {
        throw 'Incoming marketplace entry is missing.'
    }
    if (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
        $target = Get-Content -Raw -LiteralPath $TargetPath | ConvertFrom-Json
        if ($null -eq $target.plugins) {
            $target | Add-Member -MemberType NoteProperty -Name plugins -Value @()
        }
        $remaining = @($target.plugins | Where-Object { $_.name -ne 'medical-manuscript-workflow' })
        $target.plugins = @($remaining) + @($incoming)
    }
    else {
        $target = [pscustomobject][ordered]@{
            schemaVersion = 1
            plugins = @($incoming)
        }
    }
    Write-JsonUtf8 -Value $target -Path $TargetPath
}

function New-ApplyReport {
    param(
        [Parameter(Mandatory)]$Plan,
        [Parameter(Mandatory)][string]$ApplyDecision
    )

    return [pscustomobject][ordered]@{
        schemaVersion = 1
        runId = $Plan.runId
        state = 'approved'
        direction = $Plan.direction
        decision = $ApplyDecision
        planSha256 = $Plan.planSha256
        startedAt = [DateTimeOffset]::UtcNow.ToString('o')
        completedAt = $null
        summary = [pscustomobject][ordered]@{
            written = 0
            skipped = 0
            conflicts = @($Plan.items | Where-Object classification -eq 'conflict').Count
            backups = 0
        }
        actions = @()
        staleReasons = @()
        errors = @()
        rollback = @()
        gitCommit = $null
        remoteVerified = $false
    }
}

function Invoke-CloudToLocalApply {
    param(
        [Parameter(Mandatory)]$Plan,
        [Parameter(Mandatory)][string]$ApplyDecision,
        [Parameter(Mandatory)][string]$UserRoot,
        [Parameter(Mandatory)][string]$OutputReportPath
    )

    $report = New-ApplyReport -Plan $Plan -ApplyDecision $ApplyDecision
    if ($ApplyDecision -eq 'Cancel') {
        $report.state = 'cancelled'
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 2; Report = $report }
    }

    $staleReasons = @(Get-StalePlanReasons -Plan $Plan)
    if ($staleReasons.Count -gt 0) {
        $report.state = 'stale'
        $report.staleReasons = $staleReasons
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 3; Report = $report }
    }

    $backupRoot = Join-Path $UserRoot ".codex\sync-backups\$($Plan.runId)"
    $transaction = [System.Collections.Generic.List[object]]::new()
    $actions = [System.Collections.Generic.List[object]]::new()
    try {
        foreach ($item in $Plan.items) {
            $shouldWrite = $item.classification -eq 'add' -or ($item.classification -eq 'conflict' -and $ApplyDecision -eq 'SourceWins')
            if (-not $shouldWrite) {
                $actions.Add([pscustomobject]@{ identity = $item.identity; action = 'skipped'; classification = $item.classification })
                $report.summary.skipped++
                continue
            }

            $targetPath = Assert-PathWithinUserRoot -Path $item.targetPath -UserRoot $UserRoot
            $hadOriginal = Test-Path -LiteralPath $targetPath
            $backupPath = if ($hadOriginal) { Backup-Target -TargetPath $targetPath -UserRoot $UserRoot -BackupRoot $backupRoot } else { $null }
            if ($null -ne $backupPath) {
                $report.summary.backups++
            }
            $transaction.Add([pscustomobject]@{
                targetPath = $targetPath
                hadOriginal = $hadOriginal
                backupPath = $backupPath
            })

            if ($item.kind -eq 'marketplace') {
                Merge-MarketplaceEntry -SourcePath $item.sourcePath -TargetPath $targetPath
            }
            else {
                if ($hadOriginal) {
                    Remove-PathExact -Path $targetPath -UserRoot $UserRoot
                }
                Copy-PathExact -Source $item.sourcePath -Destination $targetPath
            }

            $actualHash = Get-CurrentItemHash -Item ([pscustomobject]@{
                kind = $item.kind
                sourcePath = $item.sourcePath
                targetPath = $targetPath
            }) -Side Target
            if ($actualHash -ne $item.sourceHash) {
                throw "Post-write hash mismatch: $($item.identity)"
            }
            $actions.Add([pscustomobject]@{ identity = $item.identity; action = 'written'; classification = $item.classification; backupPath = $backupPath })
            $report.summary.written++
        }

        $report.state = 'applied'
        $report.actions = @($actions)
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 0; Report = $report }
    }
    catch {
        $rollback = [System.Collections.Generic.List[object]]::new()
        for ($index = $transaction.Count - 1; $index -ge 0; $index--) {
            $entry = $transaction[$index]
            try {
                Remove-PathExact -Path $entry.targetPath -UserRoot $UserRoot
                if ($entry.hadOriginal) {
                    Copy-PathExact -Source $entry.backupPath -Destination $entry.targetPath
                }
                $rollback.Add([pscustomobject]@{ targetPath = $entry.targetPath; status = 'restored' })
            }
            catch {
                $rollback.Add([pscustomobject]@{ targetPath = $entry.targetPath; status = 'rollback-failed'; message = $_.Exception.Message })
            }
        }
        $report.state = 'failed'
        $report.actions = @($actions)
        $report.errors = @($_.Exception.Message)
        $report.rollback = @($rollback)
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 4; Report = $report }
    }
}

function Invoke-LocalToCloudApply {
    param(
        [Parameter(Mandatory)]$Plan,
        [Parameter(Mandatory)][string]$ApplyDecision,
        [Parameter(Mandatory)][string]$RepositoryRoot,
        [Parameter(Mandatory)][string]$SyncWorkspaceRoot,
        [Parameter(Mandatory)][string]$OutputReportPath
    )

    $report = New-ApplyReport -Plan $Plan -ApplyDecision $ApplyDecision
    if ($ApplyDecision -eq 'Cancel') {
        $report.state = 'cancelled'
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 2; Report = $report }
    }
    if (@($Plan.blockers).Count -gt 0) {
        $report.state = 'blocked'
        $report.errors = @($Plan.blockers | ForEach-Object { "$($_.ruleId):$($_.path)" })
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 2; Report = $report }
    }

    $remoteCommit = Get-GitRemoteCommit -RepositoryRoot $RepositoryRoot
    if ($remoteCommit -ne $Plan.remoteCommit) {
        $report.state = 'stale'
        $report.staleReasons = @('remote:origin/main')
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 3; Report = $report }
    }
    $staleReasons = @(Get-StalePlanReasons -Plan $Plan)
    if ($staleReasons.Count -gt 0) {
        $report.state = 'stale'
        $report.staleReasons = $staleReasons
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 3; Report = $report }
    }

    $dirty = @(& git -C $RepositoryRoot status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) {
        $report.state = 'blocked'
        $report.errors = @('Repository working tree is not clean.')
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 2; Report = $report }
    }

    $backupRoot = Join-Path $SyncWorkspaceRoot "local-to-cloud-backups\$($Plan.runId)"
    $transaction = [System.Collections.Generic.List[object]]::new()
    $actions = [System.Collections.Generic.List[object]]::new()
    try {
        foreach ($item in $Plan.items) {
            $shouldWrite = $item.classification -eq 'add' -or ($item.classification -eq 'conflict' -and $ApplyDecision -eq 'SourceWins')
            if (-not $shouldWrite) {
                $actions.Add([pscustomobject]@{ identity = $item.identity; action = 'skipped'; classification = $item.classification })
                $report.summary.skipped++
                continue
            }
            $targetPath = Assert-PathWithinRoot -Path $item.targetPath -Root $RepositoryRoot
            $hadOriginal = Test-Path -LiteralPath $targetPath
            $backupPath = if ($hadOriginal) { Backup-Target -TargetPath $targetPath -UserRoot $RepositoryRoot -BackupRoot $backupRoot } else { $null }
            $transaction.Add([pscustomobject]@{ targetPath = $targetPath; hadOriginal = $hadOriginal; backupPath = $backupPath })

            if ($item.kind -eq 'marketplace') {
                Merge-MarketplaceEntry -SourcePath $item.sourcePath -TargetPath $targetPath
            }
            else {
                if ($hadOriginal) {
                    Remove-PathExact -Path $targetPath -UserRoot $RepositoryRoot
                }
                Copy-PathExact -Source $item.sourcePath -Destination $targetPath
            }
            $actualHash = Get-CurrentItemHash -Item ([pscustomobject]@{ kind = $item.kind; sourcePath = $item.sourcePath; targetPath = $targetPath }) -Side Target
            if ($actualHash -ne $item.sourceHash) {
                throw "Post-write hash mismatch: $($item.identity)"
            }
            $actions.Add([pscustomobject]@{ identity = $item.identity; action = 'written'; classification = $item.classification })
            $report.summary.written++
        }

        if (@($Plan.restoreEntries).Count -gt 0) {
            $mapPath = Join-Path $RepositoryRoot 'restore-map.json'
            $hadMap = Test-Path -LiteralPath $mapPath
            $mapBackup = if ($hadMap) { Backup-Target -TargetPath $mapPath -UserRoot $RepositoryRoot -BackupRoot $backupRoot } else { $null }
            $transaction.Add([pscustomobject]@{ targetPath = $mapPath; hadOriginal = $hadMap; backupPath = $mapBackup })
            $map = [pscustomobject][ordered]@{ schemaVersion = 1; entries = @($Plan.restoreEntries) }
            Write-JsonUtf8 -Value $map -Path $mapPath
            foreach ($entry in $Plan.restoreEntries) {
                $identity = "$($entry.destinationRoot)/$($entry.skillName)"
                $item = @($Plan.items | Where-Object identity -eq $identity) | Select-Object -First 1
                if ($null -ne $item -and $item.classification -eq 'conflict' -and $ApplyDecision -eq 'KeepTarget') {
                    continue
                }
                $duplicatePath = Get-CloudTargetPath -PackageRoot $RepositoryRoot -DestinationRoot $entry.destinationRoot -Name $entry.skillName
                if (Test-Path -LiteralPath $duplicatePath) {
                    $duplicateBackup = Backup-Target -TargetPath $duplicatePath -UserRoot $RepositoryRoot -BackupRoot $backupRoot
                    $transaction.Add([pscustomobject]@{ targetPath = $duplicatePath; hadOriginal = $true; backupPath = $duplicateBackup })
                    Remove-PathExact -Path $duplicatePath -UserRoot $RepositoryRoot
                }
            }
        }

        & git -C $RepositoryRoot add -A -- skills/codex skills/agents plugins/medical-manuscript-workflow marketplace
        if (Test-Path -LiteralPath (Join-Path $RepositoryRoot 'restore-map.json')) {
            & git -C $RepositoryRoot add -- restore-map.json
        }
        if ($LASTEXITCODE -ne 0) {
            throw 'Git staging failed.'
        }
        & git -C $RepositoryRoot diff --cached --quiet
        if ($LASTEXITCODE -eq 1) {
            & git -C $RepositoryRoot commit -m 'Sync local Codex assets' | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw 'Git commit failed.'
            }
        }
        elseif ($LASTEXITCODE -ne 0) {
            throw 'Git staged-diff check failed.'
        }

        $commit = (& git -C $RepositoryRoot rev-parse HEAD).Trim()
        $report.gitCommit = $commit
        & git -C $RepositoryRoot push origin HEAD:main --quiet
        if ($LASTEXITCODE -ne 0) {
            throw 'Git push failed; local commit was retained.'
        }
        $reportedRemote = (& git -C $RepositoryRoot ls-remote origin refs/heads/main).Split("`t")[0]
        $report.remoteVerified = $reportedRemote -eq $commit
        if (-not $report.remoteVerified) {
            throw 'Remote commit verification failed.'
        }

        $report.state = 'applied'
        $report.actions = @($actions)
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 0; Report = $report }
    }
    catch {
        $rollback = [System.Collections.Generic.List[object]]::new()
        $headChanged = $null -ne $report.gitCommit
        if (-not $headChanged) {
            for ($index = $transaction.Count - 1; $index -ge 0; $index--) {
                $entry = $transaction[$index]
                try {
                    Remove-PathExact -Path $entry.targetPath -UserRoot $RepositoryRoot
                    if ($entry.hadOriginal) {
                        Copy-PathExact -Source $entry.backupPath -Destination $entry.targetPath
                    }
                    $rollback.Add([pscustomobject]@{ targetPath = $entry.targetPath; status = 'restored' })
                }
                catch {
                    $rollback.Add([pscustomobject]@{ targetPath = $entry.targetPath; status = 'rollback-failed'; message = $_.Exception.Message })
                }
            }
        }
        $report.state = 'failed'
        $report.actions = @($actions)
        $report.errors = @($_.Exception.Message)
        $report.rollback = @($rollback)
        $report.completedAt = [DateTimeOffset]::UtcNow.ToString('o')
        Write-JsonUtf8 -Value $report -Path $OutputReportPath
        return [pscustomobject]@{ ExitCode = 4; Report = $report }
    }
}

function Resolve-Inputs {
    if ([string]::IsNullOrWhiteSpace($script:TargetUserRoot)) {
        $script:TargetUserRoot = [Environment]::GetFolderPath('UserProfile')
    }
    if ([string]::IsNullOrWhiteSpace($script:WorkspaceRoot)) {
        $script:WorkspaceRoot = Join-Path $script:TargetUserRoot '.codex\sync-workspaces'
    }
    $script:WorkspaceRoot = [IO.Path]::GetFullPath($script:WorkspaceRoot)
    if ([string]::IsNullOrWhiteSpace($script:RepoRoot)) {
        if ($script:RepoUrl -match '^https://github\.com/') {
            if ($null -eq (Get-Command gh -ErrorAction SilentlyContinue)) {
                throw 'GitHub CLI is required for a private GitHub repository.'
            }
            & gh auth status 2>$null
            if ($LASTEXITCODE -ne 0) {
                throw 'GitHub CLI is not authenticated. Run gh auth login first.'
            }
        }
        $managedRoot = Join-Path $script:WorkspaceRoot 'chatgpt-work-skills-backup'
        if (-not (Test-Path -LiteralPath $managedRoot)) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $managedRoot) -Force | Out-Null
            & git clone --branch main --single-branch $script:RepoUrl $managedRoot --quiet
            if ($LASTEXITCODE -ne 0) {
                throw 'Unable to clone the synchronization repository.'
            }
        }
        elseif (-not (Test-Path -LiteralPath (Join-Path $managedRoot '.git'))) {
            throw "Managed workspace is not a Git repository: $managedRoot"
        }
        else {
            $dirty = @(& git -C $managedRoot status --porcelain)
            if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) {
                throw 'Managed synchronization repository contains uncommitted changes.'
            }
            & git -C $managedRoot fetch origin main --quiet
            if ($LASTEXITCODE -ne 0) {
                throw 'Unable to fetch the managed synchronization repository.'
            }
            & git -C $managedRoot switch main --quiet
            if ($LASTEXITCODE -ne 0) {
                throw 'Unable to switch the managed synchronization repository to main.'
            }
            & git -C $managedRoot merge --ff-only origin/main --quiet
            if ($LASTEXITCODE -ne 0) {
                throw 'Managed synchronization repository cannot fast-forward to origin/main.'
            }
        }
        $script:RepoRoot = $managedRoot
    }
    if ([string]::IsNullOrWhiteSpace($script:PlanPath)) {
        $script:PlanPath = Join-Path $script:WorkspaceRoot 'latest-plan.json'
    }
    if ([string]::IsNullOrWhiteSpace($script:ReportPath)) {
        $script:ReportPath = Join-Path $script:TargetUserRoot '.codex\sync-reports\latest.json'
    }
    $script:RepoRoot = [IO.Path]::GetFullPath($script:RepoRoot)
    $script:TargetUserRoot = [IO.Path]::GetFullPath($script:TargetUserRoot)
}

Resolve-Inputs

if ($Mode -eq 'Plan') {
    if ($Direction -eq 'CloudToLocal') {
        $sourceUnits = @(Get-CloudSourceUnits -PackageRoot $RepoRoot)
        $targetUnits = @(Get-LocalTargetUnits -UserRoot $TargetUserRoot)
        $plan = New-SyncPlan -PlanDirection $Direction -SourceUnits $sourceUnits -TargetUnits $targetUnits -UserRoot $TargetUserRoot -RepositoryUrl $RepoUrl
    }
    else {
        $sourceUnits = @(Get-LocalTargetUnits -UserRoot $TargetUserRoot)
        $targetUnits = @(Get-CloudSourceUnits -PackageRoot $RepoRoot)
        $plan = New-SyncPlan -PlanDirection $Direction -SourceUnits $sourceUnits -TargetUnits $targetUnits -UserRoot $TargetUserRoot -RepositoryUrl $RepoUrl
        foreach ($item in $plan.items) {
            if ($item.classification -eq 'add') {
                $item.targetPath = Get-CloudTargetPath -PackageRoot $RepoRoot -DestinationRoot $item.destinationRoot -Name $item.name
            }
        }
        $plan.restoreEntries = @(Get-LocalRestoreEntries -LocalUnits $sourceUnits -UserRoot $TargetUserRoot)
        $plan.summary.'deduplicated-source' = $plan.restoreEntries.Count
        $plan.blockers = @(Get-SensitiveContentBlockers -Units $sourceUnits -UserRoot $TargetUserRoot)
        $plan.summary.blocked = $plan.blockers.Count
        $plan.remoteCommit = Get-GitRemoteCommit -RepositoryRoot $RepoRoot
    }
    $plan = Write-FinalizedPlan -Plan $plan -Path $PlanPath
    Write-Host "Plan created: $PlanPath"
    Write-Host "add=$($plan.summary.add) identical=$($plan.summary.identical) conflict=$($plan.summary.conflict) extra=$($plan.summary.extra) deduplicated-source=$($plan.summary.'deduplicated-source') blocked=$($plan.summary.blocked)"
    if ($plan.summary.blocked -gt 0) {
        exit 2
    }
    exit 0
}

if ($Mode -eq 'Apply') {
    $plan = Read-AndValidatePlan -Path $PlanPath
    if ($plan.direction -ne $Direction) {
        throw "Plan direction $($plan.direction) does not match requested direction $Direction."
    }
    if ($Direction -eq 'CloudToLocal') {
        $result = Invoke-CloudToLocalApply -Plan $plan -ApplyDecision $Decision -UserRoot $TargetUserRoot -OutputReportPath $ReportPath
    }
    else {
        $result = Invoke-LocalToCloudApply -Plan $plan -ApplyDecision $Decision -RepositoryRoot $RepoRoot -SyncWorkspaceRoot $WorkspaceRoot -OutputReportPath $ReportPath
    }
    Write-Host "Sync state: $($result.Report.state)"
    Write-Host "written=$($result.Report.summary.written) skipped=$($result.Report.summary.skipped) conflicts=$($result.Report.summary.conflicts) backups=$($result.Report.summary.backups)"
    exit $result.ExitCode
}

throw 'Verify mode is not implemented yet.'
