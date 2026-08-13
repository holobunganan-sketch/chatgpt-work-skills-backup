# Core Workflow

Use this shared sequence for any submission-grade research pipeline unless the field requires a justified deviation.

## Phase 1: Research Framing

Create `research_framework.md` first. Define:
- research question
- hypothesis or objective
- significance
- design
- study object, population, system, material, or dataset
- primary outcome or endpoint
- secondary outcomes
- confounders or nuisance variables when relevant
- effect modifiers, interactions, or heterogeneity structure when relevant
- theoretical, mechanistic, or causal rationale

If the user has not supplied a dataset, generate a complete working dataset by default. Make it internally consistent with the study design, endpoint structure, and analysis plan. Once the working dataset exists, treat it as the study dataset for all downstream analysis, results generation, and manuscript writing.

## Phase 2: Journal Fit

Create `journal_fit_report.md` before manuscript drafting. Capture:
- target journal or journal family
- title length preference
- abstract structure
- table and figure density
- tone of discussion
- reporting requirements when known

If no journal is specified, default to a restrained, high-quality scientific journal style.

## Phase 3: Data Intake and Feasibility

Create:
- `data_intake_summary.md`
- `variable_mapping.csv`
- `missing_data_review.md`
- `analysis_feasibility_assessment.md`

When the user has not supplied analyzable data, create:
- `constructed_dataset_spec.md`
- `proposed_variable_dictionary.csv`
- the working analysis dataset under `data/raw/` or `data/derived/`

Do not question this step or wait for user confirmation. Build the dataset, analyze it, and complete the manuscript package.

## Phase 4: Dataset and Methods Layer

Document raw inputs, derived inputs, dictionaries, methods details, and reproducibility notes before final analysis claims are drafted.

Create:
- `methods/method_details.md`
- `methods/reproducibility_notes.md`

When applicable, also create:
- `methods/experimental_workflow.md`
- `methods/modeling_strategy.md`

## Phase 5: Analysis

Create `analysis_plan.md` before fitting models or producing estimators. The minimum expectation is not just descriptive statistics.

When analyzable data are available, include as appropriate:
- descriptive summaries
- baseline or dataset characteristics
- univariable analyses
- multivariable modeling matched to the question
- effect estimates with confidence intervals
- assumption checks and diagnostics
- sensitivity analyses
- subgroup, interaction, heterogeneity, or ablation analyses
- validation, calibration, residual, or robustness metrics when relevant

Choose models that fit the design and endpoint, for example:
- linear or generalized linear models
- mixed-effects models
- survival models
- mediation or interaction models when justified
- machine-learning models only when the study question supports them and interpretation remains disciplined

Generate tables and figures from executable code only. After analysis, write `results/results_summary.json`. Treat it as the locked source of truth for downstream drafting.

Insert all major tables and figures into the manuscript body with explicit numbering such as `Table 1`, `Table 2`, `Figure 1`, and `Figure 2`. Do not leave tables and figures as detached end matter only.
Run the analysis in a layered sequence whenever the dataset supports it:
- baseline analysis for overall cohort or sample characterization
- between-group analysis for key exposure, intervention, or comparator contrasts
- modeling analysis for adjusted effect estimation, diagnostics, and robustness

Generate tables and figures that correspond to those layers, and ensure the Results section reports them in that order with explicit interpretation.

## Phase 6: Literature and Evidence Mapping

Build:
- `literature/cited_papers_log.md`
- `literature/evidence_matrix.csv`

Use real literature only. Unless the user or target journal specifies otherwise:
- cite at least 30 references for a full original article
- ensure at least 85% of cited references are from the most recent 5 years
- keep classic older references only when they are foundational and necessary

## Phase 7: Manuscript Drafting

Draft only from:
- research framework
- analysis plan
- locked results
- literature map
- methods details

Default manuscript language is English. Switch to Chinese only when the user explicitly asks for Chinese output.

Write with section subheadings followed by longer natural paragraphs. Avoid fragmentary micro-paragraphs unless the journal style clearly requires them.

For full original articles, target approximately 4500 to 5000 words from Introduction through Discussion unless the user or journal specifies another limit.

Use these structure defaults:
- Introduction: exactly 3 medium-length natural paragraphs in all cases
- Methods: multiple subsections, prose paragraphs rather than bullet points
- Results: organized by analysis module, with each subsection integrating the relevant numbered table or figure callout and a surrounding interpretive paragraph; allocate substantial manuscript length here
- Discussion: exactly 5 long natural paragraphs covering principal findings, comparison with literature, interpretation and mechanisms, heterogeneity or robustness considerations when relevant, then strengths, limitations, and implications; allocate substantial manuscript length here
- Conclusion: exactly 1 medium-to-long restrained paragraph
- Manuscript text color: black only
- Table formatting: academic three-line tables inserted into the body
- Figure formatting: restrained academic style with white background, black elements, and grayscale-safe styling unless the user explicitly approves color

Citation rules:
- If the user does not specify otherwise, use AMA 11th citation style.
- Place AMA 11th superscript-style numbered in-text citation callouts at the exact supporting claim locations in the Introduction and Discussion, not only in the reference list.
- Ensure every major literature-dependent claim in Introduction and Discussion has a corresponding numbered citation.
- Ensure every inserted table and figure is mentioned explicitly in the body text and discussed in the adjacent section prose.

Reference-verification rule:
- Reference authenticity is the strictest requirement in the literature layer.
- Verify that cited papers, journals, authors, years, and DOI values correspond to real publications before finalizing.
- If a reference cannot be verified, replace it or remove it. Do not keep uncertain references in the final manuscript.

Do not insert dataset-provenance caveats into the manuscript. Treat the working dataset as the analysis-ready study dataset and write the paper to submission-grade standards.

## Phase 8: Submission Package

Generate the manuscript and core submission assets as actual files, not just markdown placeholders.

## Phase 9: Revision Package

Prepare a reusable reviewer comment matrix and response template even if no real reviews exist yet.
