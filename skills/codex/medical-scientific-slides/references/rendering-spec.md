# Rendering Spec

Use this reference when turning structured slide definitions into actual slide pages, HTML/CSS, PPTX-ready content, or other renderable formats.

## Engineering Preference

Build slides as `structured content -> template selection -> rendering`, not as ad hoc free-form design.

For each slide, keep a stable object with at least:

- `slide_type`
- `slide_title`
- `core_message`
- `content_blocks`
- `chart_or_svg_need`
- `citation_need`
- `layout_pattern`

Add optional fields only when needed, such as:

- `key_numbers`
- `footer_note`
- `source_lines`
- `speaker_note`
- `brand_override`

## Template Reuse

Reuse templates across slides of the same type whenever possible. Avoid inventing a new layout for every page.

Recommended repeatable slide types:

- `executive-summary`
- `evidence-summary`
- `chart-plus-conclusion`
- `comparison-matrix`
- `timeline`
- `mechanism-diagram`
- `process-flow`
- `three-card-framework`
- `two-column-argument`

## Design Tokens

Maintain stable design tokens across the deck.

### Color variables

- `--bg: #FFFFFF`
- `--text: #1F1F1F`
- `--muted: #6B7280`
- `--line: #D9DDE3`
- `--accent: #B31F2A`
- `--soft: #F5F6F8`

If the user provides brand colors, replace tokens consistently rather than page by page.

### Type scale

- `--title-size: 34px`
- `--subtitle-size: 24px`
- `--body-size: 18px`
- `--note-size: 12px`

### Spacing scale

- `--page-padding: 40px`
- `--block-gap: 20px`
- `--section-gap: 28px`
- `--card-padding: 18px`

### Shape rules

- card radius: `12px`
- line weight: `1.5px` to `2px`
- avoid heavy shadows
- use borders and soft fills before shadows

## CSS vs SVG

Prefer CSS for:

- layout grids
- text blocks
- cards
- tables
- summary metrics
- citation rows

Prefer SVG for:

- pathways
- networked logic
- multi-step mechanisms
- explanatory structures with arrows or connectors

Do not use SVG as decoration. Every graphic should help communicate the conclusion.

## Citation Area

Reserve a citation band or source line on evidence-based slides. Keep it visually quiet but readable.

When sources are missing, display:

`Source pending`

Do not invent placeholder journals, years, author names, or URLs.

## Fallback Rule

When the input is too weak for a complex visual:

1. reduce the number of modules
2. switch to a simpler layout
3. preserve the conclusion
4. keep the slide formal and readable

Clarity beats visual ambition.
