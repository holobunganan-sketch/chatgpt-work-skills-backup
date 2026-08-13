# Workflow Core

## Purpose

Define the ordered production flow from user input to slide-ready artifacts. Execute steps in order. Do not skip to rendering or bypass blueprint gating.

## Step 1: Parse The Brief

Extract the following fields:

- topic
- desired outcome
- audience
- use scenario
- source materials available
- deck scope
- deadline or speed preference
- style preference

If any field is absent, mark it as unknown instead of guessing.

## Step 2: Determine The Core Message

Reduce the request to one sentence:

`This presentation must make the audience understand, believe, decide, or remember _____.`

This sentence governs all later routing.

## Step 3: Determine The Argument Medium

For each candidate page, answer these questions before building the page:

- What cognition must this page advance?
- What must be seen before it is read?
- Would text-only treatment cause material information loss?
- Is the page value primarily in spatial, directional, layered, comparative, or network logic?

If graphic treatment carries the meaning better than text, route the page to a graphic-led page type first.

## Step 4: Build The Narrative Spine

Choose the simplest viable progression:

- context -> problem -> explanation -> evidence -> implication -> action
- background -> gap -> solution -> mechanism -> value -> next step
- situation -> analysis -> options -> recommendation
- chapter sequence for long educational decks

Do not create a slide list before the narrative spine exists. Do not assume the narrative spine requires agenda, executive summary, roadmap, or closing-ask pages unless the user explicitly wants that rhetoric.

## Step 5: Estimate Information Density

Classify each major section as:

- low density
- medium density
- high density

Use density to choose page types and graphic modules. High-density sections usually require structured diagrams, comparison layouts, layered maps, or multi-zone pages instead of paragraphs.

## Step 6: Create The Slide Inventory

For each slide, define:

- slide number
- slide role in deck
- narrative function
- page type candidate
- evidence requirement
- whether it is graphic-led, graphic-plus-text, data-led, or minimally text-led

## Step 7: Route Each Slide

For each slide, answer in order:

1. What is the single point of this slide?
2. What must be seen first?
3. What information would be lost if this stayed text-only?
4. Is this a graphic proposition page, a graphic-plus-text page, a data page, or a minimal text page?
5. What page type best expresses that point?
6. What part must remain editable in native PPT?
7. Does the main visual require SVG?
8. Which graphic module fits the slide?
9. What content should not appear on this slide?

Apply routing priority in this order:

1. graphic proposition page
2. graphic-plus-text page
3. data/evidence page
4. minimal text or chapter page

## Step 8: Draft The Page Blueprint

Create a blueprint before final drafting. Use the required schema in `page-blueprint-v2.md`.

Minimum blueprint fields:

- `page_id`
- `page_role`
- `narrative_function`
- `page_type`
- `visual_center`
- `graphic_priority`
- `svg_needed`
- `svg_module_candidate`
- `text_density`
- `ppt_native_blocks`
- `chart_or_diagram_goal`
- `key_message`
- `what_must_be_seen_first`
- `what_should_remain_outside_svg`
- `generic_consulting_layout_forbidden`
- `reuse_candidate_module`
- `information_loss_if_text_only`
- `deck_position`
- `style_keywords`
- `avoid_list`
- `open_questions`

Do not continue if `what_must_be_seen_first` or `information_loss_if_text_only` is empty.

## Step 9: Decide Rendering Strategy

Use this order:

### Graphic-Led First

Choose when the slide mainly contains:

- mechanism logic
- directional chain
- hierarchy
- system composition
- role boundary
- layered structure
- relationship map
- comparison geometry
- decision logic

Use SVG for the main zone unless a native PPT diagram is clearly simpler and equally expressive.

### Graphic + Text Hybrid

Choose when the slide combines:

- one dominant visual
- one short explanation strip
- one takeaway or evidence strip outside the visual

This is the default for mechanism, flow, relationship, framework, layered, and system pages.

### Data-Led Page

Choose when numeric evidence drives the slide.

Keep chart titles, takeaways, and notes in PPT-native layers. Use SVG only if a custom chart grammar is necessary.

### Minimal Text Page

Choose only for:

- cover
- chapter bridge
- limited summary
- constrained supporting explanation

Do not let this become the dominant page class in the deck.

## Step 10: Draft Final Slide Output

Only after blueprint approval or sufficient confidence:

- write a claim-led title
- define the visual center
- define the main-zone diagram task
- write only the minimum supporting text outside the visual
- define callouts and conclusions
- keep the main visual responsible for the page's meaning

## Step 11: Self-Check

Verify:

1. Does each slide have one primary message?
2. Is the page a visual reasoning unit rather than a generic section page?
3. Does the chosen page type match that message?
4. Has long copy been kept out of SVG?
5. Is the main visual the first thing the audience should see?
6. Is the visual system consistent with adjacent slides?
7. Are uncertain facts marked without taking over the page?
8. Is the slide maintainable by a non-designer?

## Output Preference Ladder

Prefer the most stable artifact:

1. deck storyline
2. graphic-led slide inventory
3. page blueprints
4. final slide spec
5. direct slide content

When in doubt, move one level up this ladder instead of forcing a finished slide.
