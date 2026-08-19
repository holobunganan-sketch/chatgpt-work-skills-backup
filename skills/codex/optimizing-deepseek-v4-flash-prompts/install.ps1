$ErrorActionPreference = "Stop"
$SkillName = "optimizing-deepseek-v4-flash-prompts"
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetRoot = Join-Path $HOME ".agents\skills"
$Target = Join-Path $TargetRoot $SkillName

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
if (Test-Path $Target) { Remove-Item -Recurse -Force $Target }
Copy-Item -Recurse -Force $Source $Target
Write-Host "Installed: $Target"
python (Join-Path $Target "scripts\deepseek_prompt_tool.py") doctor
