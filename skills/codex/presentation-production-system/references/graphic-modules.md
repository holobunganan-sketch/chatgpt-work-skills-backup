# Graphic Modules Handbook

## Purpose

Define reusable visual grammars for SVG-capable or geometry-heavy slide regions.

## Use Rule

Select a graphic module only after the page type is fixed. A module supports the page; it does not replace page logic.
Treat SVG as one of the preferred rendering systems for the main graphic zone when geometry carries meaning.

## SVG Boundary Rule

Place only geometry-sensitive content in SVG by default:

- nodes
- arrows
- bands
- lines
- connectors
- stage blocks
- short labels
- icon clusters

Keep these outside SVG unless explicitly required:

- slide title
- long explanation
- literature references
- speaker notes
- paragraph text
- large conclusion box

## Rendering Role

Use SVG first when the page value depends on:

- exact alignment
- arrow logic
- node spacing
- grouped region boundaries
- layered positioning
- network density
- route convergence

## Modules

### 1. Left-Right Comparison Grid

- Applicable scenarios: binary comparison with aligned criteria
- Not applicable: more than two options, loose narrative pages
- Required inputs: left entity, right entity, shared criteria
- Optional inputs: superiority markers, neutral middle divider
- Default output: mirrored grid, row labels, compact callout strip
- Common misuse: placing unrelated criteria on each side

### 2. Multi-Stage Flow

- Applicable scenarios: sequential steps, patient flow, pipeline, lifecycle, workflow
- Not applicable: branching networks or hierarchy maps
- Required inputs: ordered stages, direction
- Optional inputs: stage owners, sublabels, gates
- Default output: connected steps with arrow rhythm
- Common misuse: forcing too many branches into a linear strip

### 3. Central Radial Map

- Applicable scenarios: central thesis with surrounding themes, stakeholders, outcomes
- Not applicable: chronology or strict layered dependencies
- Required inputs: center node, outer nodes
- Optional inputs: node clusters, emphasis weighting
- Default output: one center, balanced satellites, short labels
- Common misuse: overcrowding outer ring

### 4. Layered Relationship Map

- Applicable scenarios: multi-layer systems, upstream-downstream relationships, ecosystem views
- Not applicable: simple two-step processes
- Required inputs: layer names, nodes per layer, key links
- Optional inputs: grouping bands, interaction legends
- Default output: layered rows or columns with clean linking
- Common misuse: mixing too many cross-layer arrow types

### 5. Card-Based Infographic Set

- Applicable scenarios: pillars, features, principles, workstreams, outcome groups
- Not applicable: detailed mechanism or chronology
- Required inputs: card titles, short descriptors
- Optional inputs: icons, priority markers
- Default output: 3-6 cards with consistent rhythm
- Common misuse: long paragraphs inside cards

### 6. Timeline Strip

- Applicable scenarios: time-ordered milestones
- Not applicable: cyclical loops or relationship maps
- Required inputs: time points, milestone labels
- Optional inputs: categories, current-state marker
- Default output: horizontal or vertical line with anchored events
- Common misuse: over-labeling minor events

### 7. Logic Tree

- Applicable scenarios: decomposition, issue trees, criteria trees, cause trees
- Not applicable: linear process explanation
- Required inputs: root statement, branches
- Optional inputs: branch evidence tags
- Default output: root-to-branch hierarchy
- Common misuse: mixing tree logic with process arrows

### 8. Roadmap Lane

- Applicable scenarios: phased initiatives across streams or work packages
- Not applicable: historical retrospective or static comparison
- Required inputs: phases, workstreams
- Optional inputs: dependencies, owners, risks
- Default output: lane-based phased roadmap
- Common misuse: too many simultaneous lanes without prioritization

### 9. Organizational Map

- Applicable scenarios: hierarchy, governance, stakeholder structure
- Not applicable: mechanism chains or timelines
- Required inputs: entities, relationship type
- Optional inputs: group colors, role tags
- Default output: boxes plus connectors
- Common misuse: encoding non-hierarchical relationships as org charts

### 10. Pathway Chain

- Applicable scenarios: mechanism steps, causal chain, activation-to-outcome logic
- Not applicable: unordered association diagrams
- Required inputs: ordered nodes, directional transitions
- Optional inputs: inhibitors, accelerators, evidence tags
- Default output: segmented directional chain with checkpoints
- Common misuse: adding paragraph-level explanations inside nodes

### 11. Quadrant Matrix

- Applicable scenarios: option positioning, segmentation, prioritization
- Not applicable: exact quantitative analytics without valid scales
- Required inputs: axis meanings, item set
- Optional inputs: emphasis zones, recommendation highlight
- Default output: 2x2 field with clear axes
- Common misuse: fake precision with arbitrary coordinates

### 12. Conclusion Integration Frame

- Applicable scenarios: many inputs converging into one decision or synthesis
- Not applicable: opening context slide
- Required inputs: supporting blocks, integrated conclusion
- Optional inputs: evidence weights, source grouping
- Default output: grouped input modules feeding one close
- Common misuse: showing inputs without the integrating conclusion

### 13. Upstream-Midstream-Downstream Chain

- Applicable scenarios: handoff structure, dependency transfer, chain-of-custody, system transfer logic
- Not applicable: radial, hierarchy, or full network pages
- Required inputs: upstream, midstream, downstream groups
- Optional inputs: transfer conditions, breakpoints, output notes
- Default output: three-zone directional chain
- Common misuse: turning the three-zone chain into a decorative timeline

### 14. Layer Stack

- Applicable scenarios: layered systems, architecture stacks, ecosystem tiers
- Not applicable: single-path or bilateral comparisons
- Required inputs: layer names, nodes per layer
- Optional inputs: cross-layer links, grouping shells
- Default output: stacked or banded layer map
- Common misuse: overfilling layers with paragraph text

### 15. Network Constellation

- Applicable scenarios: relationship networks, stakeholder constellations, scientific interaction maps
- Not applicable: strict hierarchy or step-by-step pathways
- Required inputs: nodes, connection types
- Optional inputs: cluster groups, edge emphasis
- Default output: cluster-aware network field
- Common misuse: drawing all edges with equal weight

### 16. Route Convergence Map

- Applicable scenarios: many streams converge into one outcome, one decision, one synthesized conclusion
- Not applicable: single chain pages with no merge behavior
- Required inputs: streams, merge points, outcome node
- Optional inputs: gates, blockers, milestones
- Default output: converging route system
- Common misuse: replacing convergence with stacked bullets

## Module Selection Heuristics

Use these shortcuts:

- sequence -> Multi-Stage Flow or Pathway Chain
- one center, many satellites -> Central Radial Map
- hierarchy or decomposition -> Logic Tree or Organizational Map
- compare two things -> Left-Right Comparison Grid
- multiple evidence blocks to one claim -> Conclusion Integration Frame
- time -> Timeline Strip
- strategic plan across streams -> Roadmap Lane
- three transfer zones -> Upstream-Midstream-Downstream Chain
- layered system -> Layer Stack
- network or ecosystem -> Network Constellation
- many streams to one endpoint -> Route Convergence Map

## Complexity Downgrade Rule

When a requested graphic is too complex:

1. preserve the relationship logic
2. reduce decorative layers
3. reduce labels to short phrases
4. move explanations to native PPT sidebars
5. deliver the module plan before drawing full SVG
