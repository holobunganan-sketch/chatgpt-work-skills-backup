# Publication Delivery Rules

## Publication profile

Treat typography, heading hierarchy, abstract labels, citation style, and title-page policy as configuration. Use `assets/default-profile.json` only when no journal or user profile overrides it.

## Citation handling

- Map each citation to a verified library item.
- Keep external citations in the configured sections.
- Do not cite external literature in Results under the default profile.
- Do not create bibliographic metadata from memory when identifiers are available.
- Preserve citation groups and order during language editing.
- Validate that every in-text citation resolves to the bibliography.

When Zotero is required, verify real Word fields:

- `ZOTERO_ITEM` for in-text citations;
- `ZOTERO_BIBL` for the bibliography;
- `ZOTERO_PREFS` for document preferences.

Plain superscripts or typed references are not Zotero embedding.

## Figure and table placement

Maintain an asset manifest containing identifier, title, scientific purpose, source path, source data, manuscript placement, and supplementary status.

For each empirical asset:

1. Cite its identifier in the prose.
2. Insert it after the paragraph that first interprets its content.
3. Keep the identifier consistent in prose, caption, filename, and manifest.
4. Keep a figure and its caption on the same page.
5. Keep a table title with the table and repeat headers across pages when needed.
6. Prevent table data rows from splitting when the format permits.

Place a methods schematic in Methods only if it contains no realized participant counts, selected model, fitted parameters, or performance results. Otherwise place it in Results.

## Default caption rules

- Use `Figure X` and `Table X` numbering.
- Put figure captions below figures and center them.
- Put table titles above tables and center them.
- Use notes below tables for abbreviations, denominators, thresholds, and analysis qualifications.
- Do not repeat a large visible title inside a figure when the caption already provides it unless the journal requires an internal title.

## DOCX requirements

- Keep the document editable.
- Use Word styles rather than scattered direct formatting where practical.
- Apply the configured font, size, color, line spacing, margins, and heading policy.
- Keep headings with the following paragraph.
- Avoid a separate title page when the profile disables it.
- Keep Conclusion to the configured paragraph count.
- Preserve vector or high-resolution source assets and embed submission-quality raster derivatives when required.

## Structural QC

Check:

- valid DOCX ZIP container;
- parseable XML and relationship files;
- no unresolved citation or asset markers;
- expected table and drawing counts;
- expected Zotero-field counts;
- correct section and asset order;
- continuous numbering;
- no duplicated captions;
- no missing bibliography.

Use `scripts/audit_docx.py` for deterministic checks.

## Visual QC

Render the DOCX through Word, LibreOffice, or another trustworthy layout engine. Inspect:

- first page and abstract;
- Methods-to-Results transition;
- every page containing a figure or table;
- reference pages;
- final page.

Reject the deliverable when any page shows clipping, overlap, blank-page artifacts, orphan headings, separated figure captions, unreadable labels, broken table rows, or inconsistent typography. OOXML validity alone is insufficient.

## Delivery set

Deliver:

- final editable DOCX;
- editable manuscript source;
- asset placement manifest;
- QC report;
- unresolved-items list;
- optional rendered PDF for inspection.

Do not include temporary files or local absolute paths in a portable skill or submission package.
