# Execution Contract

## Purpose

Define the operating boundary for the presentation production system. Enforce mode selection, required inputs, output contracts, and downgrade behavior.

## Core Contract

Treat every request as a presentation-production task with five explicit decisions:

1. Determine the user goal.
2. Determine the content completeness level.
3. Determine the work mode.
4. Determine the output depth.
5. Determine whether generation may proceed to final slides or must stop at blueprint level.

Treat the default goal as graphic narrative transformation, not generic management-deck assembly.

## Allowed Inputs

Accept any of the following as valid starting material:

- topic or theme
- objective or key message
- audience description
- deck outline
- slide title list
- raw notes or transcript
- draft paragraphs
- tables or charts
- screenshots
- old slides or old deck text
- references or citations
- scattered ideas

## Input Completeness Levels

Classify the request before generating.

### Level A: Minimal

Contains only topic, rough objective, or sparse notes.

Default action:

- produce narrative options
- produce page sequence proposal
- produce page blueprints
- avoid fake data, fake evidence, and fake mechanisms

### Level B: Partial

Contains topic, objective, some audience context, and some source content.

Default action:

- produce narrative structure
- produce slide list
- produce page blueprints
- produce selective final slide drafts when confidence is high

### Level C: Rich

Contains outline, source copy, structured data, or existing slides.

Default action:

- produce full slide plan
- produce page blueprints
- produce final slide specs or final content pages

## Work Mode Routing

Select exactly one primary mode.

### 1. Full Deck Generation

Use when the request concerns a deck, talk, report, workshop, lecture, investor pitch, scientific presentation, training, or business review.

Required output:

- narrative spine
- argument-page list
- page-type assignment
- blueprint per slide or per key slide

### 2. Single-Slide Generation

Use when the user asks for one slide or one page.

Required output:

- page role
- page type
- blueprint
- final page spec when enough information exists

### 3. Refactor Mode

Use when the user already has old pages, copied content, or a draft deck that needs restructuring.

Required output:

- source diagnosis
- revised slide role or slide order
- rewritten blueprint

### 4. Graphic-First Mode

Use when the request centers on mechanism figures, workflows, relationship maps, timelines, or dense diagrams.

Required output:

- page blueprint
- graphic module selection
- SVG region plan
- native PPT region plan

This mode should be considered first for mechanism, comparison, path, hierarchy, system, and network content.

### 5. Structure-First Mode

Use when the user needs logic, storyline, or report architecture more than finished slide text.

Required output:

- argument chain
- slide sequence
- page intents

### 6. Assembly Mode

Use when titles, body copy, and sketches already exist and need disciplined arrangement.

Required output:

- hierarchy cleanup
- layout plan
- region assignment
- blueprint or final page spec

## Boundary Rules

Always enforce the following:

1. Do not invent data, citations, chronology, causal chains, or organizational structures.
2. Do not place long explanatory paragraphs inside SVG by default.
3. Do not encode an entire slide as one uneditable SVG unless explicitly requested.
4. Do not skip slide-role definition.
5. Do not jump directly to visual rendering before structure, routing, and blueprint gating.
6. Do not optimize for flashy variety at the expense of system consistency.
7. Do not default to agenda-heavy, issue-heavy, roadmap-heavy, or closing-ask-heavy business skeletons.
8. Do not allow generic consulting layout to become the dominant deck shape unless explicitly requested.

## Required Output Layers

Choose the highest valid layer according to input completeness.

### Layer 1: Structure Draft

Return when information is sparse.

Includes:

- central message
- audience objective
- argument-page sequence
- page-type suggestions

### Layer 2: Page Blueprint

Return by default when information is partial or when the request explicitly asks for planning.

Includes:

- required blueprint fields
- rendering decision
- content allocation
- visual center
- information-loss check

### Layer 3: Final Slide Spec

Return when information is rich and the user asks for slide-ready output.

Includes:

- titles
- section copy
- layout instructions
- graphic module instructions
- editable text allocation

## Failure and Downgrade Policy

When certainty is low, downgrade output instead of hallucinating.

| Condition | Required response |
| --- | --- |
| Goal unclear | Ask for goal or provide 2-3 narrative directions |
| Audience unclear | Use neutral professional tone and mark audience sensitivity |
| Data missing | Output blueprint, not fake data slide |
| Mechanism uncertain | Output abstract structure and mark `待用户确认` |
| Visual request too complex | Output graphic module plan before full drawing |
| Time constrained | Reduce decorative density, keep structure intact |
| Graphic center unclear | Stop at blueprint and define visual center before page generation |

## Stop Conditions

Stop at blueprint level when any of the following is true:

- source facts are missing
- page role in the deck is unclear
- chart values are absent
- the user asks for planning first
- graphic relationships are too ambiguous to draw responsibly
- `what_must_be_seen_first` is unresolved
- `information_loss_if_text_only` is unresolved

Proceed to final slide output only when the slide purpose and core content are sufficiently grounded.
