---
name: source-pack-builder
description: Build self-checked source packs for any writing task before drafting. Use when the user asks to create a source pack, evidence pack, writing pack, chapter pack, section pack, briefing pack, manuscript preparation pack, report preparation pack, slide content pack, or any pre-writing package for books, chapters, articles, papers, reports, proposals, white papers, medical materials, speeches, emails, training content, or other formal writing. The skill audits project readiness, carefully reads available references, maps each usable source to the document mainline, verifies that its intended citation can connect the surrounding context and advance the argument, and then produces a clean source pack without exposing the internal evidence-alignment assessment.
---

# Source Pack Builder

## Core Rule

Use this skill to prepare writing before drafting. Do not treat a source pack as a rough outline. Treat it as the control document that locks scope, evidence, terminology, examples, structure, boundaries, and drafting rules.

This skill is universal. Do not assume the task is medical, academic, technical, commercial, legal, educational, or chapter-based unless the project materials or user request establish that context.

Treat evidence selection as an argument-design task. Read every source considered for substantive use closely enough to identify the exact proposition it can support, the mainline node it serves, the preceding judgment it continues, and the judgment it enables next. Theme relevance alone is insufficient.

Keep evidence-alignment reasoning in the working layer. Do not expose source-fit scoring, mainline-fit deliberation, transition analysis, or internal inclusion/exclusion rationale in the delivered Source Pack unless the user explicitly requests an audit report.

## Workflow

1. Inventory available project information.
2. Run the source-pack readiness self-check.
3. Lock the core question, target answer, and necessary mainline nodes.
4. Carefully read candidate references and build the internal argument-evidence alignment map.
5. Validate the internal map.
6. Output the standardized readiness assessment without internal alignment deliberation.
7. Decide whether to proceed, proceed conditionally, or stop for user input.
8. If readiness passes, build the source pack requested by the user.

## Step 1: Inventory Available Information

Before asking the user for more input, inspect what can be obtained from the current project, conversation, and accessible files.

Look for:

- User instructions and constraints in the current conversation.
- Existing outlines, drafts, notes, briefs, protocols, proposals, slide decks, manuscripts, reports, tables, bibliographies, reference managers, full-text reference files, source folders, or prior handoff files.
- Existing terminology lists, style rules, brand rules, formatting requirements, citation requirements, audience descriptions, case lists, figure/table plans, or review comments.
- File names and folder structure that reveal project stage, topic, deliverable type, or intended sequence.

Separate facts from inferences. If an element is inferred, label it as inferred in the assessment and source pack.

## Step 2: Self-Check Elements

Assess every element below, even if the final source pack will omit elements that are not applicable.

Use these status labels:

- `Clear`: enough information is available to use directly.
- `Partial`: usable but incomplete; can proceed only with assumptions or conservative wording.
- `Missing`: not available and needed.
- `Not Applicable`: genuinely irrelevant to this writing task.

Required self-check elements:

1. **Writing Object**: deliverable type, title/topic, unit of work, scope, and sequence position.
2. **Purpose**: why the piece is being written and what decision, understanding, behavior, or deliverable it must support.
3. **Audience**: reader type, expertise level, expectations, sensitivities, and use context.
4. **Core Question or Thesis**: the central problem, argument, message, or practical question the writing must answer.
5. **Reader Outcome**: what the reader should know, believe, decide, or be able to do after reading.
6. **Structure**: required outline, section order, headings, length, hierarchy, and any mandatory sequence.
7. **Source Inventory**: available references, data, evidence, notes, prior drafts, examples, interviews, policies, or other source materials.
8. **Evidence Fitness**: whether each source has been read closely enough, supports an exact proposition, serves a necessary mainline node, continues the preceding judgment, advances the next judgment, or should be limited, moved, replaced, or excluded.
9. **Citation and Attribution Rules**: citation style, reference format, source traceability, quote rules, and whether claims need formal citation.
10. **Terminology**: terms that must be standardized, avoided, defined, translated, or kept consistent.
11. **Examples, Cases, or Scenarios**: required cases, analogies, datasets, user stories, clinical cases, business examples, or narrative anchors.
12. **Figures, Tables, and Assets**: visuals, tables, diagrams, charts, appendices, screenshots, templates, or other assets needed.
13. **Boundaries and Risk Controls**: claims not to make, compliance limits, uncertainty language, tone limits, scientific/legal/financial/medical boundaries, and unsupported leaps to avoid.
14. **Style and Format**: tone, register, language, formatting, document type, heading style, word count, and output format.
15. **Dependencies and Missing Inputs**: what must be supplied by the user or obtained before drafting.
16. **Acceptance Criteria**: what must be true for the source pack and later draft to be considered usable.

