# Protected Elements in DOCX XML — Expanded Catalog

This reference expands the "do-not-touch" table in SKILL.md with recognition
heuristics, XPath markers, and "what breaks if you touch it" notes for each
protected-element family. Use this when an unfamiliar structure shows up in an
unpacked `word/document.xml` and you need to decide whether it is editable.

The general principle: **protected elements come first, editable plain-text
runs fill the gaps between them.** Run `extract_editable_runs.py` to get the
safe-zone map; consult this catalog only when something needs judgement.

## 1. Citation and cross-reference fields

### Recognition
```
<w:r>...<w:fldChar w:fldCharType="begin"/></w:r>
<w:r>...<w:instrText xml:space="preserve"> ADDIN ZOTERO_ITEM CSL_CITATION {...} </w:instrText></w:r>
<w:r>...<w:fldChar w:fldCharType="separate"/></w:r>
<w:r>...<w:rPr>...<w:vertAlign w:val="superscript"/>...</w:rPr><w:t>1</w:t></w:r>
<w:r>...<w:fldChar w:fldCharType="end"/></w:r>
```

Field codes from common reference managers:
- Zotero:           `ADDIN ZOTERO_ITEM CSL_CITATION {…json…}`
- Mendeley:         `ADDIN Mendeley{…}`
- EndNote:          `ADDIN EN.CITE{…}`
- Word's own:       `REF _Ref…`, `PAGEREF _Ref…`, `NOTEREF _Ref…`, `HYPERLINK…`

### What to protect
- The `<w:fldChar>` begin/separate/end tags — order and count must stay exact.
- The `<w:instrText>` content — the field instruction; do not delete or alter.
- The visible `<w:t>` between `separate` and `end` — this is the rendered
  citation number/text. Its superscript run-properties must remain.
- The position of the whole field block among surrounding plain-text runs —
  this is what places the citation number "after the sentence it modifies."

### What breaks if you touch it
- Word's "update field" / "update citations" reconstructs the visible text from
  the `instrText`; corrupting the begin/separate/end chain leaves a broken
  citation or a literal `ADDIN …` string visible.
- Moving the field across sentence boundaries changes which sentence the
  citation supports — a reputation/scholarly-integrity issue, not just cosmetic.
- Adjusting the citation text to match an edit you made to the surrounding
  sentence silently falsifies the citation-sentence correspondence.

## 2. Superscript citation/marker runs (visible marks)

### Recognition
Any `<w:r>` whose `<w:rPr>` carries `<w:vertAlign w:val="superscript"/>` and
contains a `<w:t>`. In `extract_editable_runs.py`, any `<w:t>` whose preceding
~15 lines contain the superscript marker is skipped.

### What to protect
- The text content (e.g., `1`, `3,4`, `6–8`, `11–15,18`).
- The run's position relative to the surrounding plain-text runs (post-sentence
  placement).
- The run properties (superscript formatting, font, size).

### What breaks
A citation/mark switched to a sibling sentence attaches to the wrong claim.

## 3. Bookmarks

### Recognition
```
<w:bookmarkStart w:id="3" w:name="_Ref654321"/>
... content ...
<w:bookmarkEnd w:id="3"/>
```

### What to protect
- The `w:id` (must stay stable and unique).
- The name (used by REF cross-references).
- The pairing of start and end IDs and their position around the target content.

### What breaks
Cross-references (REF, PAGEREF, NOTEREF) pointing at a bookmark resolve to wrong
text or stop working; "update field" produces Error or empty results.

## 4. Comments and review markup

### Recognition
```
<w:commentRangeStart w:id="N"/>
... text ...
<w:commentRangeEnd w:id="N"/>
<w:r>...<w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="N"/></w:r>
```
Plus `word/comments.xml` with `<w:comment w:id="N" w:author="…" w:date="…">…</w:comment>`.

### What to protect
- The comment IDs and their start/end pairing across `document.xml` and `comments.xml`.
- The author and date attributes (audit trail).
- The comment reference run position.

### What breaks
Comments detach from their text; reviewer attribution corrupts.

## 5. Tracked changes (revisions)

### Recognition
```
<w:ins  w:id="N" w:author="…" w:date="2026-07-28T00:00:00Z"> ...inserted run(s)... </w:ins>
<w:del  w:id="N" w:author="…" w:date="2026-07-28T00:00:00Z">
  <w:r><w:delText>...deleted text...</w:delText></w:r>
</w:del>
```
Also nested: `<w:pPr><w:rPr><w:del .../></w:rPr></w:pPr>` deletes a paragraph mark.

### What to protect
- The `<w:ins>` / `<w:del>` wrapper elements and the contained runs.
- Inside `<w:del>`, text is in `<w:delText>` (not `<w:t>`) — do not "fix" this.
- Author and date attributes (audit trail for legal/regulatory review).
- IDs (revision IDs are referenced by review UI and acceptance flows).

### What breaks
Accept/reject-change produces wrong final text; audit trail loses authorship;
"Track Changes" view corrupts. Also, if you edit the visible text inside a
tracked-change run, you change what was "originally deleted/inserted" — a
falsification of the review history.

## 6. Content controls (Structured Document Tags, SDT)

### Recognition
```
<w:sdt>
  <w:sdtPr>...binding, tag, type...</w:sdtPr>
  <w:sdtContent>
    ... <w:r>...<w:t>...</w:t></w:r> ...
  </w:sdtContent>
</w:sdt>
```
Plain-text/rich-text/checkbox/combo/dropdown/picture/date picker/map controls all
use this shape. A repeating-section SDT can wrap multiple paragraphs.

