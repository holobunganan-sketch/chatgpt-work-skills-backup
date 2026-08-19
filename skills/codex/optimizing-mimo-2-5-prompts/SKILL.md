---
name: optimizing-mimo-2-5-prompts
description: Use when creating, adapting, reviewing, or debugging prompts, agent instructions, long-context workflows, repeated cached prompts, Chinese writing instructions, or evidence-sensitive tasks specifically for Xiaomi MiMo-V2.5.
---

# Optimizing MiMo-V2.5 Prompts

## Overview

Use MiMo-V2.5 as a goal-driven agent with explicit task boundaries, source boundaries, output contracts, and observable quality gates. Prefer the included compiler and linter over hand-writing a generic mega-prompt.

## Required workflow

1. Classify the task as `general`, `writing`, `medical`, `long-context`, or `agent`.
2. Build a task JSON from `config/task-schema.json`; use `scripts/mimo_prompt_tool.py scaffold` when useful.
3. Validate it:
   `python scripts/mimo_prompt_tool.py validate-spec --input task.json`
4. Compile it:
   `python scripts/mimo_prompt_tool.py compile --input task.json --output prompt.md`
5. Lint the result:
   `python scripts/mimo_prompt_tool.py lint --prompt prompt.md`
6. For repeated calls, agents, or persistent projects, also run:
   `python scripts/mimo_prompt_tool.py cache-plan --input task.json`

Do not replace steps 2–5 with a long prose prompt when the scripts are available.

## Profile selection

- `writing`: Chinese/English drafting, rewriting, PPT copy, summaries, meeting outputs.
- `medical`: literature extraction, evidence synthesis, clinical/medical content where facts and inference must remain separated.
- `long-context`: many files, very long documents, multi-source synthesis, source-ID tracking.
- `agent`: tool use, multi-step execution, stateful work, completion checks.
- `general`: everything else.

Combine needs by choosing the highest-risk profile, then add task-specific constraints. For medical work over many documents, use `medical` and add stable source IDs; consult `references/design-rules.md` for the combined pattern.

## Core rules

- Put task type, goal, deliverable, and audience near the start.
- Separate instructions from source material.
- Specify stages; leave stage-internal planning to the model.
- Use hard, observable constraints instead of vague reminders.
- Give every important output an explicit quality gate.
- In long contexts, assign stable source IDs and define source priority.
- For repeated calls, keep stable rules in the prefix and current task/materials in the suffix.
- Avoid exaggerated role-play as a substitute for task definition.

## References

Read `references/model-profile.md` for verified MiMo-V2.5 properties and `references/design-rules.md` for detailed design decisions. Run `python scripts/self_test.py` after modifying this skill.
