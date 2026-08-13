---
name: write-evidence-grounded-manuscript
description: Create, restructure, audit, and deliver complete evidence-grounded academic research manuscripts from a source pack, verified results, figure/table assets, and a reference library. Use for IMRaD manuscript drafting, strict Methods-Results separation, literature-comparative Discussion writing, inline figure/table integration, configurable journal formatting, submission-ready DOCX generation, real Zotero Word-field embedding, or manuscript evidence and layout quality control.
---

# Write Evidence-Grounded Manuscript

## Operating contract

Treat the source pack, verified result files, asset manifest, and reference library as the evidence boundary. Do not redesign the study, rerun analyses, invent missing facts, or add unverified results unless the user explicitly expands the task.

Resolve conflicts in this order: current user instructions, locked source-pack scope, verified result sources, figure/table source data, literature evidence map, existing prose, general domain knowledge. Record unresolved conflicts instead of guessing.

Keep four rules invariant:

1. Preserve evidence fidelity and numerical traceability.
2. Separate Methods from Results using the pre-analysis test.
3. Make Discussion compare the study with its field rather than repeat Results.
4. Make every number, citation, and figure/table traceable and auditable.

## Start with a manuscript contract

Read `assets/default-profile.json` as a default, then override it with the source pack, target-journal instructions, and user requirements. Create a short manuscript contract before drafting that locks:

- article type, target audience, research question, and intended claim boundary;
- required sections, abstract labels, heading policy, and language;
- reporting guideline and unresolved checklist items;
- citation style, reference manager, and sections allowed to cite external literature;
- document typography and delivery format;
- main and supplementary asset order;
- validated result sources and prohibited extrapolations.

Do not silently apply the default publication profile when the journal or user specifies a different one.

## Execute the workflow

1. Inventory the source pack, results, literature, figures, tables, and administrative metadata.
2. Build a result-control ledger mapping every reported number to a source.
3. Build a claim-to-literature map for Introduction and Discussion.
4. Classify each candidate statement as background, protocol/method, realized result, interpretation, or declaration.
5. Draft the structured abstract and main sections under the locked section rules.
6. Insert each empirical figure/table after its first substantive citation.
7. Generate the editable DOCX and embed reference-manager fields when requested and supported.
8. Run source, DOCX, citation, asset, and visual-rendering quality gates.
9. Deliver the manuscript, editable source, QC report, asset placement record, and unresolved-items list.

## Enforce section boundaries

Apply this test to every statement:

> Could this statement have been written before executing the study, using only the protocol or analysis plan?

- If yes, route it to Methods.
- If it became known only after screening, cleaning, fitting, tuning, estimating, comparing, or observing data, route it to Results.
- If it interprets a result through prior literature, route it to Discussion.

Move misplaced results to Results; do not merely delete them. Keep Methods limited to design, eligibility rules, outcome definitions, input processing, candidate-generation procedures, comparison criteria, locking rules, comparator construction, evaluation methods, software, and prespecified settings.

Treat realized sample sizes, event counts, exclusions, missingness findings, observed feature counts, selected hyperparameters, retained variables, coefficients, equations, data-derived thresholds, group sizes, estimates, intervals, P values, rankings, and performance as Results.

Read `references/section-boundaries.md` before drafting or restructuring Methods and Results. Run `scripts/audit_manuscript.py` before DOCX generation.

## Draft each section

### Abstract

Use the configured structured labels. Keep abstract Methods procedural and abstract Results empirical. Do not leak selected variables, realized sample sizes, final parameters, or performance into abstract Methods under the strict profile.

### Introduction

Build a short logical chain from context to established evidence, unresolved gap, and study objective. Cite only evidence mapped in the source pack. Do not preview detailed study results.

### Methods

Describe what was done, to what inputs, in what order, for what analytical purpose, and under what prespecified rules. Include citations only when the publication profile permits method citations.

### Results

Report realized data flow, characteristics, analysis implementation, final model or primary effect, comparisons, uncertainty, diagnostics, sensitivity analyses, and clinically relevant outputs in evidence order. Keep external literature and field comparison out of Results.

