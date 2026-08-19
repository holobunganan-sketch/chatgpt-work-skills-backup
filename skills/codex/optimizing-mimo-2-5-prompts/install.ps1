param(
  [string]$DestinationRoot = "$HOME\.agents\skills",
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillName = Split-Path -Leaf $Source
$Destination = Join-Path $DestinationRoot $SkillName

New-Item -ItemType Directory -Force -Path $DestinationRoot | Out-Null
if (Test-Path $Destination) {
  if (-not $Force) {
    throw "Skill already exists at $Destination. Re-run with -Force to replace it."
  }
  Remove-Item -Recurse -Force $Destination
}
Copy-Item -Recurse -Force $Source $Destination
Write-Host "Installed $SkillName to $Destination"
