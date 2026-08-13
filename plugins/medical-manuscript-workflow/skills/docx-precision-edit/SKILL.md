---
name: docx-precision-edit
description: Use when making localized language, terminology, phrasing, or logic edits to a finalized DOCX whose structure is complete and whose Zotero or EndNote fields, cross-references, bookmarks, comments, tracked changes, content controls, equations, custom XML, or other protected elements must remain intact; also use for progressive, auditable edit rounds with rollback. Do not use for document creation, section restructuring, wholesale rewrites, or plain text without embedded protected structures.
---

# Docx Precision Edit

## Overview

Perform **high-fidelity localized edits** to a finalized .docx without disturbing its embedded "protected elements." Edits are confined to plain-text runs; citation fields, superscript cross-references, bookmarks, comments, content controls, equation objects, and other machine-managed XML are left byte-identical. Each round runs on a copy, is script-driven with uniqueness assertions, and is independently verified before delivery — making the edit a provably side-effect-free engineering operation rather than a freehand polish.

## When to Use

Trigger this skill when ALL of the following hold:

1. The .docx content and structure are already complete; only localized changes are wanted (language polishing, terminology unification, phrasing rewrites, or logic fixes that may rewrite several linked sentences but do not alter the section skeleton).
2. The document contains embedded protected elements whose integrity must be preserved (citation fields, superscript cross-references, bookmarks, comments, tracked changes, content controls, equation objects, custom XML, variable placeholders, etc.).
3. The work may need multiple progressive rounds and must be auditable and rollbackable.

Do NOT use this skill for: creating documents from scratch; restructuring sections; wholesale rewrites; plain-text documents with no embedded machinery (simpler tools suffice).

## Protected Elements — the "do-not-touch" catalog

The following structures commonly live inside a .docx `word/document.xml` and must NOT be edited, merged, split, or reordered. Before editing, identify which are present so the safe-edit boundaries can be drawn.

| Element | XML marker | Why protected |
|---|---|---|
| Citation/reference fields (Zotero, EndNote, Mendeley) | `<w:fldChar>` begin/separate/end + `<w:instrText>` ADDIN ... | The visible number is a field result; touching the field breaks "update citations" |
| Cross-reference fields | `fldChar` + `instrText` REF / PAGEREF / NOTEREF | Same as above; number is computed |
| Superscript citation markers | `<w:vertAlign w:val="superscript"/>` run between field begin/end | The visible citation; must remain in its exact post-sentence position |
| Bookmarks | `<w:bookmarkStart>` / `<w:bookmarkEnd>` | Cross-reference and heading targets; IDs must stay stable |
| Comments | `<w:commentRangeStart/End>` + `comments.xml` | Comment anchoring must stay intact |
| Tracked changes | `<w:ins>` / `<w:del>` with `w:author`, `w:date` | Author attribution and timestamp must remain verifiable |
| Content controls (Structured Document Tags) | `<w:sdt>` / `<w:sdtPr>` | Bound to custom XML parts or form bindings |
| Equation objects | `<m:oMath>` / `<m:oMathPara>` (OfficeMath) | Math structure must be preserved |
| Custom XML parts | `customXml/*.xml` | Application-specific bound data |
| Drawing / picture anchors | `<w:drawing>` / `<wp:anchor>` / `<a:blip r:embed=...>` | Image relationships and layout must stay |
| Hyperlinks | `<w:hyperlink r:id=...>` | Relationship target must stay |
| Section / page-break properties | `<w:sectPr>`, `<w:lastRenderedPageBreak>` | Pagination must stay |
| Numbering / list definitions | `numbering.xml` + `<w:numPr>` | List rendering must stay |
| Style definitions | `styles.xml` + `<w:pStyle>` | Style names and IDs must stay |

The full expanded catalog with XPath discriminators and "how to recognize each at a glance" is in `references/protected-elements.md`.

## Workflow

The workflow is an 8-step pipeline. Each step has a clear input, output, and verification contract. Detailed per-step instructions, including exact tool invocations and edge cases, are in `references/workflow.md`.

```
Step 0  Comprehend & model      → read full text, build mental model of mainline logic
Step 1  Deconstruct container   → unpack .docx to XML, locate protected vs editable regions
Step 2  Establish copy & sandbox → copy file to "round-N" name, unpack to a working directory
Step 3  Extract editable units  → list plain-text runs with line numbers, excluding field runs
Step 4  Plan the round's policy → decide this round's layer (word/phrase/logic); list candidates
Step 5  Scripted exact replace  → apply (old, new) pairs with str.count==1 assertion per pair
Step 6  Repack                  → pack the working directory back into a .docx
Step 7  Independent verify      → re-open the product; check XML well-formed, structure, citations
Step 8  Produce diff evidence   → generate paragraph/run-level before-vs-after diff
```

### Core invariants (must hold every round)

- Paragraph count and style-name sequence identical to the previous round.
- The full ordered sequence of protected-element markers (superscript citation text, field begin/end counts, bookmark IDs, comment IDs, etc.) is identical to the previous round.
- The number of changed paragraphs equals the number of paragraphs the round intended to change — no more, no less.
- All XML parts remain well-formed; the file opens with python-docx without error.

## How to Use the Bundled Resources

### `scripts/` — deterministic automation

Run these scripts from a shell; they don't need to be loaded into context.

