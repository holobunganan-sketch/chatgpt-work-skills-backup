# Detailed 8-Step Workflow

This reference expands the workflow overview in SKILL.md into per-step
procedures with exact tool invocations, edge cases, and rollback procedures.
Read it the first time through the pipeline; once fluent, the SKILL.md
overview plus `extract_editable_runs.py` / `apply_replacements.py` /
`verify_edits.py` / `diff_paragraphs.py` are sufficient.

Conventions:
- `<docx-skill>` = the install path of the bundled `docx` skill (provides
  `scripts/office/unpack.py` and `scripts/office/pack.py`). This skill composes
  with that one; it does not duplicate its unpack/pack scripts.
- All PowerShell commands assume Windows; on Linux/macOS use `cp`/`python3`.

## Step 0 — Comprehend & model

Goal: build a mental model of the document's mainline logic and chapter
skeleton before touching anything.

Actions:
1. Extract the full plain text using python-docx or pandoc (if available):
   ```python
   import docx
   d = docx.Document("input.docx")
   for i, p in enumerate(d.paragraphs):
       print(f"[{i}|{p.style.name}] {p.text}")
   ```
2. Read the full text end-to-end. For each section, note its role in the
   argument chain (foundation / method / evidence / recommendation / conclusion).
3. Build a one-line-per-paragraph outline in your head or in a scratch file.
   This model is the reference against which "does this edit preserve meaning?"
   is judged.

Outputs: a paragraph-level mental outline; understanding of which paragraphs
are most load-bearing (chapter intros, recommendation statements, conclusion)
and which are routine (boilerplate, methods).

Why this step matters: without a model, "preserve meaning" is impossible to
verify. The model is what lets Step 4 produce edits that the author would
approve, and Step 7 verify them honestly.

## Step 1 — Deconstruct the container

Goal: locate protected vs editable regions inside the .docx.

Actions:
1. Unpack with the docx skill's `unpack.py` (pretty-prints XML, merges adjacent
   same-format runs, converts smart quotes to XML entities so they survive
   editing):
   ```bash
   python <docx-skill>/scripts/office/unpack.py input.docx work/
   ```
2. Inspect `work/word/document.xml`:
   - `grep` for `vertAlign` to find superscript citation marks.
   - `grep` for `fldCharType` to find field regions.
   - `grep` for `ADDIN` to identify which reference manager is in use.
   - `grep` for `<w:ins ` / `<w:del ` to find tracked changes.
   - `grep` for `<w:sdt>` to find content controls.
   - `grep` for `<m:oMath` to find equations.
3. Build the protected-element inventory for THIS document. Use
   `references/protected-elements.md` to interpret unfamiliar structures.

Outputs: a list of "things I must not touch" specific to this document.

Edge cases:
- A document may have NO citation fields (plain report) — Step 1 still confirms
  that, so you proceed with confidence rather than assumption.
- A document may have customXml parts that lxml cannot parse; that's not a
  failure of the document, just an opaque bound-data part. Leave it alone.

## Step 2 — Establish copy & sandbox

Goal: work on a copy, never the source. Each round gets its own file.

Actions:
1. Decide the round's naming scheme. For iterative polish, name copies with
   the round number and date, e.g.:
   ```
   input.docx  →  round-1.docx  →  round-2.docx  →  ...
   ```
   Or, in the spirit of the original use case, suffix the descriptive name:
   ```
   …_第十四轮…_20260727.docx  →  …_第十五轮…_20260728.docx
   ```
2. Copy the latest accepted file to the new round name.
3. Unpack the new file into a working directory:
   ```bash
   python <docx-skill>/scripts/office/unpack.py round-N.docx work-N/
   ```

Outputs: `round-N.docx` (the to-be-edited file) and `work-N/` (its unpacked
XML). The previous round's file is untouched.

Why copy: every round is rollbackable by simply discarding the new file and
re-running from the previous round. Diffing two .docx files is also trivial
when each round exists as its own file.

## Step 3 — Extract editable units

Goal: produce the "what can I safely edit" map for this document.

Actions:
1. Run:
   ```bash
   python scripts/extract_editable_runs.py work-N/ > runs-N.txt
   ```
2. Read `runs-N.txt`. Each line is `lineNo: text`. The script has already
   skipped:
   - Runs inside `<w:fldChar>` regions (citation/cross-reference fields).
   - Runs whose preceding rPr carries `vertAlign superscript` (visible marks).
   - Runs inside `<w:sdt>` (content controls).
   - Runs inside `<m:oMath>` / `<m:oMathPara>` (equations).
