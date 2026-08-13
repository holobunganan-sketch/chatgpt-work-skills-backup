[CmdletBinding()]
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$userRoot = [Environment]::GetFolderPath('UserProfile')
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupRoot = Join-Path $userRoot "ChatGPT-Work-migration-backups\$timestamp"
$backupCreated = $false

function Write-Step {
    param([string]$Message)
    Write-Host "[migration] $Message"
}

function Ensure-Directory {
    param([string]$Path)
    if ($DryRun) {
        Write-Step "Would ensure directory: $Path"
        return
    }
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Backup-ExistingPath {
    param(
        [string]$Path,
        [string]$RelativeBackupPath
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    $backupPath = Join-Path $backupRoot $RelativeBackupPath
    if ($DryRun) {
        Write-Step "Would back up $Path to $backupPath"
        return
    }
    $backupParent = Split-Path -Parent $backupPath
    New-Item -ItemType Directory -Force -Path $backupParent | Out-Null
    Copy-Item -LiteralPath $Path -Destination $backupPath -Recurse -Force
    $script:backupCreated = $true
}

function Merge-Directory {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$BackupPrefix
    )
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing source directory: $Source"
    }
    Ensure-Directory -Path $Destination
    Get-ChildItem -LiteralPath $Source -Directory -Force | ForEach-Object {
        $target = Join-Path $Destination $_.Name
        if (Test-Path -LiteralPath $target) {
            Backup-ExistingPath -Path $target -RelativeBackupPath (Join-Path $BackupPrefix $_.Name)
        }
        if ($DryRun) {
            Write-Step "Would merge $($_.FullName) into $target"
        }
        else {
            New-Item -ItemType Directory -Force -Path $target | Out-Null
            Get-ChildItem -LiteralPath $_.FullName -Force | Copy-Item -Destination $target -Recurse -Force
        }
    }
}

function Install-PersonalMarketplace {
    $sourcePath = Join-Path $repoRoot 'marketplace\marketplace.json'
    $destinationPath = Join-Path $userRoot '.agents\plugins\marketplace.json'
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "Missing marketplace file: $sourcePath"
    }

    $incoming = Get-Content -Raw -LiteralPath $sourcePath | ConvertFrom-Json
    $incomingPlugin = $incoming.plugins | Where-Object { $_.name -eq 'medical-manuscript-workflow' } | Select-Object -First 1
    if ($null -eq $incomingPlugin) {
        throw 'The package marketplace does not contain medical-manuscript-workflow.'
    }

    if ($DryRun) {
        Write-Step "Would merge medical-manuscript-workflow into $destinationPath"
        return
    }

    Ensure-Directory -Path (Split-Path -Parent $destinationPath)
    if (Test-Path -LiteralPath $destinationPath) {
        Backup-ExistingPath -Path $destinationPath -RelativeBackupPath '.agents\plugins\marketplace.json'
        $current = Get-Content -Raw -LiteralPath $destinationPath | ConvertFrom-Json
        if ($null -eq $current.plugins) {
            $current | Add-Member -MemberType NoteProperty -Name plugins -Value @()
        }
        $remaining = @($current.plugins | Where-Object { $_.name -ne 'medical-manuscript-workflow' })
        $current.plugins = @($remaining) + @($incomingPlugin)
        $current | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $destinationPath -Encoding utf8
    }
    else {
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    }
}

$verifyScript = Join-Path $repoRoot 'verify.ps1'
if (-not (Test-Path -LiteralPath $verifyScript)) {
    throw "Missing verification script: $verifyScript"
}

Write-Step 'Verifying the migration package.'
& $verifyScript
if ($LASTEXITCODE -ne 0) {
    throw 'Package verification failed. Installation stopped.'
}

Merge-Directory -Source (Join-Path $repoRoot 'skills\codex') -Destination (Join-Path $userRoot '.codex\skills') -BackupPrefix '.codex\skills'
Merge-Directory -Source (Join-Path $repoRoot 'skills\agents') -Destination (Join-Path $userRoot '.agents\skills') -BackupPrefix '.agents\skills'

$pluginSource = Join-Path $repoRoot 'plugins\medical-manuscript-workflow'
$pluginDestination = Join-Path $userRoot 'plugins\medical-manuscript-workflow'
if (Test-Path -LiteralPath $pluginDestination) {
    Backup-ExistingPath -Path $pluginDestination -RelativeBackupPath 'plugins\medical-manuscript-workflow'
}
Ensure-Directory -Path $pluginDestination
if ($DryRun) {
    Write-Step "Would copy $pluginSource into $pluginDestination"
}
else {
    Get-ChildItem -LiteralPath $pluginSource -Force | Copy-Item -Destination $pluginDestination -Recurse -Force
}

Install-PersonalMarketplace

if ($DryRun) {
    Write-Step 'Dry run completed. No files were changed.'
}
else {
    Write-Step 'Skills and personal plugin source were restored.'
    if ($backupCreated) {
        Write-Step "Existing content was backed up to $backupRoot"
    }
    Write-Step 'Restart ChatGPT Work, install or enable medical-manuscript-workflow from Personal, and open a new thread.'
}
