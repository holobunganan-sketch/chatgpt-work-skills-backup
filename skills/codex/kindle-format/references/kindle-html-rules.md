# Kindle HTML Rules

This reference defines the format contract for Kindle-first long-form HTML. It is optimized for reflowable reading on narrow e-ink screens and remains usable on larger Kindle devices and apps.

## 1. Core reading model

Design for a reader who can change font size, typeface, margins, line spacing, and orientation. The document therefore has no meaningful fixed page size.

Required properties:
- Reflowable text.
- Single-column reading order.
- Semantic hierarchy.
- Minimal CSS.
- Grayscale-safe meaning.
- No interaction dependency.

The source HTML should also remain structurally suitable for later EPUB packaging.

## 2. Document skeleton

Use this hierarchy:

```html
<h1>Chapter title</h1>
<h2>Major section</h2>
<h3>Subsection</h3>
<p>Continuous prose...</p>
```

Use H4 sparingly. Never choose a heading level for visual size alone.

Long documents should contain an internal contents block with anchor links. Do not simulate printed page numbers in the contents list.

## 3. Typography

Preferred baseline:

```css
body {
    margin: 0 5%;
    line-height: 1.5;
}

h1 { font-size: 1.6em; }
h2 { font-size: 1.3em; }
h3 { font-size: 1.12em; }

p {
    text-indent: 2em;
    margin: 0 0 0.6em;
}

.noindent { text-indent: 0; }
```

Rules:
- Use relative font sizes.
- Do not force a device-specific font.
- Do not encode layout using repeated non-breaking spaces.
- Keep emphasis semantic with `<strong>` and `<em>`.
- Avoid light-gray text and thin decorative rules that disappear on e-ink.

## 4. Paragraph behavior

Default long-form Chinese prose should read as a book chapter, with complete paragraphs and controlled first-line indentation.

Good uses of `.noindent`:
- first paragraph after a heading when desired;
- definition blocks;
- key-point callouts;
- figure captions;
- table notes;
- references.

Do not break a logically continuous explanation into many one-sentence paragraphs for visual rhythm.

## 5. Chapter breaks

Prefer:

```css
h1 {
    page-break-before: always;
    break-before: page;
}
```

Do not insert repeated `<br>` elements to manufacture pages.

Try to keep headings with at least the first lines of following content by using conservative break rules when supported, but do not over-engineer pagination because reflow is reader-controlled.

## 6. Layout restrictions

Do not use for the reading body:
- `position: fixed`;
- `position: sticky`;
- CSS Grid;
- CSS multi-column layout;
- fixed body/page widths in px;
- fixed body/page heights;
- horizontal scrolling as a normal reading mechanism;
- sidebars that sit beside the main text;
- dashboard cards as the primary information architecture;
- JavaScript-dependent content;
- hover-only tooltips or controls.

Flexbox is discouraged for content layout. A simple vertical document flow should solve almost every Kindle reading layout.

## 7. Callouts

Use callouts as lightweight reading aids, not as a card system.

Example:

```html
<aside class="keypoint">
  <p class="noindent"><strong>核心概念</strong></p>
  <p class="noindent">...</p>
</aside>
```

```css
.keypoint {
    border-left: 0.25em solid #555;
    padding-left: 0.8em;
    margin: 1em 0;
}
```

Use one dominant callout style unless the content requires a second semantic category such as “clinical caution.”

## 8. Images and scientific figures

Baseline:

```css
figure {
    margin: 1em 0;
}

img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 0 auto;
}

figcaption {
    font-size: 0.9em;
    text-indent: 0;
    margin-top: 0.4em;
}
```

Rules:
- Prefer portrait or near-square compositions for narrow screens.
- Use high contrast.
- Enlarge labels before export.
- Put important explanation in HTML prose or captions, not only inside the image.
- Provide meaningful `alt` text.
- Avoid legends that depend only on red/green/blue differences.
- For grayscale safety, combine color with direct labels, line patterns, shapes, symbols, or numbered annotations.
- Avoid screenshots of dense slide decks or spreadsheets.

For diagrams containing many labels, consider splitting one complex figure into sequential figures.

## 9. Tables

