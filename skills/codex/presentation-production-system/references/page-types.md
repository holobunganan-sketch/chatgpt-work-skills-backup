# Page Type Handbook

## Purpose

Provide a reusable catalog of argument-page types. Select a page type before writing content or designing visuals.

## Selection Rule

Choose the simplest page type that can carry the slide's single message with the strongest visual reasoning. Prefer graphic-led pages over generic section pages when relation, direction, hierarchy, or comparison carries meaning.

## Routing Priority

Use this order:

1. graphic proposition page
2. graphic-plus-text page
3. data/evidence page
4. minimal text page

Do not let minimal text pages become the deck's dominant page class.

## Page Types

### 1. Center Radial Page

- Applicable scenarios: one center concept with surrounding drivers, pillars, outcomes, actors, or implications
- Not applicable: strict chronology, strict hierarchy, dense evidence tables
- Required inputs: center thesis, surrounding nodes
- Optional inputs: grouping, emphasis hierarchy, directional hints
- Default output: dominant central visual with short outer labels and minimal supporting text
- Visual center definition: the center node and first-ring relationship pattern
- SVG usage scope: center node, outer nodes, connectors, group bands
- PPT native retention: title, short subtitle, takeaway, references
- Text density cap: low
- Common misuse: forcing process logic into a radial map

### 2. Left-Right Comparison Mechanism Page

- Applicable scenarios: compare states, options, pathways, interventions, structures, or mechanisms side by side
- Not applicable: three-way comparison or loose narrative contrast
- Required inputs: two comparable entities, comparison dimensions
- Optional inputs: highlight criteria, implication note
- Default output: mirrored visual fields with aligned comparison logic
- Visual center definition: the contrast axis between left and right structures
- SVG usage scope: mirrored structures, alignment guides, arrows, labels
- PPT native retention: title, short implication strip, references
- Text density cap: low to medium
- Common misuse: filling both sides with paragraphs instead of comparable structures

### 3. Multi-Stage Path Page

- Applicable scenarios: mechanisms, journeys, lifecycle logic, causal chain, phased transformation
- Not applicable: unordered network maps
- Required inputs: ordered stages, directional logic
- Optional inputs: checkpoints, interventions, blockers, accelerators
- Default output: dominant path visual with short stage labels and a compact conclusion
- Visual center definition: the directional stage chain
- SVG usage scope: nodes, arrows, stage containers, blockers/enablers
- PPT native retention: title, short stage notes, takeaway, references
- Text density cap: low
- Common misuse: collapsing the path into bullets

### 4. Upstream-Midstream-Downstream Chain Page

- Applicable scenarios: supply chain, pathway cascade, workflow dependency, system transfer, handoff structure
- Not applicable: center-radial or pure hierarchy content
- Required inputs: upstream, midstream, downstream entities or stages
- Optional inputs: transfer conditions, failure points, outputs
- Default output: directional three-zone chain with explicit handoffs
- Visual center definition: transfer logic across the three zones
- SVG usage scope: zone bands, node groups, directional arrows
- PPT native retention: title, short annotations, conclusion strip
- Text density cap: low
- Common misuse: treating the chain like a simple timeline when dependency matters more than time

### 5. Layered Structure Page

- Applicable scenarios: multi-layer systems, architecture, stacked dependencies, ecosystem levels
- Not applicable: strict chronology or two-way comparison
- Required inputs: layer names, elements per layer
- Optional inputs: cross-layer relationships, grouping bands
- Default output: layered map with explicit level separation
- Visual center definition: the layered stack and the meaning of level position
- SVG usage scope: layer bands, nodes, connectors, group shells
- PPT native retention: title, side note, takeaway, references
- Text density cap: low to medium
- Common misuse: overusing crossing arrows until layers lose readability

### 6. Comprehensive Map Page

