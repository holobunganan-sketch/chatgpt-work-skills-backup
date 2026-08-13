# Task Taxonomy

Classify the task so the package uses appropriate evidence and escalation rules. A task may use more than one class.

## Engineering / repository work

Capture repository, branch, target files, build/test commands, dependency state, and change boundaries. Evidence can include diffs, exit codes, test output, commit SHA, status checks, and artifact hashes. Escalate architecture changes, unexpected generated files, destructive Git operations, security changes, or broad refactors outside scope.

## Research / evidence synthesis

Capture the research question, source scope, freshness requirements, inclusion/exclusion rules, citation standard, and claim-evidence mapping. Evidence should identify source, location, extracted fact, and the claim it supports. Escalate conflicting evidence, weak source quality that changes conclusions, missing authoritative sources, or requests for unsupported inference.

## Writing / content production

Capture audience, purpose, required facts, tone, length, structure, prohibited claims, and source material. Evidence can map requirements to sections and run constraint checks. Escalate missing facts that materially change the message, sensitive claims, or editorial choices with business/legal consequences.

## Data / spreadsheet / analytics work

Capture source files, schema, unit definitions, filters, date ranges, missing-data rules, formulas, and expected outputs. Evidence can include row counts, summary statistics, reconciliation totals, formula checks, and file hashes. Escalate ambiguous metric definitions, data-quality failures, inconsistent schemas, or unexplained reconciliation gaps.

## Document / presentation / artifact work

Capture source artifacts, output format, page/slide/sheet constraints, required styles, and fidelity expectations. Evidence can include page counts, rendered previews, structure checks, and content comparisons. Escalate corrupted sources, unsupported formats, fidelity failures, or design decisions that were not specified.

## Operations / workflow work

Capture systems, accounts, permissions, irreversible actions, external recipients, schedules, and confirmation points. Evidence can include IDs, timestamps, state transitions, and system confirmations. Escalate any external side effect outside the exact authorized target.

## GitHub / release work

Capture repository, default branch, branch strategy, version, tag convention, release artifacts, CI requirements, and permissions. Evidence can include commit SHA, tag ref, workflow status, release URL, and asset names. Escalate force pushes, history rewrites, secret handling, permission changes, failed required checks, or tag/version conflicts.
