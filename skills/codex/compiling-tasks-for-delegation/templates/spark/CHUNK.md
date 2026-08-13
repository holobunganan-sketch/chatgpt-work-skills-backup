# CHUNK-NNN — {bounded outcome}

## Target Executor
GPT-5.3-Codex-Spark

## Chunk Goal
{one primary outcome}

## Why This Chunk Exists
{why this is an independently executable slice}

## Required Context
- {only context needed for this chunk}

## Context Budget
- Compiler target: <= 12,000 input tokens including explicitly required context.
- Chunk instruction file: <= 24,000 characters.

## Preconditions
- {observable precondition}

## Allowed Scope
- {exact allowed mutation/read scope}

## Forbidden Actions
- Do not read or execute later chunks.
- Do not expand scope or redesign architecture.
- {task-specific prohibition}

## Files / Resources
- `{primary file or resource 1}`
- `{primary file or resource 2}`
- `{primary file or resource 3}`

## Exact Steps

### STEP 01 — {atomic action}
Delegation: SAFE_TO_DELEGATE

#### Purpose
{why this action exists}

#### Input
{exact input}

#### Action
{exact command/edit/tool operation}

#### Expected Result
{observable expected state}

#### Evidence
{what to record}

#### Verdict
PASS when {condition}; otherwise follow Exception Handling.

#### Exception Handling
{known branch -> action or stop code}

## Mandatory Verification
{exact test, lint, typecheck, build, diff, structural check, calculation, or artifact check; execution is mandatory}

## Expected Result
{chunk-level successful state}

## Evidence to Record
- {diff/output/path/status/result}

## Failure Branches
- {condition -> stop code / escalation}

## Completion Report
Report chunk ID, `PASS|BLOCKED|FAILED|HIGH_MODEL_REQUIRED`, changes, verification results, evidence, and unresolved items.

## Next-Chunk Gate
USER_APPROVAL_REQUIRED
AUTO_CONTINUE_FORBIDDEN

On `PASS`, stop after the completion report. If another chunk remains, ask the user whether to start the named next chunk. Do not preload or execute that chunk before explicit approval.
