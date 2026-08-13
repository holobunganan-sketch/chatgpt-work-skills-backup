#!/usr/bin/env python3
"""
Extract editable plain-text runs from an unpacked .docx, excluding runs that
belong to protected elements (citation/cross-reference fields, superscript
citation marks, content controls, equation runs, etc.).

Usage:
    python extract_editable_runs.py <unpacked_dir> [--document-only]

Reads <unpacked_dir>/word/document.xml (pretty-printed by the docx skill's
unpack.py) and prints one line per editable <w:t> element:

    <lineNo>: <text content>

The following runs are automatically skipped (treated as protected):

- Any <w:t> whose enclosing <w:r> sits inside a field-char region
  (between a <w:fldChar w:fldCharType="begin"> and the matching "end").
- Any <w:t> whose enclosing <w:r>'s <w:rPr> contains <w:vertAlign w:val="superscript"/>
  (visible citation / cross-reference marker number).
- Any <w:t> whose enclosing <w:r> sits inside a <w:sdt> content control.
- Any <w:instrText> or <w:delText> (field instructions and tracked-change deletes).
- Any <m:t> math run (inside OfficeMath <m:oMath>).

The script is line-oriented: it expects the pretty-printed XML produced by the
docx skill's unpack.py (one element per line). It still works on condensed XML
because the matching is done by scanning lines and tracking state, but the
line numbers reported will only be meaningful on pretty-printed XML.
"""
from __future__ import annotations

import argparse
import os
import re
import sys


_tag_re = re.compile(r"<([A-Za-z][A-Za-z0-9._-]*)([^>]*)>")


def _is_field_begin(line: str) -> bool:
    return 'fldCharType="begin"' in line or "fldCharType='begin'" in line


def _is_field_end(line: str) -> bool:
    return 'fldCharType="end"' in line or "fldCharType='end'" in line


def _is_superscript(line: str) -> bool:
    return 'vertAlign w:val="superscript"' in line or "vertAlign w:val='superscript'" in line


def _is_math_tag(tag: str) -> bool:
    return tag.startswith("m:")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("unpacked_dir", help="Directory produced by docx skill's unpack.py")
    parser.add_argument("--document-only", action="store_true", help="Only process word/document.xml")
    args = parser.parse_args()

    doc_xml = os.path.join(args.unpacked_dir, "word", "document.xml")
    if not os.path.isfile(doc_xml):
        sys.stderr.write(f"ERROR: not found: {doc_xml}\n")
        return 2

    with open(doc_xml, encoding="utf-8") as f:
        lines = f.readlines()

    field_depth = 0          # nesting of field-char regions
    sdt_depth = 0           # nesting of content controls
    math_depth = 0          # nesting of OfficeMath elements
    out_lines: list[str] = []

    for idx, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s:
            continue

        # Track field-char regions.
        if _is_field_begin(s):
            field_depth += 1
        if _is_field_end(s):
            field_depth = max(0, field_depth - 1)

        # Track content controls (SDT).
        if s.startswith("<w:sdt>") or s.startswith("<w:sdt "):
            sdt_depth += 1
        if s.startswith("</w:sdt>"):
            sdt_depth = max(0, sdt_depth - 1)

        # Track OfficeMath regions.
        m = _tag_re.match(s)
        if m:
            tag = m.group(1)
            if tag in ("m:oMath", "m:oMathPara"):
                math_depth += 1
            if tag in ("/m:oMath", "/m:oMathPara"):
                math_depth = max(0, math_depth - 1)

        # Detect <w:r> properties block preceding a <w:t> so we can check for
        # superscript formatting carried by the run. We do this by scanning the
        # current line: unpack.py pretty-prints rPr on its own lines, so the
        # superscript marker line precedes the <w:t> line. We cache it.
        # Simpler approach: detect superscript anywhere in the preceding 12 lines.
        if s.startswith("<w:t") and not s.startswith("<w:tBlur") and field_depth == 0 and sdt_depth == 0 and math_depth == 0:
            # Look back up to 15 lines for a superscript rPr.
            lookback = "".join(lines[max(0, idx - 16): idx])
            if _is_superscript(lookback):
                continue
            # Extract text content of <w:t ...>text</w:t>.
            mm = re.search(r"<w:t[^>]*>(.*)</w:t>", s)
            if not mm:
                # Possibly a self-closing or multiline <w:t>; skip defensively.
                continue
            text = mm.group(1)
            out_lines.append(f"{idx}: {text}")

        # Skip <w:instrText> (field instructions) and <w:delText> (tracked deletes)
        # explicitly — they never print here because the <w:t> branch above does
        # not match them, but make the contract explicit.

    sys.stdout.write("\n".join(out_lines))
    if out_lines:
        sys.stdout.write("\n")
    sys.stderr.write(f"editable runs: {len(out_lines)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))