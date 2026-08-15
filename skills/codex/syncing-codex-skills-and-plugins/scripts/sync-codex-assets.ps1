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

function Get-UnitsFingerprint {
    param([object[]]$Units)

    $lines = @($Units | ForEach-Object { "$($_.identity)`t$($_.hash)" })
    [Array]::Sort($lines, [StringComparer]::Ordinal)
    $payload = if ($lines.Count -gt 0) { ($lines -join "`n") + "`n" } else { '' }
    return Get-TextSha256 -Text $payload
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
        blockers = @()
        planSha256 = ''
    }
    $plan.planSha256 = Get-TextSha256 -Text ($plan | ConvertTo-Json -Depth 50 -Compress)
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

function Resolve-Inputs {
    if ([string]::IsNullOrWhiteSpace($script:TargetUserRoot)) {
        $script:TargetUserRoot = [Environment]::GetFolderPath('UserProfile')
    }
    if ([string]::IsNullOrWhiteSpace($script:WorkspaceRoot)) {
        $script:WorkspaceRoot = Join-Path $script:TargetUserRoot '.codex\sync-workspaces'
    }
    if ([string]::IsNullOrWhiteSpace($script:PlanPath)) {
        $script:PlanPath = Join-Path $script:WorkspaceRoot 'latest-plan.json'
    }
    if ([string]::IsNullOrWhiteSpace($script:ReportPath)) {
        $script:ReportPath = Join-Path $script:TargetUserRoot '.codex\sync-reports\latest.json'
    }
    if ([string]::IsNullOrWhiteSpace($script:RepoRoot)) {
        throw 'RepoRoot is required until managed GitHub workspace support is enabled.'
    }
    $script:RepoRoot = [IO.Path]::GetFullPath($script:RepoRoot)
    $script:TargetUserRoot = [IO.Path]::GetFullPath($script:TargetUserRoot)
}

Resolve-Inputs

if ($Mode -eq 'Plan') {
    if ($Direction -ne 'CloudToLocal') {
        throw 'LocalToCloud planning is not implemented yet.'
    }
    $sourceUnits = @(Get-CloudSourceUnits -PackageRoot $RepoRoot)
    $targetUnits = @(Get-LocalTargetUnits -UserRoot $TargetUserRoot)
    $plan = New-SyncPlan -PlanDirection $Direction -SourceUnits $sourceUnits -TargetUnits $targetUnits -UserRoot $TargetUserRoot -RepositoryUrl $RepoUrl
    Write-JsonUtf8 -Value $plan -Path $PlanPath
    Write-Host "Plan created: $PlanPath"
    Write-Host "add=$($plan.summary.add) identical=$($plan.summary.identical) conflict=$($plan.summary.conflict) extra=$($plan.summary.extra)"
    exit 0
}

if ($Mode -eq 'Apply') {
    throw 'Apply mode is not implemented yet.'
}

throw 'Verify mode is not implemented yet.'
