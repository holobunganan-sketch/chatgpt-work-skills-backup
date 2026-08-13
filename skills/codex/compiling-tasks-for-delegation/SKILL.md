---
name: compiling-tasks-for-delegation
description: Use when a task will be delegated to a less capable model, including explicit GPT-5.3-Codex-Spark handoffs, and execution reliability depends on bounded decisions, verifiable steps, environment-specific instructions, or safe escalation.
---

# Compiling Tasks for Delegation

## Core principle

Do the reasoning before delegation. Produce an execution package in which the executor can determine every allowed next action from explicit instructions plus observable results.

## Mandatory workflow

1. Preserve the user's goal, deliverables, constraints, prohibitions, and prior decisions. Do not silently widen scope.
2. Decide whether live context can change the plan. If yes, inspect the relevant files, repository state, tools, environment, permissions, connected sources, or current artifacts before compiling. Read `references/compiler-protocol.md`.
3. Classify the task and choose domain-specific evidence. Read `references/task-taxonomy.md` when the task is more than trivial.
4. Classify every executable unit as `SAFE_TO_DELEGATE`, `CONDITIONAL`, or `HIGH_MODEL_REQUIRED`. Apply `references/delegation-policy.md` strictly.
5. Detect executor specialization before writing environment-specific steps. If the user explicitly targets `GPT-5.3-Codex-Spark` or an unambiguous `Codex Spark` shorthand, activate `SPARK_EXECUTION_MODE` and read `references/gpt-5.3-codex-spark-profile.md`. Generic references to Codex or a lower-tier model do not activate this mode.
6. Build the platform-independent task contract first. Then adapt it to the current execution environment using `references/environment-adaptation.md`.
7. Decompose work into atomic steps. Every verifiable step must contain Purpose, Input, Action, Expected Result, Evidence, Verdict, and Exception Handling. Follow `references/execution-step-spec.md`.
8. Define explicit failure branches and stop codes from `references/stop-codes.md`. An uncovered material branch must stop and escalate; the executor must not improvise.
9. Define acceptance criteria before finalizing the package. Evidence must prove completion according to `references/evidence-policy.md`.
10. Choose output mode:
   - Explicit GPT-5.3-Codex-Spark target: always use the Spark chunked package defined in `references/gpt-5.3-codex-spark-profile.md` and `templates/spark/`.
   - Other simple, linear tasks: instantiate `templates/EXECUTION_PLAN.md`.
   - Other complex, multi-phase, multi-artifact, or stateful tasks: instantiate `templates/TASK.md`, `CONTEXT.md`, `STEPS.md`, `ACCEPTANCE.md`, and `EXECUTION_REPORT.md`; add `phases/` only when it reduces executor context load.
11. Run the compiler audit in `references/compiler-audit.md`. Repair every failure before handoff.
12. When files can be created, run `python scripts/validate_execution_pack.py <package-path>`. A nonzero exit status blocks handoff.

## Executor boundary

The executor may perform only actions explicitly authorized by the package. It may make local syntactic choices only when the package states the allowed range and those choices cannot materially change the outcome. It must stop on undefined branches, conflicting evidence, changed scope, destructive operations without an explicit gate, or any decision labeled `HIGH_MODEL_REQUIRED`.

## Output rule

Return the compiled package and a short handoff stating the output mode, delegation summary, validator result, and any high-model gates that remain. Do not execute the underlying user task unless the user explicitly requested execution in the same turn.
