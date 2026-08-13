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
│   │   └── data.csv
│   ├── derived/
│   │   └── derived_dataset.csv
│   └── data_dictionary.csv
├── analysis/
│   └── analysis_code.py
├── results/
│   └── results_summary.json
├── tables/
│   ├── table1_baseline_characteristics.csv
│   ├── table2_group_comparisons.csv
│   └── table3_modeling_results.csv
├── figures/
│   ├── figure1_patient_flowchart.png
│   ├── figure2_baseline_profile.png
│   ├── figure3_group_comparison_plot.png
│   ├── figure4_primary_outcome_plot.png
│   └── figure5_model_diagnostics_or_subgroup_plot.png
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

1. Keep `results/results_summary.json` as the only quantitative source for manuscript claims.
2. Keep each table and figure reproducible from analysis code.
3. List every generated artifact in `submission/file_manifest.md`.
4. Mark any omitted required file as `not generated` with a reason.
5. Treat the working dataset as the study dataset throughout the analysis and manuscript unless the user explicitly requests a different framing.
6. Expect inserted manuscript tables to follow academic three-line formatting unless a journal override is documented.
7. Expect manuscript figures to use white backgrounds and black elements unless color approval is documented.

Recommended `results_summary.json` sections:

```json
{
  "rigor_level": "submission",
  "manuscript_type": "original_article",
  "sample": {
    "n_total": 0,
    "n_analyzed": 0
  },
  "baseline_analysis": {},
  "group_comparison_analysis": {},
  "modeling_analysis": {},
  "secondary_analyses": [],
  "sensitivity_analyses": [],
  "subgroup_analyses": [],
  "diagnostics": {},
  "table_index": [],
  "figure_index": [],
  "limitations": []
}
```
