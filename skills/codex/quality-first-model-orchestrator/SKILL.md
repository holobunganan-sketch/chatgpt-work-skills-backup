---
name: quality-first-model-orchestrator
description: Use when a task may benefit from Codex subagents, parallel work, mixed model families, or dynamic model routing, especially when the current conversation model must remain the main agent and final quality must not be reduced for speed, cost, quota use, or model diversity.
---

# Quality-First Model Orchestrator

Keep the current conversation model as the main agent. Delegate only work that another discovered model can complete at the required quality level and that can be independently verified.

## Non-negotiable invariant

Final quality is a hard constraint. Speed, quota use, cost, concurrency, and model diversity are soft preferences. When no subagent passes the quality gate, perform the work in the main agent.

The main agent always owns:

- interpretation of the user's goal;
- the quality contract and task graph;
- critical scientific, legal, financial, safety, architectural, and release decisions;
- conflict resolution;
- integration and final editing;
- the final quality gate and delivery.

Never replace or downgrade the current conversation model. Never force delegation merely to consume another model's quota.

## Required workflow

### 1. Establish the quality contract

Before spawning any subagent, define:

- objective and required deliverables;
- factual, evidentiary, completeness, consistency, and formatting requirements;
- prohibited outcomes and scope boundaries;
- acceptance tests;
- consequences of error.

Read [quality-policy.md](references/quality-policy.md) for the contract and hard priorities.

### 2. Decide whether delegation helps

Use the main agent directly when the task is small, tightly coupled, highly ambiguous, difficult to verify, or dominated by L3 decisions.

Delegate only bounded units with clear inputs, outputs, acceptance criteria, and verification. Read [task-risk-and-roles.md](references/task-risk-and-roles.md) before classifying tasks.

### 3. Discover available models

Resolve `SKILL_ROOT` as the directory containing this `SKILL.md`. Use the available Python 3 command and run:

```bash
python3 "$SKILL_ROOT/scripts/discover_models.py" --output <temp>/model-catalog.json
python3 "$SKILL_ROOT/scripts/build_model_registry.py" \
  --catalog <temp>/model-catalog.json \
  --history "$HOME/.codex/model-orchestrator/model-history.json" \
  --output <temp>/model-registry.json
```

Omit `--history` when the file does not exist.

The discovery helper queries Codex App Server `model/list`. It can also consume a saved catalog through `--catalog-file` or `CODEX_MODEL_CATALOG_JSON`.

If discovery fails, do not invent model availability. Use only models explicitly confirmed by the current client. When no reliable catalog is available, keep the task in the main agent.

Read [model-routing-policy.md](references/model-routing-policy.md) before assigning models.

### 4. Build a task manifest and obtain a routing proposal

Create a JSON manifest containing the domain and independent task units. Each task must include risk, category, delegation permission, critical-output status, required modalities, and required traits.

Run:

```bash
python3 "$SKILL_ROOT/scripts/route_tasks.py" \
  --manifest <temp>/task-manifest.json \
  --registry <temp>/model-registry.json \
  --output <temp>/routing-proposal.json
```

Treat this output as a conservative proposal. The main agent may move work upward to a stronger model or retain it. The main agent may not move work below the registry's quality ceiling.

### 5. Compile model-adapted task packets

For every delegated unit, write a fresh task packet. Do not send the same generic prompt to every model.

Lower-capability or speed-optimized models require:

- one narrow objective;
- explicit source and file boundaries;
- ordered steps;
- fixed output fields;
- source-location requirements;
- explicit prohibitions on inference and scope expansion;
- a concrete stop condition.

Stronger models may receive broader context and limited judgment, while still operating under a role contract and acceptance criteria.

Read [task-packets.md](references/task-packets.md) for schemas and prompt adaptation.

### 6. Validate the full plan before spawning

Create a complete orchestration plan containing the main-agent lock, quality contract, tasks, assignments, verification methods, write sets, dependency graph, escalation rules, and final gate.

Run:

```bash
python3 "$SKILL_ROOT/scripts/validate_orchestration_plan.py" \
  --plan <temp>/orchestration-plan.json \
  --registry <temp>/model-registry.json
```

Do not spawn subagents when validation fails. Repair the plan and validate again.

### 7. Spawn and supervise

Spawn subagents with explicit model and reasoning-effort values from the validated plan. Use parallel execution only for independent tasks.

Defaults:

- read-only for exploration, extraction, review, and evidence work;
- one writer per file or artifact;
- no nested delegation unless the plan explicitly permits it;
- wait for all required results before integration;
- return structured findings and concise evidence, excluding raw process noise.

Read [context-and-security.md](references/context-and-security.md) whenever agents read files, web content, messages, or other potentially untrusted material.

### 8. Verify every result

Verification strength follows risk:

- L0: deterministic check;
- L1: main-agent sampling or source recheck;
- L2: independent review, countercheck, or dual execution;
- L3: main-agent execution and final gate.

A subagent's confidence statement is not verification. Read [verification-escalation.md](references/verification-escalation.md).

### 9. Escalate quality failures

On failure:

1. Give the same model one retry with specific defect evidence when the task remains within its capability ceiling.
2. Reassign to a stronger qualified model.
3. Use an independent second analysis when conflict remains.
4. Transfer the work to the main agent.

Never downgrade after a quality failure. Never remove required validation to preserve speed or quota.

### 10. Integrate and deliver from the main agent

The main agent must inspect the underlying evidence for material claims, resolve conflicts, complete the final artifact, and run the final quality gate. Do not concatenate subagent outputs into the final deliverable without synthesis and review.

Optionally record privacy-minimized performance metrics after validation:

```bash
python3 "$SKILL_ROOT/scripts/record_outcome.py" \
  --model-id <model> --category <category> --risk <L0-L2> \
  --passed <true|false> --repair-count <n> --validator-failures <n>
```

The history contains metrics only. It may demote future routing. It never auto-promotes a model above the built-in conservative ceiling.

## Failure-safe behavior

Use the main agent when:

- model discovery is unavailable or ambiguous;
- no model satisfies every hard requirement;
- the task cannot be independently verified;
- required context cannot be safely isolated;
- subagent results remain inconsistent after escalation;
- the orchestration overhead threatens completeness or coherence.

Report material limitations honestly. Complete all reliable work that can be completed in the current task.
