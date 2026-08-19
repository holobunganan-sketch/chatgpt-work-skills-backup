# optimizing-deepseek-v4-flash-prompts

Executable Agent Skill for compiling task instructions optimized for DeepSeek V4 Flash.

## Install

Windows PowerShell:

```powershell
.\install.ps1
```

Linux/macOS:

```bash
./install.sh
```

Default cross-runtime location: `~/.agents/skills/optimizing-deepseek-v4-flash-prompts`.

## Quick use

```bash
python scripts/deepseek_prompt_tool.py scaffold --profile medical --out task.json
python scripts/deepseek_prompt_tool.py validate-spec task.json
python scripts/deepseek_prompt_tool.py route task.json
python scripts/deepseek_prompt_tool.py compile task.json --profile medical --out prompt.md
python scripts/deepseek_prompt_tool.py lint prompt.md
python scripts/deepseek_prompt_tool.py cache-plan task.json --profile medical
python scripts/deepseek_prompt_tool.py adapter task.json
python scripts/deepseek_prompt_tool.py doctor
```

The compiler creates a stable prefix, source-authority boundary, current task section, execution/tool policy, constraints, output contract, quality gate, and stop condition.
