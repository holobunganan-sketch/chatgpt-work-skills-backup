---
name: presentation-production-system
description: Build reusable, high-quality presentation systems for any professional domain by converting complex source material into graphic-first slide blueprints, diagram-led page specifications, and mixed PPT/SVG slide outputs. This skill should be used when the task involves turning mechanisms, relationships, paths, systems, comparisons, hierarchies, or dense concepts into professional visual argument pages rather than defaulting to generic business-deck templates.
---

# Presentation Production System

## Overview

Build presentations as a graphic-narrative production system, not as a generic report generator. Route each request through narrative analysis, visual-center selection, page typing, blueprint gating, and mixed rendering decisions before generating any final slide content.

Prioritize argument quality, visual argument density, and information flow over novelty. Treat each slide as a visual reasoning unit inside a larger deck, then decide whether the page should be graphic-led, graphic-plus-text, data-led, or only minimally text-led.

## Use This Skill For

Trigger this skill when the request includes any of the following:

- Build a full deck from a topic, objective, outline, manuscript, notes, screenshots, table, or mixed materials.
- Design or rewrite one slide with a clear role in a larger presentation.
- Refactor an existing slide or deck to improve clarity, structure, logic, or professional quality.
- Produce complex explanatory diagrams, mechanism pages, relationship maps, path diagrams, comparison structures, layered systems, or decision logic pages.
- Convert dense or fragmented source content into a graphic-led slide system with reusable page and diagram modules.
- Decide what belongs in SVG and what must remain editable in native PPT elements.

Do not use this skill as a pure copywriting shortcut, a pure layout shortcut, a generic management-deck generator, or a fantasy "fully automatic deck generator" that invents missing facts.

## Operating Principles

Apply these rules on every invocation:

1. Determine the presentation goal before drafting any slide.
2. Identify what cognition the slide must advance before choosing any layout.
3. Determine whether text-only treatment would cause material information loss.
4. Route any mechanism, relation, hierarchy, comparison, system, path, or decision content to graphic-first evaluation before considering generic text layouts.
5. Produce a page blueprint before every final page. Treat blueprint approval as a hard gate, not a suggestion.
6. Keep long-form explanation, citations, speaker support text, and editable text blocks in native PPT structures by default.
7. Treat SVG as a primary rendering option for complex graphic main zones, not as an optional embellishment.
8. Reuse existing graphic page types and diagram modules instead of improvising a one-off page when a standard module fits.
9. Mark uncertain facts as `待用户确认` instead of inventing specifics, but do not let placeholder text take over the main visual zone.
10. Preserve a consistent grid, label logic, color system, and information density across the deck.
11. Prefer claim-led page titles over section-label titles.
12. Prefer conservative clarity over decorative complexity.

## Required Workflow

Follow this sequence. Do not skip ahead unless the user explicitly narrows the task.

1. Read the task and classify the work mode using `references/execution-contract.md`.
2. Apply `references/graphic-first-routing.md` before choosing any generic deck skeleton.
3. Analyze narrative inputs and completeness using `references/workflow-core.md`.
4. Convert the request into a deck-level or page-level structure centered on argument pages rather than generic sections.
5. Assign each page a role, a narrative function, and a page type using `references/page-types.md`.
6. Draft the page blueprint using `references/page-blueprint-v2.md` or `assets/templates/page_blueprint.template.json`.
7. Stop if `what_must_be_seen_first` or `information_loss_if_text_only` is unresolved.
8. Select a graphic grammar from `references/graphic-modules.md` whenever the page carries relationship-heavy meaning.
9. Apply the visual and editorial rules in `references/style-system.md` and the guardrails in `references/anti-generic-consulting-guardrails.md`.
10. Validate the blueprint structure with `scripts/validate_blueprint.py` when the output is JSON.
11. Generate the requested deliverable: argument-page sequence, page blueprint set, single-slide spec, or final slide draft.

## Work Modes

Route the request into one of these modes before generating output:

- Full deck generation: Build a narrative spine, slide list, and page blueprints for an entire presentation.
- Single-slide generation: Solve one slide with explicit upstream/downstream context.
- Refactor mode: Reorganize existing content without losing source intent.
- Graphic-first mode: Produce blueprint plus SVG plan before final slide details.
- Structure-first mode: Produce storyline, page order, and slide purposes before page drafting.
- Assembly mode: Assemble user-provided title, copy, and sketches into a clean slide blueprint or final slide spec.

See `references/execution-contract.md` for triggers, required outputs, downgrade rules, and stop conditions.

## Resource Map

Load only the files needed for the current task:

- `references/execution-contract.md`
  Use to classify mode, define boundaries, and apply failure handling.
- `references/graphic-first-routing.md`
  Use to decide whether the page must be graphic-led before any generic page skeleton is considered.
- `references/workflow-core.md`
  Use to execute the ordered production pipeline from brief to slide output.
- `references/page-blueprint-v2.md`
  Use to build stable page-blueprint objects and inspect required hard-gate fields.
- `references/page-types.md`
  Use to choose argument-page roles and standard graphic-led page grammars.
- `references/graphic-modules.md`
  Use to choose reusable SVG-capable main-zone diagram modules.
- `references/style-system.md`
  Use to enforce visual and editorial consistency.
- `references/anti-generic-consulting-guardrails.md`
  Use to prevent regression into agenda-heavy, template-heavy, text-heavy consulting deck defaults.
- `references/development-guide.md`
  Use when extending the skill with new page types, graphic grammars, or style themes.
- `references/examples.md`
  Use for compact examples of the expected method and output form.
- `assets/templates/page_blueprint.template.json`
  Copy when a structured blueprint artifact is needed.
- `assets/templates/deck_brief.template.md`
  Copy when the user needs help structuring inputs.
- `scripts/validate_blueprint.py`
  Run to validate JSON blueprint files against required keys and boundary rules.

## Output Rules

Produce artifacts, not process commentary, unless the user explicitly asks for explanation.

Default output priority:

1. Graphic-led argument pages or page sequence
2. Page blueprint set
3. Graphic module selection and SVG plan
4. Data/diagram-backed final slide content
5. Minimal text-only supporting pages

When information is incomplete, stop at the highest-confidence artifact instead of fabricating details. Prefer blueprints, graphic routing, structure drafts, and flagged assumptions over fake completeness.