The narrow screen is the binding constraint.

Preferred forms:
1. Two-column “field / content” table.
2. Three-column comparison table.
3. Multiple smaller tables grouped by topic.
4. Stacked record blocks for highly dimensional evidence.

Avoid normalizing every dataset into a large matrix. A seven- or eight-column table may be technically representable yet functionally unreadable.

Example narrow table:

```html
<table>
  <thead>
    <tr><th>药物</th><th>机制</th><th>关键特点</th></tr>
  </thead>
  <tbody>
    <tr><td>A</td><td>...</td><td>...</td></tr>
  </tbody>
</table>
```

For an original wide evidence table, split by a stable comparison dimension such as efficacy, safety, population, or study design.

## 10. References and citations

For scientific and medical writing:
- keep citation markers in normal text flow;
- use concise superscript or bracketed numbering consistently;
- place full references in an end section;
- use internal anchors for endnotes when practical;
- keep DOI/URL strings from forcing horizontal overflow by allowing natural wrapping.

Avoid putting critical source details only in image footnotes.

## 11. Equations and symbols

Prefer Unicode and normal HTML text for simple equations and symbols. Keep mathematical expressions short enough to wrap naturally.

For complex equations that cannot reflow safely, use a high-contrast image or SVG with large labels and an adjacent text explanation. Do not make comprehension depend on zooming into a dense equation screenshot.

## 12. Internal navigation

For a long standalone HTML file, include:

```html
<nav class="toc" aria-label="目录">
  <h1>目录</h1>
  <ol>
    <li><a href="#ch1">第一章……</a>
      <ol>
        <li><a href="#ch1-s1">1.1 ……</a></li>
      </ol>
    </li>
  </ol>
</nav>
```

Keep the visible table of contents to one or two levels unless the document is unusually complex.

## 13. Links

Links must have meaningful anchor text. Do not use raw, extremely long URLs as the primary visible label when a source title is available.

External links are supplementary. The document must remain understandable offline.

## 14. CSS baseline

Recommended standalone CSS:

```css
html, body {
    padding: 0;
}

body {
    margin: 0 5%;
    line-height: 1.5;
    word-wrap: break-word;
}

h1 {
    font-size: 1.6em;
    margin: 0 0 1em;
    page-break-before: always;
    break-before: page;
}

h2 {
    font-size: 1.3em;
    margin: 1.4em 0 0.6em;
}

h3 {
    font-size: 1.12em;
    margin: 1.2em 0 0.5em;
}

p {
    text-indent: 2em;
    margin: 0 0 0.6em;
}

.noindent,
figcaption,
li,
th,
td {
    text-indent: 0;
}

figure {
    margin: 1em 0;
}

img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 0 auto;
}

figcaption {
    font-size: 0.9em;
    margin-top: 0.4em;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}

th,
td {
    border: 0.08em solid #666;
    padding: 0.35em;
    vertical-align: top;
}

blockquote,
.keypoint {
    margin: 1em 0;
    padding-left: 0.8em;
    border-left: 0.25em solid #555;
}

.toc ol {
    padding-left: 1.4em;
}
```

Adjust spacing to the manuscript, while preserving reflow and narrow-screen readability.

## 15. Content-shape rules

Formatting must not turn the manuscript into slide notes.

Use prose for:
- mechanisms;
- pathophysiology;
- causal reasoning;
- evidence interpretation;
- clinical explanation;
- historical or conceptual development.

Use lists for:
- genuinely enumerated criteria;
- step sequences;
- compact differential points;
- short takeaways after a fully developed explanation.

The reader should be able to learn by reading continuously without mentally reconstructing missing connective reasoning.

## 16. Final QA

Before delivery:
1. Open the HTML in a narrow browser viewport and verify linear reading order.
2. Increase browser text zoom substantially; content must reflow without clipping.
3. Check every figure in grayscale or mentally verify non-color coding.
4. Review every table over three columns and redesign unless preservation is required.
5. Confirm H1 → H2 → H3 hierarchy.
6. Confirm all images have useful alt text and captions when appropriate.
7. Run `scripts/validate_kindle_html.py`.
8. Fix all validator errors and review warnings.
