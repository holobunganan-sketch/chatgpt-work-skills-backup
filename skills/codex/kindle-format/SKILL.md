---
name: kindle-format
description: Use when writing, converting, or editing long-form HTML or EPUB-ready content intended for Kindle, Paperwhite, or Scribe reading, especially Chinese prose and medical/scientific documents with chapters, tables, figures, references, or internal navigation.
---

# Kindle Format

## Overview

Format long-form content as a **reflowable**, **single-column** reading document for Kindle-class e-ink screens. Preserve substantive depth and continuous prose while making the HTML resilient to user-controlled font size, margins, and device width.

## Output Contract

For Kindle-targeted HTML, produce content in this order:

1. Semantic HTML document structure and UTF-8 metadata.
2. Stable H1 → H2 → H3 hierarchy; use H4 only when the content genuinely needs it.
3. Continuous book-like paragraphs as the default; lists only when the information is inherently list-shaped.
4. Relative units for typography and spacing; never design around a fixed page width or height.
5. Responsive images, grayscale-safe information encoding, useful alt text, and HTML captions.
6. Tables optimized for narrow screens; prefer 2–3 columns or stacked record blocks.
7. Internal navigation for long documents and chapter-level page breaks.
8. Final validation with `scripts/validate_kindle_html.py` when an HTML file is produced.

## Required Format Rules

Use **semantic HTML** (`h1`–`h3`, `p`, `ul/ol`, `blockquote`, `figure`, `figcaption`, `table`) and a linear reading order.

Use **relative units** such as `em`, `rem`, and `%`. Let the Kindle reader control the final text size. Keep CSS simple and deterministic.

Do not use scripts, fixed/sticky UI, CSS Grid, multi-column CSS, dashboard/card layouts, hover-only meaning, or fixed page dimensions. Avoid Flexbox for reading layout; use it only when a tiny non-reading element cannot be expressed more simply.

For Chinese prose, default to `text-indent: 2em` with restrained paragraph spacing. Use `.noindent` for definitions, callouts, captions, and paragraphs immediately following headings when appropriate.

Treat color as optional decoration. Every scientific distinction must remain understandable in grayscale through labels, shapes, line patterns, symbols, or direct annotations.

## Tables and Images

A **table** with more than three columns is a redesign trigger. Split it by comparison dimension, convert each row into a stacked record, or create several narrow tables. Preserve a wide table only when the user explicitly requires the original structure, then document the compromise.

An **image** should normally fill most of the available text width, retain aspect ratio, avoid tiny embedded labels, and carry a separate HTML caption. Scientific figures must remain legible on a 6-inch monochrome screen.

## Workflow

When starting a Kindle-oriented writing task, read `references/kindle-html-rules.md`. Use `templates/kindle-reflowable.html` as the structural baseline when creating a new standalone HTML file.

After generating or modifying HTML, use the bundled **validator** to check the final file:

```bash
python scripts/validate_kindle_html.py path/to/document.html
```

Fix every ERROR. Review each WARN against the actual content. If an original >3-column table must be preserved, rerun with `--allow-wide-tables` and record that decision.

## Boundary

This skill controls presentation, reading order, and Kindle compatibility. It must not reduce substantive detail, convert explanatory prose into outline fragments, or simplify scientific reasoning merely to shorten the document.
