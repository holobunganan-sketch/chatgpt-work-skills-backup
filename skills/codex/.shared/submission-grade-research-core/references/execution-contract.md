# Execution Contract

Treat this file as the highest-priority operating contract inside the research pipeline skill.

## Mandatory Sequence

Follow this order exactly:
1. Build the research framework.
2. Define journal fit.
3. Build or ingest the working dataset.
4. Create the analysis plan.
5. Run the full analysis and lock `results/results_summary.json`.
6. Build tables and figures from code.
7. Retrieve and verify literature.
8. Draft the manuscript.
9. Generate submission assets.
10. Run quality control and revise until the draft passes or only explicitly documented limitations remain.

Do not skip analysis and jump straight to prose.
Do not stop after a short draft when the request is for a full paper.
Do not treat missing user-supplied data as a reason to wait. Generate the working dataset and continue.

## Non-Negotiable Defaults

- Default manuscript language: English
- Default article type: full original article
- Default main-text target: 4500 to 5000 words from Introduction through Discussion
- Default reference minimum: 30
- Default recent-reference target: at least 85% from the most recent 5 years
- Default structure: section subheadings followed by developed academic paragraphs
- Default Introduction: exactly 3 medium-length paragraphs
- Default Discussion: exactly 5 long paragraphs
- Default Conclusion: exactly 1 medium-to-long paragraph
- Reference authenticity is the top literature constraint
- Default in-text citation style: AMA 11th superscript numbered citations placed at claim locations in the body text
- Default figure style: white background, black elements, grayscale-safe, no color unless explicitly authorized
- Default manuscript text color: black only
- Default table presentation: academic three-line-table style inserted into the manuscript body
- Default analysis depth sequence: baseline analysis, group-comparison analysis, then modeling analysis with supporting diagnostics and figures

## Failure Conditions

The draft is not ready if any of the following is true:
- the main text is far below target length without journal justification
- the references are below the minimum target
- any reference, journal, author line, year, or DOI is unverified or suspect
- the discussion only restates results
- the statistics stop at shallow descriptive comparisons when the topic supports richer modeling
- the manuscript reads like an outline, demo, template, or workflow artifact
- the paper contains provenance caveats about the working dataset
- tables, figures, and claims are not aligned with locked results
- major tables and figures are not inserted, numbered, cited, and discussed in the body
- Introduction or Discussion lacks in-text numbered citations under the default AMA-style workflow
- citations are not formatted as AMA-style superscript callouts in the manuscript body unless the target journal explicitly requires a different presentation
- tables are not presented in academic three-line style unless the target journal explicitly requires another layout
- figures use color without user or journal authorization, or otherwise depart from a restrained academic black-and-white style
- the manuscript body uses non-black font colors for emphasis
- the analysis does not progress through baseline, group-comparison, and modeling layers when the dataset supports that sequence
- Introduction does not have exactly 3 paragraphs
- Discussion does not have exactly 5 paragraphs
- Conclusion does not have exactly 1 medium-to-long paragraph

If a failure condition is present, revise before finalizing.

## Finalization Rule

Before considering the work complete:
- run the file-level QC script
- run the manuscript QC script
- fix any failures that are correctable
- document only the residual limitations that cannot be resolved within the workflow
