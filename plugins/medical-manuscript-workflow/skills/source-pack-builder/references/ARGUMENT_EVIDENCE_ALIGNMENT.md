# Argument–Evidence Alignment

This file governs internal evidence work. Do not copy its fields, scores, or deliberation into the delivered Source Pack.

## 1. Lock the argument before placing sources

Write:

- the core question;
- the target answer;
- the shortest necessary sequence of mainline judgments;
- the function of each planned section.

Keep the mainline revisable. A source may reveal a missing step or a clearer comparison, but no source may create a side branch solely to justify its inclusion.

## 2. Read sources at claim level

For every source considered for substantive use, inspect:

1. the source's research question or purpose;
2. the population, setting, material, or object studied;
3. the design or method that determines what the result means;
4. the exact result or normative statement intended for use;
5. the comparison, direction, magnitude, condition, and outcome;
6. the authors' interpretation and any qualification that changes the usable proposition;
7. the exact page, section, table, figure, or paragraph location.

Titles, metadata, search snippets, secondary mentions, and topic similarity do not establish claim-level support. Abstract-only access permits background classification or a readiness gap. It does not permit detailed substantive use.

## 3. Extract the minimum usable proposition

Separate the source's own narrative from the planned document. Retain the smallest fact, relationship, comparison, definition, explanation, method, or recommendation that advances one mainline node.

Reject or restrict material that requires importing the source's unrelated problem statement, method narrative, or conclusion. Preserve source context that changes meaning.

## 4. Assign one evidence task

Use one primary task for each planned citation:

- `establish_fact`
- `quantify`
- `define`
- `explain`
- `compare`
- `distinguish`
- `bridge`
- `method`
- `counterpoint`
- `support_action`

Multiple sources may share one task. Synthesize their common contribution before assigning placement. Keep separate study-by-study treatment only when the differences themselves advance the current judgment.

## 5. Build the internal inference bridge

Record:

`preceding judgment → missing relation → source contribution → new local judgment → next mainline node`

The planned citation passes only when all five parts are specific.

Ask:

- What has the reader already accepted immediately before this citation?
- What exact relation or information is missing?
- What does this source add at claim level?
- What distinct judgment becomes justified after the source enters?
- How does that judgment continue toward the target answer?

If the downstream judgment simply repeats the source contribution, revise the placement or exclude the source.

## 6. Check contextual continuity

Evaluate internally:

- subject continuity;
- terminology continuity;
- tone continuity;
- abstraction-level continuity;
- sentence-function continuity.

Use `continuous`, `requires_adaptation`, or `incompatible`.

When adaptation is required, record a short instruction that restores the document's subject and vocabulary while preserving the supported proposition. Exclude an incompatible source from that placement.

## 7. Placement decisions

- `include`: closely read, exact proposition identified, mainline node and inference bridge complete.
- `move`: evidence is usable, but the proposed section or sentence position interrupts the current reasoning.
- `background_only`: useful for orientation, search expansion, or broad context; not approved for a detailed claim.
- `exclude`: no exact support, redundant, tangential, context-breaking, or unable to advance the mainline.

Theme relevance alone never produces `include`.

## 8. Delivery-layer conversion

The delivered Source Pack may contain:

- the supported claim or use;
- the final source classification;
- the chosen section or placement;
- any factual limitation needed for accurate drafting.

The delivered Source Pack must omit:

- mainline-fit scores;
- upstream and downstream reasoning fields;
- continuity checks;
- internal adaptation deliberation;
- source inclusion or exclusion rationale;
- descriptions of how the model evaluated the source.

Run `audit_source_pack_boundary.py` before delivery.

## 9. Evaluation cases

### Topic match without progression

A source discusses the same disease but reports a variable unrelated to the planned paragraph judgment. Classify it as `background_only` or `exclude`.

### Exact result with a broken entry point

A source supports the later implementation section, but placing it in the epidemiology paragraph changes the subject and interrupts the sequence. Classify the proposed use as `move` and place it at the implementation node.

### Abstract-only detailed claim

An abstract reports an association, while population definition and model adjustment are unavailable. Do not approve a detailed adjusted-effect claim. Record a readiness gap or use the source only for search expansion.

### Multiple sources with one task

Several studies quantify the same phenomenon. Build one shared quantitative judgment and attach the sources to that judgment. Avoid consecutive author-led summaries.
