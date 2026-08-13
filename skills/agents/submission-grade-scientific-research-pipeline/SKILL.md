---
name: submission-grade-scientific-research-pipeline
description: Build submission-grade scientific research deliverables from a research idea, study design sketch, protocol outline, or real dataset. Accept Chinese or English user instructions and produce English manuscript outputs by default, switching to Chinese only when explicitly requested. Use when the user wants a traceable scientific manuscript package with research framing, data-intake planning, deeper analysis code, tables, figures, IMRaD drafting, journal-style adaptation, DOCX outputs, submission materials, or reviewer-response templates. Triggers include scientific paper writing, cross-domain real-data analysis, computational or experimental manuscript drafting, journal submission packages, cover letters, reference formatting, and end-to-end bilingual research workflows.
---

# Submission-Grade Scientific Research Pipeline

## Mission

Turn a scientific research topic, hypothesis, protocol idea, or dataset into a coherent manuscript package whose question, design, variables, methods, analysis, results, visuals, and claims remain internally consistent.

## Core References

Read these shared references first:
- [execution-contract.md](../../../.codex/skills/.shared/submission-grade-research-core/references/execution-contract.md)
- [workflow-core.md](../../../.codex/skills/.shared/submission-grade-research-core/references/workflow-core.md)
- [language-and-integrity.md](../../../.codex/skills/.shared/submission-grade-research-core/references/language-and-integrity.md)
- [submission-assets.md](../../../.codex/skills/.shared/submission-grade-research-core/references/submission-assets.md)
- [manuscript-gate.md](../../../.codex/skills/.shared/submission-grade-research-core/references/manuscript-gate.md)

Then apply the scientific specialization:
- [scientific-specialization.md](./references/scientific-specialization.md)
- [file-contract.md](./references/file-contract.md)
- [modes-and-manuscript-types.md](./references/modes-and-manuscript-types.md)

## Operating Rules

- Default to `RIGOR_LEVEL=submission` and `MANUSCRIPT_TYPE=original_article` unless the user specifies otherwise.
- Explicitly invoke [$docx](../docx/SKILL.md) when `.docx` outputs are required.
- Use [scripts/init_pipeline_project.py](./scripts/init_pipeline_project.py) to scaffold a new project when helpful.
- Use [scripts/qc_manifest_check.py](./scripts/qc_manifest_check.py) before final delivery when a file-level completeness check is useful.
- Use [scripts/manuscript_qc.py](./scripts/manuscript_qc.py) on `docs/manuscript.docx` before final delivery and revise until it passes or only explicit residual limitations remain.
- Treat the shared execution contract as binding. Do not finalize a short, shallow, or under-analyzed draft.

## Scientific Defaults

- Default journal family: generic high-quality scientific journal with restrained, precise tone.
- Default prose language: English. Switch to Chinese only when the user explicitly requests Chinese output.
- Keep mechanism, causality, and validation claims matched to the evidence type.
