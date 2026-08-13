# File Contract

Use this layout unless the user already has an established repository structure:

```text
project-root/
├── project_plan.md
├── research_framework.md
├── journal_fit_report.md
├── data_intake_summary.md
├── missing_data_review.md
├── analysis_feasibility_assessment.md
├── constructed_dataset_spec.md                # when a working dataset is built inside the workflow
├── proposed_variable_dictionary.csv           # when a working dataset is built inside the workflow
├── analysis_plan.md
├── variable_mapping.csv
├── data/
│   ├── raw/
│   ├── derived/
│   │   └── derived_dataset.csv
│   └── data_dictionary.csv
├── methods/
│   ├── method_details.md
│   ├── reproducibility_notes.md
│   ├── modeling_strategy.md
│   └── experimental_workflow.md               # when applicable
├── analysis/
│   └── analysis_code.py
├── results/
│   └── results_summary.json
├── tables/
├── figures/
├── literature/
│   ├── cited_papers_log.md
│   └── evidence_matrix.csv
├── docs/
│   ├── manuscript.docx
│   ├── abstract.docx
│   ├── title_page.docx
│   ├── cover_letter.docx
│   ├── figure_legend.docx
│   └── highlights.docx
├── submission/
│   ├── submission_checklist.md
│   └── file_manifest.md
└── revision/
    ├── reviewer_comment_matrix.docx
    └── response_to_reviewers.docx
```

Minimum locked-result rules:

1. Keep `results/results_summary.json` as the only quantitative or computational source for manuscript claims.
2. Keep each table and figure reproducible from analysis code.
3. List every generated artifact in `submission/file_manifest.md`.
4. Mark any omitted required file as `not generated` with a reason.
5. Treat the working dataset as the study dataset throughout the analysis and manuscript unless the user explicitly requests a different framing.

Recommended `results_summary.json` sections:

```json
{
  "rigor_level": "submission",
  "manuscript_type": "original_article",
  "sample_or_system": {},
  "descriptive": {},
  "primary_analysis": {},
  "secondary_analyses": [],
  "sensitivity_analyses": [],
  "subgroup_or_heterogeneity_analyses": [],
  "diagnostics": {},
  "table_index": [],
  "figure_index": [],
  "limitations": []
}
```
