# Changelog

## 1.1.0 — 2026-08-09

- Added explicit `GPT-5.3-Codex-Spark` target detection and `SPARK_EXECUTION_MODE`.
- Added a Spark-specific compiler profile for compact real-time execution loops.
- Added chunked Spark package templates and user-approval continuation gates.
- Added mandatory per-chunk verification requirements.
- Added Spark chunk budgets: maximum 6 atomic steps, default maximum 3 primary files/resources, and a <=12k-token compiler target for active context.
- Extended the validator with Spark package, chunk-size, model-target, verification, and continuation-gate checks.
- Added Spark-specific tests, example package, documentation, and CI/release validation.

## 1.0.0 — 2026-08-08

- Initial public release.
- Added deterministic task-compilation protocol.
- Added three-state delegation policy.
- Added single-file and multi-file execution-package templates.
- Added environment adaptation, evidence policy, stop codes, and compiler audit.
- Added structural execution-package validator with tests.
- Added example packages and forward-test evaluation cases.
- Added Codex `agents/openai.yaml` metadata.
- Added CI and version-triggered GitHub Release automation.
