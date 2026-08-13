# GPT-5.3-Codex-Spark Execution Profile

Use this profile only when the user explicitly names `GPT-5.3-Codex-Spark`, `GPT 5.3 Codex Spark`, `5.3 Codex Spark`, or an unambiguous shorthand such as `Codex Spark` that clearly refers to this model. Generic phrases such as `Codex`, `small model`, `lower-tier model`, or `fast model` do not activate this profile.

## Why this profile exists

OpenAI describes Codex-Spark as a model optimized for real-time work in Codex, targeted edits, rapid iteration, and a lightweight default working style. OpenAI also states that it does not automatically run tests unless asked. At launch OpenAI documented a 128k context window and text-only operation.

Compiler implication: keep the execution loop compact, explicit, and easy to verify. Do not use the documented context window as a packing target. Reserve substantial headroom for repository state, tool output, diffs, and verification results.

Official source:
- https://openai.com/index/introducing-gpt-5-3-codex-spark/

## Spark compilation mode

When this profile is active, set the mode to `SPARK_EXECUTION_MODE` and always generate a chunked package, even when the full task could fit in one generic execution plan.

Required structure:

```text
spark-execution-package/
├── TASK.md
├── CONTEXT.md
├── SPARK_MASTER_INDEX.md
├── ACCEPTANCE.md
├── EXECUTION_REPORT.md
└── chunks/
    ├── CHUNK-001.md
    ├── CHUNK-002.md
    └── ...
```

The executor reads `TASK.md`, `CONTEXT.md`, `SPARK_MASTER_INDEX.md`, and only the active chunk. It must not preload later chunk files.

## Chunk sizing policy

Each chunk must satisfy all of these rules:

- one primary outcome;
- no more than 6 atomic `STEP` blocks;
- default maximum of 3 primary files/resources;
- compiler target of no more than 12,000 input tokens for the active chunk plus explicitly required context;
- chunk instruction file no longer than 24,000 characters;
- one subsystem or tightly coupled local change where possible;
- no hidden dependency on unread later chunks;
- independent verification at the end of the chunk.

The 12,000-token target is a conservative compiler budget, not a claim about the model's maximum context. If the required context cannot fit comfortably inside this budget, split the work further or move the affected unit to `HIGH_MODEL_REQUIRED`.

Count only the files the executor must actively inspect or modify for the chunk as primary files. Repository-wide test commands, generated outputs, and a single manifest used only for verification may be listed separately as supporting resources when they do not require material reasoning.

## Instruction style for Spark

Write commands and edits in direct imperative form. Each action should name:

- the exact file, tool, command, symbol, or UI target;
- the exact scope of allowed change;
- the expected observable result;
- the evidence to capture;
- the branch to take when the expected result is absent.

Avoid broad instructions such as `fix the issue`, `clean this up`, `make it robust`, `review related files`, or `test as needed`. Replace them with bounded edits and explicit verification.

Prefer minimal targeted modifications. Do not ask Spark to redesign architecture, reinterpret user intent, choose among materially different approaches, or expand scope inside a chunk.

## Mandatory verification rule

Every chunk must contain `## Mandatory Verification` with an explicit verification action. For code work, name the exact test, lint, typecheck, build, compile, diff, or targeted behavior check. For non-code work, name the exact structural, content, numerical, source, or artifact check.

A chunk cannot receive `PASS` without executing the stated verification and recording the result. If verification cannot be run because a required tool or input is unavailable, return a stop code. Do not substitute visual confidence or a summary claim for evidence.

## Chunk lifecycle

Use these states in `SPARK_MASTER_INDEX.md`:

- `READY`: compiled and waiting for execution;
- `RUNNING`: current active chunk;
- `PASS`: completed and independently verified;
- `BLOCKED`: execution stopped on a defined dependency, mismatch, or permission problem;
- `FAILED`: the requested result or mandatory verification failed;
- `HIGH_MODEL_REQUIRED`: the next action requires material judgment or recompilation.

Only one chunk may be `RUNNING` at a time.

## Completion and continuation gate

Every chunk must end with these literal control markers under `## Next-Chunk Gate`:

```text
USER_APPROVAL_REQUIRED
AUTO_CONTINUE_FORBIDDEN
```

After a successful non-final chunk, Spark must stop and report:

```text
CHUNK-NNN COMPLETED

Result: PASS
Changes: <concise list>
Verification: <commands/checks and results>
Evidence: <paths, diffs, outputs, or other proof>
Next planned chunk: CHUNK-NNN+1 — <title>

当前片段已经完成并通过核查。是否开始下一片段 CHUNK-NNN+1？
```

Match the user's language for the final question. Do not read, preload, execute, or partially begin the next chunk until the user explicitly approves continuation.

For the final chunk, report completion and final acceptance status. There is no next-chunk question.

## Blocked or failed behavior

When a chunk becomes `BLOCKED`, `FAILED`, or `HIGH_MODEL_REQUIRED`, stop immediately after recording:

```text
CHUNK-NNN BLOCKED
Stop Code: <code>
Expected: <expected state>
Observed: <observed state>
Evidence: <proof>
Required escalation: <specific decision, input, permission, or recompilation>
```

Do not ask whether to continue to the next chunk. The affected work returns to the capable compiler model or the user for the missing authorization/input.

## Compiler responsibilities before handoff

Before emitting a Spark package, the capable model must:

1. resolve all material design choices that can be resolved safely;
2. inspect live repository/files/tool state when it can change the plan;
3. split cross-subsystem work into independent chunks;
4. ensure each chunk has a bounded file/resource set and explicit verification;
5. ensure later chunks depend only on recorded outputs from earlier chunks;
6. mark every remaining judgment gate `HIGH_MODEL_REQUIRED`;
7. run `python scripts/validate_execution_pack.py <spark-package-path>` when file execution is available.
