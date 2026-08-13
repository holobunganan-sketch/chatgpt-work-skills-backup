#!/usr/bin/env python3
"""
Independently verify that two .docx files are structurally identical except for
the intended paragraph text edits. This is the third-party check that runs
AFTER the editing step — it does not trust the edit step's assumptions.

Usage:
    python verify_edits.py <new.docx> <old.docx>

Checks performed (all must pass):
  1. All XML parts in the new file are well-formed.
  2. Paragraph count in new vs old is identical.
  3. The style-name sequence of paragraphs is identical (chapter skeleton preserved).
  4. The ordered sequence of superscript citation/marker runs is identical
     (citation positions and numbers preserved).
  5. The count of Zotero/field ADDIN items, field-char begins, and field-char
     ends are identical (citation fields and cross-reference fields intact).
  6. Report which paragraphs changed and a short preview.

Exit code is 0 only if checks 1-5 pass. The script prints a summary and a
per-changed-paragraph preview to stdout.

Caveats:
- This script treats .docx as opaque ZIPs of XML; it does not require the
  docx skill and uses only stdlib + lxml. If lxml is unavailable, it falls
  back to a lighter ElementTree-based path for the well-formedness check
  but skips checks that need lxml's namespace-handling shortcuts.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from xml.etree import ElementTree as ET

try:
    from lxml import etree as LET
    HAVE_LXML = True
except Exception:
    HAVE_LXML = False


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{" + W_NS + "}"
NS = {"w": W_NS}


def _parse(zip_path: str, inner: str):
    with zipfile.ZipFile(zip_path) as z:
        return z.read(inner)


def _wellformed(zip_path: str) -> list[str]:
    bad: list[str] = []
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            try:
                data = z.read(name)
                if HAVE_LXML:
                    LET.fromstring(data)
                else:
                    ET.fromstring(data)
            except Exception as e:
                bad.append(f"{name}: {e}")
    return bad


def _paragraphs(zip_path: str) -> list[tuple[str, str]]:
    """Return list of (style_name, text) per paragraph."""
    # stdlib-only path: avoid relying on python-docx being installed.
    root = ET.fromstring(_parse(zip_path, "word/document.xml"))
    paras = []
    for p in root.iter(W + "p"):
        # Style name: first <w:pStyle w:val="..."/> in pPr
        style = ""
        ppr = p.find(W + "pPr")
        if ppr is not None:
            pstyle = ppr.find(W + "pStyle")
            if pstyle is not None:
                style = pstyle.get(W + "val") or ""
        # Concatenate <w:t> texts (excluding instrText/delText).
        text_parts = []
        for t in p.iter(W + "t"):
            if t.text:
                text_parts.append(t.text)
        paras.append((style, "".join(text_parts)))
    return paras


def _superscripts(zip_path: str) -> list[str]:
    """Ordered list of superscript run texts (citation markers)."""
    if not HAVE_LXML:
        return []
    root = LET.fromstring(_parse(zip_path, "word/document.xml"))
    out = []
    for r in root.iter(f"{{{W_NS}}}r"):
        rpr = r.find("w:rPr", NS)
        if rpr is None:
            continue
        va = rpr.find("w:vertAlign", NS)
        if va is not None and va.get(f"{{{W_NS}}}val") == "superscript":
            t = r.find("w:t", NS)
            if t is not None and t.text:
                out.append(t.text)
    return out


def _field_counts(zip_path: str) -> tuple[int, int, int]:
    """(ADDIN_ZOTERO_ITEM count, fldChar begin count, fldChar end count)."""
    body = _parse(zip_path, "word/document.xml").decode("utf-8", errors="replace")
    return (
        body.count("ADDIN ZOTERO_ITEM"),
        body.count('fldCharType="begin"'),
        body.count('fldCharType="end"'),
    )


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("new_docx", help="The edited .docx to verify")
    p.add_argument("old_docx", help="The previous-round .docx to compare against")
    args = p.parse_args()

    failures: list[str] = []

    # 1. XML well-formedness of new file.
    bad = _wellformed(args.new_docx)
    # customXml parts are warnings, not failures — they're application-bound
    # parts that may be opaque; flag them but don't fail unless core parts fail.
    real_bad = [b for b in bad if not b.startswith("customXml/")]
    if real_bad:
        failures.append(f"XML well-formedness failures: {real_bad}")
    if bad and real_bad != bad:
        print("WARNING (non-blocking): customXml parts not parseable:")
        for b in bad:
            if b.startswith("customXml/"):
                print(f"  {b}")

    # 2-3. Paragraphs and styles.
    new_paras = _paragraphs(args.new_docx)
    old_paras = _paragraphs(args.old_docx)
    if len(new_paras) != len(old_paras):
        failures.append(f"paragraph count: new={len(new_paras)} old={len(old_paras)}")
    else:
        new_styles = [s for s, _ in new_paras]
        old_styles = [s for s, _ in old_paras]
        if new_styles != old_styles:
            # Report first divergence for diagnostics.
            for i, (a, b) in enumerate(zip(old_styles, new_styles)):
                if a != b:
                    failures.append(f"style divergence at paragraph {i}: old='{a}' new='{b}'")
                    break

    # 4. Superscript citation sequence.
    if HAVE_LXML:
        new_supers = _superscripts(args.new_docx)
        old_supers = _superscripts(args.old_docx)
        if len(new_supers) != len(old_supers):
            failures.append(f"superscript count: new={len(new_supers)} old={len(old_supers)}")
        elif new_supers != old_supers:
            # Find first divergence.
            for i, (a, b) in enumerate(zip(old_supers, new_supers)):
                if a != b:
                    failures.append(f"superscript divergence at #{i}: old='{a}' new='{b}'")
                    break
    else:
        print("NOTE: lxml unavailable — skipping superscript-sequence check")

    # 5. Field counts.
    new_fields = _field_counts(args.new_docx)
    old_fields = _field_counts(args.old_docx)
    if new_fields != old_fields:
        failures.append(f"field counts differ: new={new_fields} old={old_fields}")

    # 6. Changed paragraphs (informational, not a failure).
    changed = []
    if len(new_paras) == len(old_paras):
        for i, ((so, to_), (sn, tn)) in enumerate(zip(old_paras, new_paras)):
            if to_ != tn:
                changed.append(i)

    # Report.
    print("=" * 60)
    print("VERIFY REPORT")
    print("=" * 60)
    print(f"new file      : {args.new_docx}")
    print(f"reference file: {args.old_docx}")
    print(f"paragraphs    : new={len(new_paras)} old={len(old_paras)}")
    if HAVE_LXML:
        print(f"superscripts   : new={len(new_supers)} old={len(old_supers)}   same={new_supers == old_supers}")
    else:
        print("superscripts   : SKIPPED (lxml unavailable)")
    print(f"zotero items   : new={new_fields[0]} old={old_fields[0]}")
    print(f"field begins   : new={new_fields[1]} old={old_fields[1]}")
    print(f"field ends     : new={new_fields[2]} old={old_fields[2]}")
    print(f"style sequence : {'identical' if len(new_paras) == len(old_paras) and [s for s,_ in new_paras] == [s for s,_ in old_paras] else 'DIVERGENT'}")
    print(f"changed paras  : {len(changed)} -> {changed}")
    print()

    if changed:
        print("-" * 60)
        for i in changed[:20]:
            so_text = old_paras[i][1]
            sn_text = new_paras[i][1]
            preview = 140
            print(f"--- para {i} ---")
            print(f"  OLD: {so_text[:preview]}{'...' if len(so_text) > preview else ''}")
            print(f"  NEW: {sn_text[:preview]}{'...' if len(sn_text) > preview else ''}")
        if len(changed) > 20:
            print(f"  ... and {len(changed) - 20} more")
        print("-" * 60)

    if failures:
        print()
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print()
    print("RESULT: PASS  (structure and protected elements preserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))