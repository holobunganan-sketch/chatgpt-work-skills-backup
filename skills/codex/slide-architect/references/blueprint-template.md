# Slide blueprint template (copy-ready)

Use this structure when the user wants production-ready slide-by-slide output. Keep it concise.

## Deck spec (once)

- Ratio: `16:9` (default unless specified)
- Font: `微软雅黑` (default unless specified)
- Palette: user-provided; if missing after asking once: `white + red accent + dark gray + light gray`
- Footers: logo/brand/page number (only if requested)
- Sources: required when claims use medical/research/policy/market evidence

## Per-slide spec (repeat)

Slide `N` / `Title (结论式)`

- **Takeaway**: 1 sentence (what you want the audience to remember)
- **Layout**: choose from `A/B/C/D/E` (see `layout-patterns.md`)
- **Modules (2–4)**:
  - `Module 1 heading`: 2–3 bullets (short, parallel)
  - `Module 2 heading`: 2–3 bullets
  - (optional) `Module 3/4 heading`: 1–2 bullets
- **Visual** (one):
  - Type: `bar` / `comparison` / `flow` / `structure` / `table` / `none`
  - Data needed: list what must be provided (do not invent)
  - Build: `CSS` (simple) or `SVG` (complex)
  - Highlight: what uses the accent color (keywords / key number / key arrow)
- **Copy edits**:
  - Replace long sentences with short points
  - Convert description → claim
  - Apply parallel structure (并列/递进/对比/因果)
- **Sources footer**:
  - If provided: list (机构/论文/报告/链接/年份)
  - If missing: `来源待补充（请提供：…）`

## Optional bilingual rule

If bilingual is requested:
- Prefer: Chinese title + English subtitle, or
- Provide 2 versions of the deck (CN and EN) rather than mixing dense bilingual paragraphs.