3. Cross-check the count against the model from Step 0: do the editable runs
   reconstruct the document's plain narrative? If a meaningful sentence is
   missing, it may be inside a field — investigate.

Outputs: the safe-edit map.

Edge cases:
- After re-unpacking a previously packed file, run counts can differ (the
  unpack's run-merging is deterministic but may produce different boundaries
  when input XML is already condensed). Text content is identical; only run
  boundaries shift. This is normal.
- A `<w:t>` with leading space carries `xml:space="preserve"`. The leading
  space appears in `runs-N.txt`; when designing replacements, anchor on a
  substring that avoids the leading space unless you specifically handle it.

## Step 4 — Plan the round's policy

Goal: decide what THIS round should and shouldn't touch, then design the
specific replacement pairs.

Actions:
1. Pick the round's layer:
   - **Word-level normalization** (round 1 of a multi-round job): terminology
     unification, missing measure words, punctuation normalization,
     parallelism within enumerations, date/number consistency.
   - **Translation-tone removal / phrasing rewrites** (round 2): eliminate
     Englishized constructions; reorder subject/adverbial; add missing
     connectives; replace faceless passives with active voice.
   - **Logic rewrites with linked context** (round 3 and beyond): rewrite a
     sentence whose meaning is obscured AND adjust its neighbors so the
     semantic chain reads cleanly end-to-end.
2. For each candidate edit, write the (old, new) pair to a JSON file:
   ```json
   [
     {"old": "原文片段", "new": "润色后片段"}
   ]
   ```
   Make each `old` substring specific enough to be unique in the file. If the
   same phrase appears in three places and you want to change only one, include
   surrounding context (a few characters before or after) to disambiguate.
3. Do NOT design pairs that cross protected-element boundaries. The `old`
   string should sit entirely within one editable run (or, if it spans multiple
   adjacent editable runs that the unpack didn't merge, design two pairs
   instead).

Outputs: `pairs-N.json`.

Design rules of thumb:
- A pair's `old` should not be a substring of another pair's `new`. Otherwise
  the second pair could match the first's output and the uniqueness assertion
  fails or, worse, succeeds but on the wrong occurrence.
- If you intend to rewrite a whole sentence, use the full sentence as `old`;
  this makes the audit diff legible and the uniqueness check trivial.
- For run-split cases (a sentence broken across two `<w:t>` runs by an
  intervening field or a formatting change), edit each fragment as a separate
  pair rather than trying to bridge the split.

## Step 5 — Scripted exact replace

Goal: apply the pairs with a hard uniqueness assertion per pair.

Actions:
1. Run:
   ```bash
   python scripts/apply_replacements.py work-N/ pairs-N.json
   ```
2. The script:
   - Backs up `work-N/word/document.xml` to `.bak`.
   - For each pair, asserts `text.count(old) == 1`. On any mismatch, aborts
     WITHOUT writing. The file is untouched on abort.
   - On all-pass, writes the modified buffer back.
3. If any pair fails uniqueness, either:
   - Add more context to the `old` to make it unique, or
   - If the substring genuinely doesn't exist (a typo in your `old`), fix the
     `old` to match the file exactly (use `runs-N.txt` to verify).

Outputs: `work-N/word/document.xml` modified; `work-N/word/document.xml.bak`
preserved.

Critical rules:
- "Self-proving no-collateral": `count==1` per pair is non-negotiable. If you
  are tempted to use `count>=1` because "the second occurrence is fine too,"
  you have lost the audit property. Split into explicit pairs instead.
- Never edit inside field-char regions, inside `<w:sdt>`, inside `<m:oMath>`,
  inside `<w:ins>`/`<w:del>`, or in a superscript run. The extraction script
  has already steered you away, but the apply script is text-only — it does
  what you tell it. You are the boundary enforcer.
- Smart quotes: when adding new text with apostrophes or quotes, use the XML
  entities `&#x2018; &#x2019; &#x201C; &#x201D;` so they survive the
  round-trip. The unpack's entity-conversion handles existing smart quotes;
  match that convention in your `new` strings.

## Step 6 — Repack

Goal: turn the working directory back into a .docx.

Actions:
1. Run:
   ```bash
   python <docx-skill>/scripts/office/pack.py work-N/ round-N.docx --original round-(N-1).docx --validate false
   ```
