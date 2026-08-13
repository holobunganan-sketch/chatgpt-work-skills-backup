# Page Blueprint V2

## Purpose

Define the hard-gate intermediate object between source content and final slide generation.

## Rule

Produce a page blueprint for every page before final drafting. Do not skip blueprint creation, even when the user asks for a direct final page.

## Hard Gate

Do not continue to final slide generation unless the blueprint explicitly answers:

- `what_must_be_seen_first`
- `information_loss_if_text_only`

If either field is missing or vague, stop at blueprint level.

## Required Fields

```json
{
  "page_id": "S03",
  "deck_position": "middle / mechanism cluster",
  "page_role": "mechanism explanation",
  "narrative_function": "Show how A leads to B through a three-step path.",
  "page_type": "multi-stage-path-page",
  "visual_center": "A left-to-right pathway chain occupying the main zone.",
  "graphic_priority": "high",
  "svg_needed": true,
  "svg_module_candidate": "pathway-chain",
  "text_density": "low",
  "ppt_native_blocks": ["title", "subtitle", "short explanation", "takeaway", "reference strip"],
  "chart_or_diagram_goal": "Clarify directional mechanism logic with checkpoints.",
  "key_message": "A drives B through a visible three-step chain.",
  "what_must_be_seen_first": "The direction and sequence of the pathway.",
  "what_should_remain_outside_svg": ["title", "long explanation", "references", "takeaway box"],
  "generic_consulting_layout_forbidden": true,
  "reuse_candidate_module": "pathway-chain",
  "information_loss_if_text_only": "The audience would lose stage order, dependency, and intervention-point visibility.",
  "title_zone": {
    "title": "A Drives B Through a Three-Step Pathway",
    "subtitle": "Mechanism overview",
    "tone": "professional"
  },
  "main_visual_zone": {
    "purpose": "Show the ordered mechanism",
    "content_blocks": ["A", "Stage 1", "Stage 2", "B"],
    "svg_scope": ["nodes", "arrows", "checkpoints"],
    "native_ppt_scope": ["title", "annotation strip", "references"]
  },
  "explanation_zone": {
    "format": "short bullets",
    "content": ["Stage 1 primes the system", "Stage 2 amplifies the effect"]
  },
  "conclusion_zone": {
    "format": "takeaway box",
    "content": "The intervention point sits between Stage 1 and Stage 2."
  },
  "reference_zone": {
    "format": "footnote",
    "content": ["reference 1"]
  },
  "style_keywords": ["graphic-led", "clean", "restrained"],
  "avoid_list": ["long paragraph in SVG", "generic issue-roadmap layout"],
  "open_questions": ["待用户确认: exact quantitative effect size"]
}
```

## Field Definitions

### `page_role`

State the job of the page in the deck.

### `narrative_function`

State what cognition the page advances.

### `visual_center`

State the visual object or visual region that must dominate the page.

### `graphic_priority`

Use:

- `high`
- `medium`
- `low`

Default to `high` for mechanism, path, comparison, hierarchy, system, relationship, and decision pages.

### `svg_needed`

Set to `true` when the page meaning depends on geometry, direction, layering, relationship, or diagram precision.

### `svg_module_candidate`

Choose the most reusable module candidate. Use `none` only when the page is genuinely not diagram-led.

### `text_density`

Use:

- `low`
- `medium`
- `high`

Prefer `low` or `medium` for graphic-led pages.

### `ppt_native_blocks`

List the blocks that must remain editable in PowerPoint native objects.

### `chart_or_diagram_goal`

State what the main diagram must prove, clarify, or compare.

### `key_message`

State the one idea the page must land.

### `what_must_be_seen_first`

State the first visual fact the audience must perceive before reading supporting text.

### `what_should_remain_outside_svg`

List all content that should stay out of the SVG region.

### `generic_consulting_layout_forbidden`

Set to `true` unless the user explicitly requests consulting or management-report rhetoric.

### `reuse_candidate_module`

Name the page or graphic module that should be reused.

### `information_loss_if_text_only`

State exactly what would be lost if the page became only paragraphs or bullets.

## Blueprint Quality Checks

A valid blueprint must satisfy all of the following:

1. State one clear key message.
2. State one narrative function.
3. State one visual center.
4. State whether SVG is needed.
5. State what must be seen first.
6. State what would be lost in a text-only version.
7. State what must remain outside SVG.
8. Explicitly block generic consulting layout when not requested.
9. Contain at least one avoid-item tied to execution risk.
10. Mark missing facts in `open_questions`.

## Stop Conditions

Stop at blueprint level when:

- `what_must_be_seen_first` is vague
- `information_loss_if_text_only` is vague
- the main visual goal is unclear
- the page has no defensible visual center
- the page is drifting into a generic business-template skeleton
