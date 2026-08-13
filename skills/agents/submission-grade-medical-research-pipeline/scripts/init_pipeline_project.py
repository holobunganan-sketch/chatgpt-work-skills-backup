#!/usr/bin/env python3
"""Scaffold a submission-grade medical research project tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VALID_RIGOR = {"prototype", "submission", "high_rigor"}
VALID_TYPES = {
    "original_article",
    "brief_report",
    "narrative_review",
    "systematic_style_overview",
    "methods_paper",
}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_project_plan(topic: str, rigor: str, manuscript_type: str, output_language: str) -> str:
    return f"""# Project Plan

## Study Setup

- Topic: {topic}
- Rigor level: {rigor}
- Manuscript type: {manuscript_type}
- Output language: {output_language}

## Planned Phases

1. Research framing
2. Journal fit
3. Data intake and feasibility
4. Dataset and methods layer
5. Statistical analysis
6. Literature retrieval
7. Manuscript drafting
8. Submission package assembly
9. Revision package preparation

## Default manuscript targets

- Main text length from Introduction through Discussion: approximately 4500 to 5000 words
- References: at least 30
- Recent references target: at least 85% from the most recent 5 years
- Default manuscript language: English unless explicitly requested otherwise

## Notes

- Treat `results/results_summary.json` as the locked source of truth after analysis.
- Mark any missing citation as `citation needed` or `source pending`.
- If the user does not provide data, generate a complete working dataset and treat it as the study dataset for downstream analysis and writing.
"""


def build_results_stub(rigor: str, manuscript_type: str) -> dict:
    return {
        "rigor_level": rigor,
        "manuscript_type": manuscript_type,
        "sample": {"n_total": None, "n_analyzed": None},
        "descriptive": {},
        "primary_analysis": {},
        "secondary_analyses": [],
        "sensitivity_analyses": [],
        "subgroup_analyses": [],
        "diagnostics": {},
        "table_index": [],
        "figure_index": [],
        "limitations": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", help="Directory for the project scaffold")
    parser.add_argument("--topic", default="TBD medical research topic")
    parser.add_argument("--rigor-level", default="submission", choices=sorted(VALID_RIGOR))
    parser.add_argument(
        "--manuscript-type",
        default="original_article",
        choices=sorted(VALID_TYPES),
    )
    parser.add_argument("--output-language", default="English")
    args = parser.parse_args()

    root = Path(args.output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)

    dirs = [
        "data/raw",
        "data/derived",
        "analysis",
        "results",
        "tables",
        "figures",
        "literature",
        "docs",
        "submission",
        "revision",
    ]
    for rel in dirs:
        (root / rel).mkdir(parents=True, exist_ok=True)

    write_text(
        root / "project_plan.md",
        build_project_plan(args.topic, args.rigor_level, args.manuscript_type, args.output_language),
    )
    write_text(root / "research_framework.md", "# Research Framework\n\nTBD\n")
    write_text(root / "journal_fit_report.md", "# Journal Fit Report\n\nTBD\n")
    write_text(root / "analysis_plan.md", "# Analysis Plan\n\nTBD\n")
    write_text(root / "data_intake_summary.md", "# Data Intake Summary\n\nTBD\n")
    write_text(root / "missing_data_review.md", "# Missing Data Review\n\nTBD\n")
    write_text(
        root / "analysis_feasibility_assessment.md",
        "# Analysis Feasibility Assessment\n\nTBD\n",
    )
    write_text(
        root / "variable_mapping.csv",
        "source_variable,analysis_variable,definition,unit,notes\n",
    )
    write_text(root / "constructed_dataset_spec.md", "# Constructed Dataset Specification\n\nTBD\n")
    write_text(root / "proposed_variable_dictionary.csv", "variable_name,label,type,unit,allowed_values,notes\n")
    write_text(root / "literature/cited_papers_log.md", "# Cited Papers Log\n\n")
    write_text(
        root / "literature/evidence_matrix.csv",
        "citation_key,role,claim_supported,study_design,population,doi,year,notes\n",
    )
    write_text(
        root / "data/data_dictionary.csv",
        "variable_name,label,type,unit,allowed_values,missing_rule,source\n",
    )
    write_text(root / "data/derived/derived_dataset.csv", "")
    write_text(root / "analysis/analysis_code.py", "# analysis entrypoint\n")
    write_json(root / "results/results_summary.json", build_results_stub(args.rigor_level, args.manuscript_type))
    write_text(
        root / "submission/submission_checklist.md",
        f"# Submission Checklist\n\n- Output language: {args.output_language}\n- Target word count: 4500-5000\n- Minimum references: 30\n",
    )
    write_text(
        root / "submission/file_manifest.md",
        f"# File Manifest\n\n- Output language: {args.output_language}\n",
    )

    print(f"Created medical research scaffold at: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