### What to protect
- The `<w:sdtPr>` block — contains the binding (`<w:dataBinding>`), tag, and type.
- The `<w:sdtContent>` boundary — bound content lives inside.

### What breaks
The control may be bound to a customXml part; editing the inner text manually
diverges from the binding and is silently overwritten on the next binding
refresh. Edit only if you understand the binding, or via Word's UI.

## 7. Equations and math

### Recognition
```
<m:oMathPara>
  <m:oMath>
    <m:r><m:t>x = ...</m:t></m:r>
    ...
  </m:oMath>
</m:oMathPara>
```
Inline math uses `<m:oMath>` directly inside a `<w:p>`; display math wraps in
`<m:oMathPara>`. Math runs use `<m:t>` (NOT `<w:t>`) for text — `extract_editable_runs.py`
explicitly skips them.

### What to protect
- The whole OfficeMath tree. Even small textual edits can corrupt the linear
  format and break Word's equation editor.

### What breaks
The equation renders broken or shows raw linear format; re-opening in Word's
equation editor may fail.

## 8. Custom XML parts

### Recognition
```
customXml/item1.xml, item2.xml, ...
customXml/itemProps1.xml, ...
```
Plus matching `<ds:datastoreItem>` / relationship entries.

### What to protect
- The parts themselves (Word may not even be able to parse them — `verify_edits.py`
  treats customXml parsing failures as non-blocking warnings for this reason).
- The relationships tying content controls to these parts.

### What breaks
SDT bindings lose their data; Information Rights Management or workflow metadata
may go missing; "Save as" operations produce inconsistent documents.

## 9. Drawings, pictures, shapes, charts

### Recognition
```
<w:drawing>
  <wp:inline> or <wp:anchor>
    <wp:extent cx=... cy=.../>
    <a:graphic><a:graphicData uri="...">
      <pic:pic>
        <pic:blipFill><a:blip r:embed="rIdN"/></pic:blipFill>
      </pic:pic>
    </a:graphicData></a:graphic>
  </wp:inline>
</w:drawing>
```
Charts: `<c:chart>` with `<c:externalData r:id="..."/>`. Charts live in
`word/charts/chartN.xml` separately.

### What to protect
- The `r:embed` / `r:id` relationship IDs — they point into `word/_rels/document.xml.rels`.
- The extent / positioning / wrapping settings.
- The relationship file: any rename must be consistent across both the consumer
  and the rels file.

### What breaks
Pictures or charts vanish, become "broken image" placeholders, or get the wrong
graphic on the next save.

## 10. Hyperlinks

### Recognition
```
<w:hyperlink r:id="rIdN" w:anchor="...">
  <w:r>...<w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr><w:t>...</w:t></w:r>
</w:hyperlink>
```
External hyperlinks use `r:id`; internal ones use `w:anchor` (targets a bookmark).

### What to protect
- The `r:id` and the matching row in `word/_rels/document.xml.rels`.
- The element structure (the wrapper splits runs).

### What breaks
External-link target URL drops; internal anchor breaks.

## 11. Section properties, page breaks, last-rendered-page-break

### Recognition
```
<w:sectPr> ... <w:pgSz>, <w:pgMar>, <w:cols>, <w:type w:val="..."/> ... </w:sectPr>
<w:lastRenderedPageBreak/>     — Word's cached page-break hint
<w:br w:type="page"/>          — explicit page break
```

### What to protect
- The `<w:sectPr>` blocks (per-section layout).
- The position of explicit page breaks inside paragraphs.
- `<w:lastRenderedPageBreak/>` (cosmetic but Word regenerates it; leave it be).

### What breaks
Pagination, headers/footers, or columns shift; numbering restarts unexpectedly.

## 12. Numbering, list definitions

### Recognition
```
numbering.xml: <w:num w:numId="N">...<w:abstractNumId w:val="M"/>...</w:num>
                <w:abstractNum w:abstractNumId="M"> ...level definitions... </w:abstractNum>
document.xml: <w:numPr><w:ilvl w:val="0"/><w:numId w:val="N"/></w:numPr>
```

### What to protect
- `w:numId`/`w:abstractNumId` references.
- `numId` numbering — used to auto-renumber list items.
- Level — `ilvl` controls nesting.

### What breaks
List numbering restarts, reorders, or collapses across paragraphs you didn't touch.

## 13. Styles

### Recognition
```
styles.xml: <w:style w:type="paragraph" w:styleId="Heading1">
document.xml: <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
```

### What to protect
- Style `w:styleId` references (don't rename a style by editing styles.xml without
  also renaming every consumer in document.xml — `verify_edits.py` catches this by
  verifying the per-paragraph style sequence is unchanged).
- The `w:val` attribute on `<w:pStyle>` / `<w:rStyle>` must match a style that exists.

### What breaks
Local formatting overrides silently swap; TOC entries vanish; navigation pane
reformats.

## Quick decision tree

When in front of a `<w:r>` you might want to edit:

1. Is it inside a `<w:fldChar>` begin/separate/end region? → NO, leave alone.
2. Does its `<w:rPr>` carry `<w:vertAlign w:val="superscript"/>`? → NO.
3. Is it inside `<w:sdt>` / `<m:oMath>` / `<w:ins>` / `<w:del>`? → NO (inside
   `<w:ins>` you may want to edit if accepting tracked changes is part of the
   task, but normal polish work leaves them intact).
4. Is its text `<w:instrText>` or `<w:delText>` rather than `<w:t>`? → NO.
5. Is its `<w:t>` immediately followed or preceded by a field-char sequence in
   the file? Even if safe-zone extraction marked it editable, double check the
   citation hasn't shifted. → Be conservative.

If you pass all five, the run is plain editable text.