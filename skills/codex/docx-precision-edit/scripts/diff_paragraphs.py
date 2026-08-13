#!/usr/bin/env python3
"""
Generate a paragraph-level before-vs-after diff between two .docx files,
printing only the paragraphs whose concatenated <w:t> text differs.

Usage:
    python diff_paragraphs.py <new.docx> <old.docx> [-o output_file] [--full]

Output (to stdout or -o file), one block per changed paragraph:

    ### Para <i> [<style_name>]
    OLD: <full old text>
    NEW: <full new text>

    ### Para <j> [<style_name>]
    OLD: ...
    NEW: ...

By default the text is truncated to 600 chars per side for readability; use
--full to print the entire text. A final summary line reports the count.

This is the audit-trail step: hand the produced diff to reviewers, or attach
it to a delivery note to make "what changed in this round" self-evident.

The script is stdlib-only (no python-docx, no lxml) so it runs anywhere.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{" + W_NS + "}"


def _paragraphs(zip_path: str) -> list[tuple[str, str]]:
    with zipfile.ZipFile(zip_path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    paras = []
    for p in root.iter(W + "p"):
        style = ""
        ppr = p.find(W + "pPr")
        if ppr is not None:
            pstyle = ppr.find(W + "pStyle")
            if pstyle is not None:
                style = pstyle.get(W + "val") or ""
        text_parts = []
        for t in p.iter(W + "t"):
            if t.text:
                text_parts.append(t.text)
        paras.append((style, "".join(text_parts)))
    return paras


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("new_docx")
    p.add_argument("old_docx")
    p.add_argument("-o", "--output", help="Write diff to this file instead of stdout")
    p.add_argument("--full", action="store_true", help="Do not truncate paragraph text")
    args = p.parse_args()

    new = _paragraphs(args.new_docx)
    old = _paragraphs(args.old_docx)

    if len(new) != len(old):
        sys.stderr.write(f"WARNING: paragraph counts differ (new={len(new)} old={len(old)}); diffing common prefix\n")

    out_lines: list[str] = []
    changed = 0
    n = min(len(new), len(old))
    for i in range(n):
        s_old, t_old = old[i]
        s_new, t_new = new[i]
        if t_old != t_new:
            changed += 1
            out_lines.append(f"### Para {i} [{s_new}]")
            if args.full:
                out_lines.append(f"OLD: {t_old}")
                out_lines.append(f"NEW: {t_new}")
            else:
                lim = 600
                o = t_old if len(t_old) <= lim else t_old[:lim] + "…"
                n_ = t_new if len(t_new) <= lim else t_new[:lim] + "…"
                out_lines.append(f"OLD: {o}")
                out_lines.append(f"NEW: {n_}")
            out_lines.append("")

    out_lines.append(f"=== changed paragraphs: {changed} of {n} ===")

    text = "\n".join(out_lines)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stdout.write(f"wrote {args.output} ({changed} changed paragraphs)\n")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))