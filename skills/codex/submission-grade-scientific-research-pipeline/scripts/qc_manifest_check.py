#!/usr/bin/env python3
"""Check whether a scientific research project contains the minimum submission assets."""

from __future__ import annotations

import argparse
from pathlib import Path


COMMON_REQUIRED = [
    "project_plan.md",
    "research_framework.md",
    "journal_fit_report.md",
    "analysis_plan.md",
    "methods/method_details.md",
    "methods/reproducibility_notes.md",
    "data_intake_summary.md",
    "missing_data_review.md",
    "analysis_feasibility_assessment.md",
    "variable_mapping.csv",
    "data/data_dictionary.csv",
    "analysis/analysis_code.py",
    "results/results_summary.json",
    "literature/cited_papers_log.md",
    "literature/evidence_matrix.csv",
    "submission/submission_checklist.md",
    "submission/file_manifest.md",
]

DOCX_REQUIRED = [
    "docs/manuscript.docx",
    "docs/abstract.docx",
    "docs/title_page.docx",
    "docs/cover_letter.docx",
    "docs/figure_legend.docx",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", help="Path to the project root")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    missing: list[str] = []

    for rel in COMMON_REQUIRED + DOCX_REQUIRED:
        if not (root / rel).exists():
            missing.append(rel)

    print(f"Project root: {root}")
    if missing:
        print("Missing required artifacts:")
        for rel in missing:
            print(f"- {rel}")
        return 1

    print("All minimum required artifacts are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
