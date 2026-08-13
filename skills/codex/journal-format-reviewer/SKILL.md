---
name: journal-format-reviewer
description: Strictly audit a manuscript for journal-format compliance and report all non-compliant items without directly editing the manuscript. Use when the user wants a journal-format check, submission-readiness audit, formatting review, structure review, title page check, abstract/keywords compliance check, reference style consistency check, figure-table callout audit, or missing declarations review for a biomedical manuscript.
---

# Journal Format Reviewer

## When to use this skill

Use this skill when the user wants an audit-only review of manuscript formatting, structure, completeness, and submission readiness.

This skill is for compliance review, not rewriting. It should identify problems for the main agent to fix later.

## Instructions

1. Read the manuscript and any target-journal requirements the user provides.
2. If official journal instructions are unavailable, state that explicitly and perform only a cautious pre-check based on common biomedical journal conventions.
3. Do not directly revise the manuscript. Do not output a rewritten full manuscript.
4. Audit for:
   - title page completeness
   - author names, affiliations, and corresponding author block
   - running title where relevant
   - abstract structure and probable word-limit issues
   - keyword count and style
   - section order and heading hierarchy
   - abbreviation definition at first mention
   - units, nomenclature, capitalization, italics, and style consistency
   - statistical formatting such as `n`, `%`, `P`, `CI`, `SD`, `SE`, and decimal consistency
   - figure/table numbering, legends, titles, footnotes, and in-text callouts
   - reference formatting consistency
   - declarations including ethics, consent, registration, funding, conflicts, contributions, data availability, acknowledgments, and supplementary labels
   - internal consistency across title, abstract, main text, tables, figures, and references
   - missing sections or other likely submission blockers
5. Use the strict reporting schema in [references/review-schema.md](./references/review-schema.md).
6. Prefer exhaustive issue identification over elegant prose.
7. Do not fabricate missing information. Flag missing items and say when author confirmation is required.

## Output contract

Return the audit in this order:

- A. Overall review verdict
- B. Critical submission-blocking issues
- C. Major format/structure issues
- D. Minor consistency/style issues
- E. Possible journal-specific issues requiring confirmation
- F. Missing information requiring author input
- G. Priority-ranked action list for the main agent

For exact issue fields and hard constraints, follow [references/review-schema.md](./references/review-schema.md).
