# optimizing-mimo-2-5-prompts

A portable Agent Skill for producing and checking task instructions optimized for Xiaomi MiMo-V2.5.

This package deliberately contains executable tooling, configuration, task schemas, model-specific profiles, tests, examples, and installation helpers. `SKILL.md` is the router and operating contract; it is not the whole implementation.

## Contents

- `SKILL.md` — skill discovery and required workflow
- `scripts/mimo_prompt_tool.py` — compiler, linter, cache planner, task validator, scaffolder
- `config/` — required fields, section rules, cache layout, JSON schema
- `templates/profiles/` — general, writing, medical, long-context, agent behavior modules
- `references/` — verified model profile and detailed design rules
- `tests/` — regression tests and fixtures
- `examples/` — ready-to-edit task specs and compiled prompts
- `install.ps1` / `install.sh` — copy into the cross-runtime `~/.agents/skills/` location

## Requirements

Python 3.10+; no third-party Python packages.

## Quick usage

```bash
python scripts/mimo_prompt_tool.py scaffold --profile medical --output task.json
python scripts/mimo_prompt_tool.py validate-spec --input task.json
python scripts/mimo_prompt_tool.py compile --input task.json --output prompt.md
python scripts/mimo_prompt_tool.py lint --prompt prompt.md
python scripts/mimo_prompt_tool.py cache-plan --input task.json
python scripts/self_test.py
```

## Profiles

- `general`
- `writing`
- `medical`
- `long-context`
- `agent`

Profiles remain small and composable. Task-specific requirements belong in the JSON spec rather than in a permanent global prompt.
