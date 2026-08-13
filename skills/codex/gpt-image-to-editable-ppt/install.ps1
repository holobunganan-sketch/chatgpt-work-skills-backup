$ErrorActionPreference = "Stop"
$SkillName = "gpt-image-to-editable-ppt"
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetRoot = Join-Path $HOME ".agents\skills"
$Target = Join-Path $TargetRoot $SkillName
New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
if (Test-Path $Target) { Remove-Item -Recurse -Force $Target }
Copy-Item -Recurse -Force $Source $Target
Write-Host "Installed to $Target"
Write-Host "Restart Codex if the skill does not appear. Invoke with `$gpt-image-to-editable-ppt."
