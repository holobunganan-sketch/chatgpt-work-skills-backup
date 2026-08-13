# Evidence Policy

Evidence proves that an action occurred and that its result satisfies the compiled contract.

## Evidence chain

For every important step preserve:

`ACTION -> EXPECTED -> OBSERVED -> EVIDENCE -> VERDICT`

The package defines Action, Expected, Evidence, and verdict rules. The executor fills Observed and the final Verdict.

## Evidence quality

Evidence must be:

- directly tied to the step;
- sufficient to distinguish PASS from failure;
- compact enough for later review;
- reproducible where practical;
- free of unnecessary secrets or personal data.

Do not substitute "done", "looks good", or "completed successfully" for evidence.

## Domain examples

### Code / Git

Use exact command, exit code, relevant output, diff summary, test count, commit SHA, tag, or CI status.

### Files / artifacts

Use exact path, existence, size when useful, checksum when identity matters, rendered/parsed validation, and before/after comparison for required changes.

### Research

Use source title/identifier, source location, extracted fact, date/version when freshness matters, and claim mapping.

### Data

Use source identifier, row/column counts, filters, missing-value counts, reconciliation totals, formula or query results, and output path.

### Writing

Use a requirement-to-section check, prohibited-claim scan, length/format check, and source-fact trace for externally grounded claims.

## Final acceptance

Acceptance should rely on accumulated evidence rather than re-performing the whole task. If acceptance still requires subjective judgment, classify that gate as `HIGH_MODEL_REQUIRED` and state what material the capable model must review.