### Discussion

Make the first paragraph a concise synthesis of the main findings and their evidence boundary. In later paragraphs, compare the study with relevant benchmarks, same-domain studies, systematic evidence, transportability work, and implementation evidence. Explain meaningful convergence or divergence through differences in population, outcome, design, measurement, platform, validation level, and clinical context.

Make the final Discussion paragraph a single integrated paragraph containing exactly three high-priority limitations. Pair each limitation with a concrete future-study improvement that directly addresses it. State how each limitation affects bias, uncertainty, generalizability, interpretation, or implementation; avoid an unprioritized limitation list and generic calls for "more research." Use clear first/second/third transitions under the default profile so the three pairs remain auditable, unless the journal requires another style.

Do not follow the Results sequence paragraph by paragraph, conduct new analyses, invent mechanisms, rank incompatible studies by a single metric, or convert association into causation. Read `references/discussion-evidence.md` before drafting Discussion.

### Conclusion

Write one configured-length paragraph that answers the objective, states the supported contribution, preserves the principal limitation, and avoids new citations or claims.

### Declarations and references

Report only verified ethics, consent, registration, funding, conflicts, data availability, code availability, and patient-involvement information. Use explicit unresolved placeholders only in a draft authorized to contain them.

## Integrate citations and assets

Use the configured citation distribution. Under the default biomedical profile, cite external literature in Introduction and Discussion only; allow method citations only when the journal, source pack, or user overrides the default.

Place result-bearing figures and tables in Results. Place a purely methodological schematic in Methods only when it contains no realized sample, selected model, or performance information. Cite every asset before insertion. Keep numbering continuous and synchronized among prose, captions, filenames, and the asset manifest.

Place figure captions below figures and table titles above tables under the default profile. Keep each figure with its caption and each table title with its table. Read `references/publication-delivery.md` before assembling DOCX.

## Deliver DOCX and reference-manager fields

Produce an editable DOCX, not a flattened PDF-only deliverable. When Zotero is requested, embed genuine `ZOTERO_ITEM`, `ZOTERO_BIBL`, and `ZOTERO_PREFS` Word fields. Never claim Zotero embedding when citations are plain text or the local integration is unavailable.

Preserve journal-configured font, size, color, line spacing, heading depth, title-page policy, caption placement, table style, and margins. Render the final DOCX to PDF or page images and inspect representative and asset-heavy pages.

Run `scripts/audit_docx.py` after final generation. Treat visual rendering as a separate required gate because OOXML validity does not detect clipping, caption separation, blank pages, or unreadable figures.

## Quality gates

Do not mark the task complete until all applicable gates pass:

- every manuscript number maps to a verified result source;
- no unverified result or citation has been added;
- abstract Methods and main Methods pass the section-boundary audit;
- all realized outputs are reported in Results or explicitly omitted with a reason;
- Discussion opens with a finding synthesis and performs field comparison;
- Discussion ends with exactly three limitation-future improvement pairs in one paragraph;
- every empirical asset is cited before insertion and appears in the correct order;
- figure/caption and table-title/table pairs remain together;
- citations resolve to the reference library and match the configured section policy;
- requested Zotero fields are genuine and counted;
- DOCX ZIP and XML integrity pass;
- no unresolved tokens, missing assets, blank pages, orphan headings, or visible overflow remain;
- all missing administrative or scientific information is listed separately.

## Bundled resources

- `assets/default-profile.json`: configurable biomedical manuscript defaults.
- `assets/source-pack-template.md`: generic source-pack structure.
- `assets/manuscript-contract-template.md`: compact pre-drafting contract.
- `references/section-boundaries.md`: detailed Methods-Results classification and examples.
- `references/discussion-evidence.md`: evidence mapping and comparative Discussion workflow.
- `references/publication-delivery.md`: citations, figures/tables, DOCX, Zotero, and rendering QC.
- `scripts/audit_manuscript.py`: Markdown structure, boundary, citation-marker, and asset-marker audit.
- `scripts/audit_docx.py`: DOCX integrity, Zotero-field, table, drawing, font, and unresolved-token audit.