## Step 3: Lock the Mainline and Align Evidence

Before assigning any reference to a section, write the core question, target answer, and the shortest sequence of judgments needed to connect them.

For every source considered for substantive use:

1. Read the full text when accessible. At minimum inspect the research question, population or material, design or method relevant to the claim, exact result, and authors' interpretation.
2. Record the exact passage or table/figure location that supports the usable proposition.
3. Extract the smallest proposition that can enter the planned document without importing the source's unrelated narrative.
4. Assign the proposition to one mainline node and one evidence task.
5. State internally what the reader already knows immediately before the citation.
6. State internally what new judgment becomes possible immediately after the citation.
7. Check continuity of subject, terminology, tone, abstraction level, and sentence function.
8. Decide to include, move, restrict to background, or exclude.

Use [ARGUMENT_EVIDENCE_ALIGNMENT.md](references/ARGUMENT_EVIDENCE_ALIGNMENT.md) for the complete decision rules. For multi-source or long-form tasks, fill [internal-evidence-alignment.template.json](assets/internal-evidence-alignment.template.json) and validate it:

```bash
python scripts/validate_evidence_alignment.py <internal-evidence-alignment.json>
```

Do not promote a source to `include` when:

- only metadata or an abstract has been inspected for a detailed substantive claim;
- it has topic relevance but no exact usable proposition;
- its placement cannot continue a specific preceding judgment;
- it repeats the current conclusion without adding evidence or inference;
- it creates a side branch that does not return to the mainline;
- no clear downstream judgment follows from its use.

Keep this map in the internal working area. Do not copy its assessment fields or reasoning into the Source Pack. Audit the final pack with:

```bash
python scripts/audit_source_pack_boundary.py <source-pack.md-or-docx>
```

Before moving to readiness output, confirm internally:

- every substantive source has been closely read;
- every included use maps to one necessary mainline node;
- every planned citation continues a specific preceding judgment;
- every planned citation enables a distinct downstream judgment;
- context-breaking or non-progressive sources have been moved, restricted, or excluded;
- the alignment map passes machine validation.

Do not copy this internal completion gate into the delivered Source Pack.

## Step 4: Standard Readiness Assessment Output

Always output a readiness assessment before the source pack unless the user explicitly asks only for a source pack template.

Use this structure:

```markdown
# Source Pack Readiness Assessment

## Readiness Decision

Decision: PASS / CONDITIONAL PASS / BLOCKED
Reason: ...
Next action: ...

## Element Assessment

| Element | Status | Available From Current Project | Gap / Risk | Needed From User or Next Action |
|---|---|---|---|---|
| Writing Object | Clear / Partial / Missing / Not Applicable | ... | ... | ... |
| Purpose | ... | ... | ... | ... |
| Audience | ... | ... | ... | ... |
| Core Question or Thesis | ... | ... | ... | ... |
| Reader Outcome | ... | ... | ... | ... |
| Structure | ... | ... | ... | ... |
| Source Inventory | ... | ... | ... | ... |
| Evidence Fitness | ... | ... | ... | ... |
| Citation and Attribution Rules | ... | ... | ... | ... |
| Terminology | ... | ... | ... | ... |
| Examples, Cases, or Scenarios | ... | ... | ... | ... |
| Figures, Tables, and Assets | ... | ... | ... | ... |
| Boundaries and Risk Controls | ... | ... | ... | ... |
| Style and Format | ... | ... | ... | ... |
| Dependencies and Missing Inputs | ... | ... | ... | ... |
| Acceptance Criteria | ... | ... | ... | ... |

## User Input Needed

- Critical: ...
- Useful but not blocking: ...
```

Keep the assessment concrete. Do not write generic phrases such as "needs more detail" without naming the exact missing detail.

Summarize evidence readiness at the level needed for action. Omit source-by-source mainline-fit reasoning, transition analysis, scores, and internal inclusion/exclusion deliberation.

## Step 5: Readiness Decision Rules

Use `PASS` when:

- Writing object, purpose, audience, core question, structure, and source basis are clear enough to proceed.
- Every source approved for substantive use has passed the internal argument-evidence alignment validation.
- Missing details are minor and do not affect scope, evidence integrity, or compliance boundaries.

Use `CONDITIONAL PASS` when:

- The source pack can be built using explicit assumptions.
- Gaps are manageable if marked as assumptions, limitations, or drafting cautions.
- Sources with incomplete reading access remain background-only and are not assigned to substantive claims.
- The user can later confirm details without invalidating the whole source pack.

Use `BLOCKED` when any of these are missing and cannot be safely inferred:

- What is being written.
- The intended audience or use context.
- The core question, objective, or thesis.
- The source basis for a source-backed writing task.
- A central claim has no closely read source that can connect its preceding judgment to a valid downstream judgment.
- Mandatory format, compliance, legal, medical, financial, or scientific constraints that materially affect content safety.

If `BLOCKED`, ask only the few questions needed to unblock the task. Prefer 1 to 3 questions.

If `PASS` or `CONDITIONAL PASS`, continue immediately to the source pack in the same response or create the requested source-pack file.

## Step 6: Source Pack Output Standard

Build a source pack that is specific enough for a later writer to draft without rediscovering the project.

Use this default structure and adapt labels to the user's domain:

```markdown
# Source Pack: [Title / Unit of Work]

## 1. Scope Lock

- Deliverable:
- Unit of work:
- Position in sequence:
- Working title:
- Included scope:
- Excluded scope:
- Assumptions:

## 2. Purpose and Reader Outcome

- Purpose:
- Target audience:
- Reader starting point:
- Reader outcome:

## 3. Core Question, Thesis, or Message

- Core question:
- Main thesis / message:
- Supporting sub-questions:
- Claims that must be proven:

## 4. Structure Map

| Section | Function | Required Content | Source Basis | Drafting Notes |
|---|---|---|---|---|

## 5. Concept and Terminology Lock

| Term | Required Meaning | Use / Avoid | Notes |
|---|---|---|---|

## 6. Source and Evidence Map

| Source ID / Source | Claim or Use | Support Type | Strength | Limitation | Placement |
|---|---|---|---|---|---|

Support Type options: Direct, Indirect, Background, Example, Counterpoint, Method, Data, Policy, Style, Not for use.

## 7. Cases, Examples, Data, or Scenarios

| Item | Role in Writing | Placement | Evidence Basis | Limits |
|---|---|---|---|---|

## 8. Figures, Tables, and Assets

| Asset | Purpose | Placement | Required Inputs | Notes |
|---|---|---|---|---|

## 9. Boundaries and Risk Controls

- Do not claim:
- Use cautious wording for:
- Required caveats:
- Compliance / scientific / factual constraints:
- Unsupported leaps to avoid:

## 10. Drafting Instructions

- Tone:
- Length:
- Citation approach:
- Style rules:
- Required transitions:
- Terms to use consistently:
- Terms to avoid:

## 11. Open Items

| Item | Blocking? | Owner / Next Action |
|---|---|---|

## 12. Draft-Readiness Checklist

- [ ] Scope is locked.
- [ ] Evidence placement is clear.
- [ ] Indirect or supplemental sources are limited.
- [ ] Terminology is standardized.
- [ ] Cases and visuals are assigned.
- [ ] Risk boundaries are explicit.
- [ ] Missing inputs are either resolved or marked as assumptions.
```

## Quality Rules

- Do not invent sources, data, cases, requirements, or stakeholder intent.
- Do not assign a source from its title, metadata, search snippet, or topic similarity.
- Read the full text or the complete claim-relevant sections before substantive use. Treat abstract-only access as background or a readiness gap.
- Do not use a source for a claim it does not support.
- Do not use a source only because it is relevant to the same topic.
- Require each included source to perform a clear evidence task at a defined mainline node.
- Require each planned citation to connect a preceding judgment to a distinct downstream judgment.
- Synthesize sources that perform the same task; avoid source-by-source summary sequences.
- Mark indirect, background, or supplemental evidence explicitly.
- Convert missing information into either a user question, a conservative assumption, or a non-blocking open item.
- Keep the source pack operational, not essay-like. It should guide drafting decisions.
- Keep the internal alignment map, fit judgments, transition reasoning, and exclusion rationale out of the delivered Source Pack.
- Preserve any user-specified order exactly. If the user requires sequential writing, enforce that order in the source pack.
- If a later draft will be formal, regulatory, clinical, legal, financial, or scientific, include stronger boundary controls and evidence-use limits.

## Minimal Source Pack

When time or material is limited, still include:

1. Scope lock.
2. Purpose and audience.
3. Core question or thesis.
4. Source and evidence map.
5. Required structure.
6. Boundaries and risk controls.
7. Open items.

Do not skip the readiness assessment unless explicitly requested.
