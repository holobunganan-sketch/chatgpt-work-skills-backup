# Verification and Escalation

## Verification layers

### Structural validation

Check required fields, schema, scope, files covered, and declared assumptions. Use deterministic scripts where possible.

### Deterministic validation

Use tests, parsers, counts, checksums, source-location checks, formula checks, file existence, format validation, and reproducible commands.

### Independent semantic review

Use a separate agent or the main agent to inspect original inputs and verify material findings. The reviewer must be able to disagree with the producer.

### Main-agent final gate

Check:

- completeness against the user's request;
- factual or functional correctness;
- evidence traceability;
- consistency across all sections and files;
- compliance with user constraints;
- unresolved risks and limitations;
- usability of the finished artifact.

## Risk-specific requirements

| Risk | Minimum verification |
|---|---|
| L0 | Deterministic check |
| L1 | Deterministic check plus main-agent sampling or source recheck |
| L2 | Independent review, dual execution, counteranalysis, or direct source recheck by a strong reviewer |
| L3 | Main-agent execution plus final gate; use subagents only for evidence and adversarial review |

## Escalation ladder

1. Identify the exact failed criterion and preserve verified evidence.
2. Retry the same model once with concrete defect feedback when the task still fits its ceiling.
3. Spawn a stronger qualified model with a fresh packet and the failed criterion highlighted.
4. For unresolved conflicts, run an independent second analysis or adversarial review.
5. Transfer the task to the main agent.

Stop retrying when the failure reveals a capability mismatch, missing authoritative input, unsafe permission requirement, or invalid task decomposition.

## Failure rules

- No automatic downgrade after a failed validation.
- No acceptance-criterion removal.
- No source-traceability removal.
- No repeated retries without new evidence or a changed execution condition.
- No majority vote when all candidates share the same unsupported assumption.
- No final delivery while a material conflict remains unresolved.

## Outcome recording

Record an outcome only after validation. A pass means the output met its acceptance criteria without undisclosed defects. Repair count includes main-agent corrections and subagent reruns. History can demote future assignments after repeated failures.
