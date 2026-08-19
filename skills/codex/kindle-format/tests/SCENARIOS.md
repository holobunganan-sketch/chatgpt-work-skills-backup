# Kindle Format behavior scenarios

These scenarios test whether an agent applies the skill rather than merely mentioning it.

## Scenario 1 — Long medical chapter
Prompt: “Write a 12,000-word Chinese medical chapter as HTML for Kindle Paperwhite reading, with definitions, mechanisms, one pathway figure, and several comparison tables.”
Expected behavior:
- Uses reflowable, single-column semantic HTML.
- Keeps prose continuous and book-like; headings form a stable H1→H2→H3 hierarchy.
- Uses relative units; no fixed page dimensions.
- Converts wide comparisons into 2–3-column tables or stacked sections.
- Uses high-contrast, width-responsive figures with text alternatives/captions.
- Provides or runs the validator when a final HTML file is produced.

## Scenario 2 — User supplies web-style HTML
Prompt: “Convert this dashboard-like HTML into something comfortable on Kindle.”
Expected behavior:
- Removes navigation rails, cards-as-layout, grid/flex multi-column structure, sticky/fixed elements, scripts, hover-only meaning, and decorative effects.
- Preserves information hierarchy and reading order.
- Rewrites content into a linear book flow.

## Scenario 3 — Color-dependent scientific figure
Prompt: “Embed this red-vs-green mechanism diagram in the Kindle document.”
Expected behavior:
- Requires grayscale-safe differentiation through labels, line patterns, shapes, or annotations.
- Uses a legible figure width and separate HTML caption.

## Scenario 4 — Wide evidence table
Prompt: “Keep this 8-column evidence table in the chapter.”
Expected behavior:
- Does not blindly retain the 8-column layout.
- Splits it into smaller tables or record-style blocks unless the user explicitly requires the original table.
