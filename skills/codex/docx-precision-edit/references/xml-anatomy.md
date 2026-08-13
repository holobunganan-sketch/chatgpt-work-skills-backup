# DOCX XML Anatomy — Common Patterns on Sight

This reference maps common .docx content patterns to the XML you'll see after
unpacking with the `docx` skill's `unpack.py` (which pretty-prints one element
per line and merges adjacent same-format runs). Use this as a quick visual
glossary so that you can recognize each pattern on sight while editing.

All examples are simplified to their essential structure; real files have more
properties (`<w:rFonts>`, `<w:i>`, `<w:color>`, etc.) that you can ignore for
shape recognition.

## 1. A plain paragraph

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Normal"/>
    <w:spacing .../>
    <w:ind .../>
    <w:rPr>...</w:rPr>     <!-- paragraph-mark formatting; appears last in pPr -->
  </w:pPr>
  <w:r>
    <w:rPr>...font, size, color...</w:rPr>
    <w:t>Some plain text.</w:t>
  </w:r>
</w:p>
```

Element order inside `<w:pPr>` matters for schema validity:
`pStyle, numPr, spacing, ind, jc, rPr(last)`.

## 2. A heading paragraph

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading1"/>
  </w:pPr>
  <w:r>
    <w:t>1 Introduction</w:t>
  </w:r>
</w:p>
```

Heading styles drive the table of contents, the navigation pane, and the
chapter skeleton — never rename `w:val` without updating every consumer.

## 3. A paragraph with an inline citation field (Zotero)

```xml
<w:p>
  <w:pPr>...</w:pPr>

  <!-- Plain text run, ending at a sentence boundary -->
  <w:r><w:rPr>...</w:rPr><w:t>This is the cited claim.</w:t></w:r>

  <!-- Field begins -->
  <w:r><w:rPr>...</w:rPr><w:fldChar w:fldCharType="begin"/></w:r>
  <w:r><w:rPr>...</w:rPr><w:instrText xml:space="preserve"> ADDIN ZOTERO_ITEM CSL_CITATION {...} </w:instrText></w:r>
  <w:r><w:rPr>...</w:rPr><w:fldChar w:fldCharType="separate"/></w:r>

  <!-- Visible citation mark -->
  <w:r>
    <w:rPr>...<w:vertAlign w:val="superscript"/>...</w:rPr>
    <w:t>1</w:t>
  </w:r>

  <w:r><w:rPr>...</w:rPr><w:fldChar w:fldCharType="end"/></w:r>
  <!-- Field ends -->

  <!-- Text continuing after the citation -->
  <w:r><w:rPr>...</w:rPr><w:t xml:space="preserve"> Next sentence...</w:t></w:r>
</w:p>
```

Note the `xml:space="preserve"` on the trailing `<w:t>` — its leading space is
significant and must be preserved on edit. The unpack's run-merging will often
absorb the plain text into a single `<w:t>` between field blocks; that's the
unit `extract_editable_runs.py` lists.

## 4. A multi-citation field (grouped references)

```xml
<w:fldChar w:fldCharType="begin"/>
<w:instrText xml:space="preserve"> ADDIN ZOTERO_ITEM CSL_CITATION {"citationID":"...","citationItems":[{...},{...}]} </w:instrText>
<w:fldChar w:fldCharType="separate"/>
<w:r>
  <w:rPr><w:vertAlign w:val="superscript"/></w:rPr>
  <w:t>3,4</w:t>     <!-- or "6–8", "11–15,18" -->
</w:r>
<w:fldChar w:fldCharType="end"/>
```

A single field may render multiple numbers. The visible text is one run; do
not split it.

## 5. A cross-reference field (REF)

```xml
<w:fldChar w:fldCharType="begin"/>
<w:instrText> REF _Ref654321 \r \h </w:instrText>
<w:fldChar w:fldCharType="separate"/>
<w:r><w:t>3.2</w:t></w:r>
<w:fldChar w:fldCharType="end"/>
```

The visible text (`3.2`) is computed from the referenced bookmark's content at
field-update time. Editing it manually is a temporary overwrite.

## 6. A tracked-change insertion and deletion

```xml
<!-- Inserted -->
<w:ins w:id="7" w:author="Claude" w:date="2026-07-28T00:00:00Z">
  <w:r><w:t>new wording</w:t></w:r>
</w:ins>

<!-- Deleted (note: uses <w:delText>, not <w:t>) -->
<w:del w:id="8" w:author="Claude" w:date="2026-07-28T00:00:00Z">
  <w:r><w:delText>old wording</w:delText></w:r>
</w:del>
```

Minimal-edit pattern when changing one phrase inside a sentence:

```xml
<w:r><w:t>The term is </w:t></w:r>
<w:del w:id="1" w:author="..." w:date="..."><w:r><w:delText>30</w:delText></w:r></w:del>
<w:ins w:id="2" w:author="..." w:date="..."><w:r><w:t>60</w:t></w:r></w:ins>
<w:r><w:t> days.</w:t></w:r>
```