2. The `--original` flag uses the previous round as the ZIP metadata reference.
3. The `--validate false` flag skips the docx skill's built-in validator. This
   is sometimes necessary on non-UTF-8 consoles where the validator hits a
  codec error reading XML parts (e.g., GBK Windows reading a non-GBK file).
   The independent verify step in Step 7 covers the same correctness ground
   with a stdlib + lxml path that doesn't share the codec issue.

Outputs: `round-N.docx`.

Edge cases:
- File size after repack can differ from the previous round. Common causes:
  re-unpacking a condensed file produces more run splits; the pack's XML
  condensation is less aggressive than a previous round's. As long as Step 7
  passes (paragraph count, style sequence, citation sequence, field counts
  all identical), the size difference is cosmetic.
- The `customXml/item*.xml` parts may not parse with lxml; that's an opaque
  bound-data part, not a corruption. `verify_edits.py` treats these as
  non-blocking warnings.

## Step 7 — Independent verify

Goal: prove the product is structurally identical to the previous round except
for the intended text edits. Verification must NOT trust the editing step.

Actions:
1. Run:
   ```bash
   python scripts/verify_edits.py round-N.docx round-(N-1).docx
   ```
2. The script checks, from scratch (re-opens the .docx with stdlib + lxml):
   - All XML parts well-formed.
   - Paragraph count identical.
   - Per-paragraph style-name sequence identical (chapter skeleton preserved).
   - Ordered superscript citation sequence identical (citation positions
     preserved).
   - Zotero ADDIN item count, field-char begin count, field-char end count
     identical (citation fields and cross-reference fields intact).
   - Reports which paragraphs changed, with short previews.
3. Accept the round only if the script prints `RESULT: PASS` and the list of
   changed paragraphs matches what you intended in Step 4.

Outputs: a verify report to stdout. Save it as `round-N.verify.txt` for
audit.

Critical rules:
- Verification must be independent: it opens the produced .docx afresh, not
  the in-memory buffer from Step 5. This catches repack bugs, encoding bugs,
  and accidental field-region edits.
- The number of changed paragraphs MUST equal the number of paragraphs you
  intended. If `verify_edits.py` reports 7 changed but you only designed 5
  edits, two unintended changes happened — investigate before delivery.

## Step 8 — Produce diff evidence

Goal: generate a legible before-vs-after diff for the round.

Actions:
1. Run:
   ```bash
   python scripts/diff_paragraphs.py round-N.docx round-(N-1).docx -o round-N.diff.txt
   ```
2. The diff shows, for every changed paragraph:
   ```
   ### Para <i> [<style_name>]
   OLD: <old text, truncated to 600 chars>
   NEW: <new text, truncated to 600 chars>
   ```
   Use `--full` to disable truncation.
3. Optionally, also produce a run-level diff (use `extract_editable_runs.py`
   on both the previous and current round's unpacked dirs and diff the two
   `runs-N.txt` files) for finer-grained audit.

Outputs: `round-N.diff.txt`.

Why this step matters: the diff is what makes the round auditable. Hand it to
a reviewer or attach to the delivery note so "what changed in this round" is
self-evident, not asserted.

## Rollback procedures

- **Round-level rollback**: discard `round-N.docx`; re-run from `round-(N-1).docx`.
  The previous round's file is intact by construction (Step 2 only copies).
- **Edit-level rollback**: `apply_replacements.py` writes
  `work-N/word/document.xml.bak` before applying. To undo an apply that
  succeeded, copy `.bak` back over `document.xml` and re-pack.
- **Mid-apply abort**: `apply_replacements.py` does NOT write the file on any
  uniqueness failure — no rollback needed, the file is already pristine.

## Encoding checklist (Windows / non-UTF-8 consoles)

Set UTF-8 console output before any command that displays or writes CJK:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
```
Without this:
- Tool stdout mojibakes (unreadable but not corrupting).
- Chinese written to a Python script via a PowerShell here-string can be
  corrupted before the script ever sees it.
- The docx skill's validator may report `gbk codec can't decode` errors that
  are environment issues, not file issues (Step 6's `--validate false` works
  around this; Step 7 independently verifies).

Always prefer writing Python scripts to a file (via the `write` tool or
`Set-Content -Encoding UTF8`) over passing them inline via `python -c` with
CJK content; the latter is fragile on Windows.