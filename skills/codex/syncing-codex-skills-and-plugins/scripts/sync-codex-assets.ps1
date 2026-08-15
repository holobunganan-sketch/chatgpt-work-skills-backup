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

throw 'Engine implementation pending.'
