#!/usr/bin/env python3
"""
Apply a list of (old, new) replacement pairs to an unpacked .docx's
word/document.xml with a hard uniqueness assertion per pair.

Usage:
    python apply_replacements.py <unpacked_dir> <pairs_file.json> [--target <relative_xml_path>]

The pairs file is a JSON array of objects with "old" and "new" string fields:

    [
      {"old": "原文片段（须全文档唯一）", "new": "润色后片段"},
      {"old": "另一处", "new": "另一处改后"}
    ]

Contract:
- Read <unpacked_dir>/word/document.xml (or --target path relative to unpacked_dir).
- Back it up to <path>.bak.
- For each pair in order:
    * Assert text.count(old) == 1 in the current in-memory buffer.
    * If any pair fails the assertion, abort WITHOUT writing; original file unchanged.
    * On success, apply str.replace(old, new, 1).
- Write the buffer back only if ALL pairs matched uniquely.

Why per-pair uniqueness: this is the "self-proving no-collateral" guarantee.
Freehand edits can heal one occurrence and silently corrupt another identical
substring elsewhere. Forcing count==1 turns "I was careful" into "I can prove
I touched exactly one place."

Notes:
- Pairs are applied sequentially; later pairs search the buffer as modified by
  earlier pairs. Design pairs so they don't collide (no pair's "old" is a
  substring created by an earlier pair's "new").
- If you need to apply the same change to multiple occurrences, split it into
  explicit pairs with enough surrounding context to make each unique.
- The script does NOT touch field-char regions, superscript citation runs,
  comments, or any protected element directly — it only does plain string
  replacement on the XML text. You, the designer of pairs, are responsible
  for ensuring your "old" / "new" strings do not span protected-element
  boundaries. Use extract_editable_runs.py first to confirm safe zones.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("unpacked_dir", help="Directory produced by docx skill's unpack.py")
    p.add_argument("pairs_file", help="JSON file with the replacement pairs")
    p.add_argument("--target", default="word/document.xml",
                   help="Relative path of the XML to edit (default: word/document.xml)")
    args = p.parse_args()

    target = os.path.join(args.unpacked_dir, args.target)
    if not os.path.isfile(target):
        sys.stderr.write(f"ERROR: target not found: {target}\n")
        return 2

    try:
        with open(args.pairs_file, encoding="utf-8") as f:
            pairs = json.load(f)
    except Exception as e:
        sys.stderr.write(f"ERROR: cannot read pairs file: {e}\n")
        return 2

    if not isinstance(pairs, list) or not all(isinstance(x, dict) and "old" in x and "new" in x for x in pairs):
        sys.stderr.write("ERROR: pairs file must be a JSON array of {\"old\":..., \"new\":...} objects\n")
        return 2

    with open(target, encoding="utf-8") as f:
        src = f.read()

    # Backup.
    shutil.copy(target, target + ".bak")

    out = src
    failures: list[str] = []
    for i, pair in enumerate(pairs):
        o = pair["old"]
        n = pair["new"]
        if not isinstance(o, str) or not isinstance(n, str):
            failures.append(f"pair {i}: 'old'/'new' must be strings")
            break
        c = out.count(o)
        if c != 1:
            preview = o[:80].replace("\n", "\\n")
            failures.append(f"pair {i}: count={c} (expected 1)  old='{preview}{'...' if len(o) > 80 else ''}'")
            break
        out = out.replace(o, n, 1)

    if failures:
        sys.stderr.write("UNIQUENESS FAILURES — file NOT modified:\n")
        for msg in failures:
            sys.stderr.write(f"  {msg}\n")
        return 1

    with open(target, "w", encoding="utf-8") as f:
        f.write(out)
    sys.stdout.write(f"OK applied {len(pairs)} edits to {args.target}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))