- Applicable scenarios: synthesize multiple relationships, evidence blocks, actors, or pathways into one integrated page
- Not applicable: simple single-chain pages
- Required inputs: node groups, integration logic
- Optional inputs: category colors, evidence grouping, convergence logic
- Default output: one integrated visual map with a dominant reading path
- Visual center definition: the convergence or network pattern that carries the meaning
- SVG usage scope: grouped nodes, links, convergence paths, region bands
- PPT native retention: title, short reading guide, takeaway, references
- Text density cap: medium
- Common misuse: adding every fact until the map becomes unreadable

### 7. Logic Tree Page

- Applicable scenarios: decomposition, issue trees, criteria trees, decision trees, causal branching
- Not applicable: network maps or path pages
- Required inputs: root node, branches
- Optional inputs: branch labels, evidence tags, priority markers
- Default output: root-to-branch tree with explicit branch logic
- Visual center definition: the root claim and branch decomposition
- SVG usage scope: nodes, branch connectors, grouping brackets
- PPT native retention: title, short interpretation strip, references
- Text density cap: low to medium
- Common misuse: mixing tree logic with timeline or process arrows

### 8. Network Relationship Page

- Applicable scenarios: stakeholder maps, interaction maps, scientific networks, ecosystem relationships
- Not applicable: strict hierarchy or simple path
- Required inputs: nodes, relationship types
- Optional inputs: cluster grouping, edge weighting, node emphasis
- Default output: network map with one clear center of interpretation
- Visual center definition: the dominant cluster or focal node pattern
- SVG usage scope: nodes, edges, cluster boundaries, emphasis rings
- PPT native retention: title, short legend, takeaway, references
- Text density cap: low
- Common misuse: drawing every possible connection without prioritization

### 9. Route Convergence Page

- Applicable scenarios: show many inputs, paths, or workstreams converging into one outcome or decision
- Not applicable: pages without visible convergence logic
- Required inputs: input streams, convergence node, outcome
- Optional inputs: gate conditions, blockers, priorities
- Default output: converging route map with one end-state
- Visual center definition: the convergence point and its incoming routes
- SVG usage scope: route lines, lane groups, merge points, blockers
- PPT native retention: title, takeaway, short note, references
- Text density cap: low
- Common misuse: reducing convergence into a bullet summary

### 10. Conclusion Integration Diagram Page

- Applicable scenarios: multiple evidence items or causes feed one conclusion
- Not applicable: single-source result pages
- Required inputs: evidence clusters, integrated conclusion
- Optional inputs: evidence weighting, source labels
- Default output: structured convergence diagram toward one conclusion block
- Visual center definition: the integrated conclusion and its feed-in structure
- SVG usage scope: evidence blocks, connectors, convergence arrows
- PPT native retention: title, evidence notes, references
- Text density cap: medium
- Common misuse: listing evidence without visual synthesis

### 11. Data Support Page

- Applicable scenarios: charts, metric evidence, benchmark data, trend analysis
- Not applicable: conceptual explanation without actual data
- Required inputs: chart title, metric, values or source table
- Optional inputs: benchmark line, highlight point
- Default output: chart plus claim-led takeaway plus source
- Visual center definition: the chart pattern or comparative evidence field
- SVG usage scope: custom chart grammars only when native charting is insufficient
- PPT native retention: title, takeaway, source, interpretation strip
- Text density cap: medium
- Common misuse: forcing concept pages into bar charts

### 12. Cover Or Bridge Page

- Applicable scenarios: opening, chapter transition, limited summary, constrained supporting note
- Not applicable: pages whose meaning depends on relation, mechanism, comparison, hierarchy, or network structure
- Required inputs: page claim, context, transition purpose
- Optional inputs: subtitle, event, speaker, confidentiality
- Default output: minimal text-led support page
- Visual center definition: one dominant title or one restrained transition visual
- SVG usage scope: optional motif only
- PPT native retention: almost all visible content
- Text density cap: medium
- Common misuse: letting cover/bridge/support pages dominate the deck

## Custom Page Type Rule

Create a new page type only when:

1. no existing type matches the slide job
2. the new type has a repeatable use case
3. the new type can be documented with inputs, outputs, and misuse cases

Document it in `development-guide.md` before routine use.