- `scripts/extract_editable_runs.py <unpacked_dir>` — Print every editable plain-text `<w:t>` run as `lineNo: text`, automatically skipping runs inside field-char regions (citation fields, cross-reference fields) and runs carrying protected formatting (superscript citation marks). Use this to build the "what can I edit" map before designing replacements.
- `scripts/apply_replacements.py <unpacked_dir> <pairs_file.json>` — Apply a JSON list of `{"old": ..., "new": ...}` pairs to `word/document.xml`. For each pair, assert the substring occurs exactly once in the file; on any mismatch, abort without writing. This is the "self-proving no-collateral" engine.
- `scripts/verify_edits.py <new.docx> <old.docx>` — Independent third-party verification. Checks: all XML parts well-formed; paragraph count and style sequence identical; superscript citation sequence identical; Zotero/field counts identical; reports which paragraphs changed. Exits non-zero on any structural drift.
- `scripts/diff_paragraphs.py <new.docx> <old.docx>` — Print a paragraph-level before/after diff for every changed paragraph, for hand review and audit delivery.

`pairs_file.json` format:

```json
[
  {"old": "原文片段（唯一）", "new": "润色后片段"},
  {"old": "另一处原文", "new": "另一处润色"}
]
```

### `references/` — loaded when needed

- `references/workflow.md` — Detailed 8-step procedure with exact commands, edge cases (leading-space runs with `xml:space="preserve"`, run splitting after re-unpack, encoding pitfalls on non-UTF-8 consoles, validator codec errors), and rollback procedures.
- `references/protected-elements.md` — Expanded protected-element catalog with XPath markers, recognition heuristics, and "what breaks if you touch it" notes for each.
- `references/xml-anatomy.md` — How common .docx content patterns (a citation, a cross-reference, a tracked-change insertion, a content control, a tracked list item) map to XML, so the editor can recognize each on sight.

## Extraction/Apply/Verify Mini-Pipeline (quick reference)

```
# 0. Set UTF-8 console (Windows) to avoid mojibake in tool output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 1. Create the round-N copy and unpack
Copy-Item final.docx round-N.docx
python <docx-skill>/scripts/office/unpack.py round-N.docx work/
# (the docx skill's unpack.py: pretty-prints, merges adjacent runs, entity-encodes smart quotes)

# 2. Extract editable runs map
python scripts/extract_editable_runs.py work/ > runs.txt

# 3. Design replacements; write to pairs.json

# 4. Apply with uniqueness assertion
python scripts/apply_replacements.py work/ pairs.json

# 5. Repack (validate=false when the validator hits environment codec issues — independent verify covers the same checks)
python <docx-skill>/scripts/office/pack.py work/ round-N.docx --original prev.docx --validate false

# 6. Independently verify
python scripts/verify_edits.py round-N.docx prev.docx

# 7. Diff for audit
python scripts/diff_paragraphs.py round-N.docx prev.docx > round-N.diff.txt
```

## Round-Layering Strategy

When the task spans multiple rounds, layer the work to avoid redoing and to keep each round auditable:

1. **Word-level normalization** — terminology unification, number/date consistency, missing measure words, punctuation normalization, parallelism within enumerations. Low risk, high coverage.
2. **Translation-tone removal / phrasing rewrites** — eliminate "使……能够" / "在……条件下" / "当……时" Englishized constructions; reorder subject/adverbial to native positions; add missing connectives; replace faceless passive structures with active ones. Mid risk; rewrite clauses but keep meaning and section skeleton.
3. **Logic rewrites with linked context** — when a sentence's intended meaning is obscured by poor logical expression, rewrite the sentence AND adjust the surrounding context (the sentence before's lead-in, the sentence after's "therefore/furthermore") so the semantic chain reads cleanly end-to-end. Highest risk; verify the change is confined to the intended neighborhood and no protected element moved.

Each round: copy → unpack → extract → design → apply → repack → verify → diff. Never layer two rounds' edits into a single pass; keep each round self-contained and auditable.

## Critical Rules

- **Protected-element catalog comes first.** Before designing any edit, run `extract_editable_runs.py` to draw the safe-edit boundary. Never edit a run that's inside a field, carries superscript formatting, or is otherwise in the protected catalog.
- **Every replacement must self-prove uniqueness.** `apply_replacements.py` asserts `count == 1` per pair; any ambiguity stops the run without writing. "I was careful" is not a substitute for "I can prove I didn't hit something else."
- **Verification must be independent.** The verify step re-opens the produced .docx with python-docx/lxml and checks from scratch — it does not trust the editing step's assumptions.
- **Never merge, split, or move runs across protected boundaries.** Even if two adjacent plain-text runs look mergeable, the field-bookmark boundary between them may be invisible at a glance. The unpack's run-merging handles benign cases; manual run surgery inside fields is prohibited.
- **Smart quotes and entities.** When adding text with apostrophes or quotes, use the XML entities `&#x2018; &#x2019; &#x201C; &#x201D;` so they survive XML round-tripping. The unpack step already converts smart quotes to entities in existing content; match that convention.
- **Encoding on non-UTF-8 consoles.** PowerShell on Chinese Windows defaults to GBK. Always set `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` at the top of any command that will display or write CJK; otherwise tool output mojibakes and Chinese written to the script via here-strings can be corrupted.

## Scope Boundaries

This skill is **scope-limited to in-place localized edits**. Out of scope and requiring other skills:

- Creating new .docx documents → use the `docx` skill (docx-js) or `minimax-docx`.
- Reformatting / template application → use `minimax-docx` or `officecli`.
- Full document conversion (docx → markdown, docx → PDF) → use `doc-to-markdown` or `pdf`.
- Schema/content validation of the document's intellectual content → use domain-specific review skills.

This skill composes cleanly with the `docx` skill: the `docx` skill provides `unpack.py` / `pack.py` for the ZIP↔XML round-trip; this skill provides the safe-edit, verify, and diff layers on top of that round-trip.
