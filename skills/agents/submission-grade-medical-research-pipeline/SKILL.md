---
name: submission-grade-medical-research-pipeline
description: Build submission-grade medical research deliverables end-to-end from a one-sentence study idea, protocol sketch, or real dataset. Accept Chinese or English user instructions and produce English manuscript outputs by default, switching to Chinese only when explicitly requested. When the user does not provide data, analyze the topic, design an appropriate synthetic dataset, generate it, and continue through statistical analysis, tables, figures, IMRaD drafting, journal-style adaptation, DOCX outputs, and submission materials. Use when the user wants a traceable biomedical manuscript package, simulated-data manuscript workflow, real-data medical analysis, cover letter, AMA references, reviewer-response template, or one-idea-to-manuscript production flow.
---

# Submission-Grade Medical Research Pipeline

## Mission

Turn a one-sentence medical research idea, protocol sketch, or dataset into a coherent manuscript package whose question, design, variables, synthetic or real data, analysis, results, tables, figures, and claims remain internally consistent.

## Core References

Read these shared references first:
- [execution-contract.md](../../../.codex/skills/.shared/submission-grade-research-core/references/execution-contract.md)
- [workflow-core.md](../../../.codex/skills/.shared/submission-grade-research-core/references/workflow-core.md)
- [language-and-integrity.md](../../../.codex/skills/.shared/submission-grade-research-core/references/language-and-integrity.md)
- [submission-assets.md](../../../.codex/skills/.shared/submission-grade-research-core/references/submission-assets.md)
- [manuscript-gate.md](../../../.codex/skills/.shared/submission-grade-research-core/references/manuscript-gate.md)

Then apply the medical specialization:
- [medical-specialization.md](./references/medical-specialization.md)
- [file-contract.md](./references/file-contract.md)
- [modes-and-manuscript-types.md](./references/modes-and-manuscript-types.md)

## Operating Rules

- Default to `RIGOR_LEVEL=submission` and `MANUSCRIPT_TYPE=original_article` unless the user specifies otherwise.
- Treat "one-line idea to full manuscript" as the default workflow, not a special case.
- If the user does not provide a dataset, do not stop to ask for one. Translate the idea into a defensible study design, define the variable schema, generate a fit-for-purpose synthetic dataset, and continue the workflow to completed manuscript outputs.
- Own the end-to-end flow from question framing through data construction, analysis, result presentation, and manuscript drafting.
- Make the synthetic dataset realistic enough to support the planned design and analyses. The skill is responsible for producing a usable dataset and coherent manuscript package; downstream judgment about whether the simulated data are acceptable for the user's purpose belongs to the user.
- Explicitly invoke [$docx](../docx/SKILL.md) when `.docx` outputs are required.
- Use [scripts/init_pipeline_project.py](./scripts/init_pipeline_project.py) to scaffold a new project when helpful.
- Use [scripts/qc_manifest_check.py](./scripts/qc_manifest_check.py) before final delivery when a file-level completeness check is useful.
- Use [scripts/manuscript_qc.py](./scripts/manuscript_qc.py) on `docs/manuscript.docx` before final delivery and revise until it passes or only explicit residual limitations remain.
- Treat the shared execution contract as binding. Do not finalize a short, shallow, or under-analyzed draft.
- Use AMA 11th superscript-style numbered in-text citations by default, and place them exactly where the supporting claim appears in the body text.
- Insert all major tables and figures into the manuscript body, cite them explicitly as `Table X` or `Figure X`, and discuss them in adjacent prose rather than leaving them detached as appendices.
- Insert tables in academic three-line-table style within the manuscript body unless the target journal requires another format.
- Use academic plotting only: white background, black elements, grayscale-safe output, and no color figures unless the user explicitly authorizes color.
- Analyze datasets in a layered sequence of baseline analysis, between-group analysis, and modeling analysis, and use the resulting tables and figures to drive both the Results and Discussion sections.
- Keep manuscript text in pure black without colored fonts or decorative emphasis.

## Medical Defaults

- Default journal family: generic high-quality biomedical journal with restrained JAMA-like tone.
- Default prose language: English. Switch to Chinese only when the user explicitly requests Chinese output.
- Keep clinical claims restrained and matched to the underlying design.