Inside `<w:del>`, use `<w:delText>` (not `<w:t>`) and `<w:delInstrText>` (not
`<w:instrText>`). When deleting an entire paragraph, also mark its paragraph
mark as deleted by adding `<w:del .../>` inside `<w:pPr><w:rPr>`.

## 7. A comment

```xml
<!-- In document.xml -->
<w:commentRangeStart w:id="0"/>
<w:r><w:t>text being commented</w:t></w:r>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>
```

```xml
<!-- In word/comments.xml -->
<w:comment w:id="0" w:author="Claude" w:date="2026-07-28T00:00:00Z" w:initials="C">
  <w:p>...comment body...</w:p>
</w:comment>
```

Comment markers are siblings of `<w:r>`, never inside it. Replies nest range
markers inside a parent's range and add another `<w:commentReference>`.

## 8. A content control (SDT)

```xml
<w:sdt>
  <w:sdtPr>
    <w:alias w:val="Date"/>
    <w:tag w:val="dateField"/>
    <w:id w:val="12345"/>
    <w:date w:fullDate="2026-07-28T00:00:00Z"/>
    <w:dataBinding w:prefixMappings="..." w:storeItemID="..." w:xpath="..."/>
    <w:text/>
  </w:sdtPr>
  <w:sdtContent>
    <w:p>
      <w:r><w:t>2026-07-28</w:t></w:r>
    </w:p>
  </w:sdtContent>
</w:sdt>
```

If you see a `<w:dataBinding>`, the inner text is sourced from a customXml
part. Editing the inner text manually will be reverted on the next binding
refresh — edit through Word or by changing the bound customXml part instead.

## 9. A display equation

```xml
<w:p>
  <w:pPr><w:pStyle w:val="Equation"/></w:pPr>
  <m:oMathPara>
    <m:oMath>
      <m:r><m:t>x = </m:t></m:r>
      <m:f>
        <m:num><m:r><m:t>a</m:t></m:r></m:num>
        <m:den><m:r><m:t>b</m:t></m:r></m:den>
      </m:f>
    </m:oMath>
  </m:oMathPara>
</w:p>
```

Math text is in `<m:t>` (NOT `<w:t>`). The whole `<m:oMath>` / `<m:oMathPara>`
tree is the unit; do not fragment it. `extract_editable_runs.py` skips math
runs entirely.

## 10. An inline picture

```xml
<w:r>
  <w:drawing>
    <wp:inline distT="0" distB="0" distL="0" distR="0">
      <wp:extent cx="914400" cy="457200"/>
      <a:graphic>
        <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
          <pic:pic xmlns:pic="...">
            <pic:blipFill><a:blip r:embed="rId5"/></pic:blipFill>
            <pic:spPr>...</pic:spPr>
          </pic:pic>
        </a:graphicData>
      </a:graphic>
    </wp:inline>
  </w:drawing>
</w:r>
```

`r:embed="rId5"` resolves via `word/_rels/document.xml.rels` to a media file in
`word/media/`. The rels file and the media file together are the picture; keep
all three consistent.

## 11. A section break

```xml
<w:p>
  <w:pPr>
    <w:sectPr>
      <w:type w:val="nextPage"/>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
      <w:cols w:space="720"/>
    </w:sectPr>
  </w:pPr>
</w:p>
```

The last section's properties live directly inside `<w:body>` as the trailing
`<w:sectPr>`. Moving or removing these silently shifts the document's page
layout.

## 12. A numbered list paragraph

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="ListParagraph"/>
    <w:numPr>
      <w:ilvl w:val="0"/>
      <w:numId w:val="3"/>
    </w:numPr>
    <w:ind w:left="720" w:hanging="360"/>
  </w:pPr>
  <w:r><w:t>First item</w:t></w:r>
</w:p>
```

The numbering comes from `numbering.xml` via the `numId`. Never use Unicode
bullet characters (`•`, `\u2022`) in plain text to fake a list — the schema
provides `<w:numPr>` for that.

## 13. Run with significant leading/trailing space

```xml
<w:t xml:space="preserve"> Next sentence...</w:t>
```

The `xml:space="preserve"` attribute tells XML parsers to keep leading and
trailing whitespace. When editing such a run, preserve the surrounding spaces
in your `old`/`new` strings; the `unpack.py` auto-repair will add the attribute
back on repack if needed, but mismatching the spaces themselves will shift the
text. `verify_edits.py` will surface this as a paragraph-text diff.

## How to read an unfamiliar element

1. Note the namespace prefix: `w:` = WordprocessingML (main body), `m:` = math,
   `wp:` = drawing positioning, `a:` = drawing, `pic:` = picture, `r:` = relationships,
   `c:` = chart, `dc:` = Dublin Core metadata.
2. Look at the enclosing element: is it inside `<w:fldChar>` regions? `<w:sdt>`?
   `<m:oMath>`? `<w:ins>`/`<w:del>`? If so, treat as protected.
3. Look at the run properties `<w:rPr>`: superscript `vertAlign` = citation mark.
4. If you reach a `<w:t>` with none of the above protections and not inside a
   field, it's editable plain text — that's the unit `extract_editable_runs.py`
   hands you.