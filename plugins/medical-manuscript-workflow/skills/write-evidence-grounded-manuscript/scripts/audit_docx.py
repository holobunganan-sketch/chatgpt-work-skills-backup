#!/usr/bin/env python3
"""Audit DOCX integrity, fields, assets, fonts, and unresolved tokens."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
UNRESOLVED_RE = re.compile(r"\[\[(?:TABLE|FIGURE|CITE|ZOTERO|BIBLIOGRAPHY)[^\]]*\]\]", re.IGNORECASE)


def add_issue(target: list[dict[str, Any]], code: str, message: str, **details: Any) -> None:
    item: dict[str, Any] = {"code": code, "message": message}
    if details:
        item["details"] = details
    target.append(item)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", help="DOCX file to audit")
    parser.add_argument("--require-zotero", action="store_true")
    parser.add_argument("--expected-zotero-items", type=int)
    parser.add_argument("--expected-tables", type=int)
    parser.add_argument("--expected-figures", type=int)
    parser.add_argument("--expected-font", help="Report an error if this font is absent from OOXML font declarations")
    parser.add_argument("--json-out")
    return parser.parse_args()


def audit(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.docx).resolve()
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    if not path.is_file():
        add_issue(errors, "missing-file", "DOCX does not exist", path=str(path))
        return {"status": "fail", "docx": str(path), "errors": errors, "warnings": warnings, "metrics": metrics}

    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            metrics["zip_crc_bad_member"] = bad_member
            if bad_member:
                add_issue(errors, "zip-crc", "DOCX ZIP CRC failed", member=bad_member)

            names = archive.namelist()
            xml_errors: list[dict[str, str]] = []
            for name in names:
                if not (name.endswith(".xml") or name.endswith(".rels")):
                    continue
                try:
                    ET.fromstring(archive.read(name))
                except Exception as exc:  # noqa: BLE001
                    xml_errors.append({"file": name, "error": str(exc)})
            metrics["xml_errors"] = xml_errors
            if xml_errors:
                add_issue(errors, "xml-parse", "One or more OOXML parts failed to parse", files=xml_errors)

            if "word/document.xml" not in names:
                add_issue(errors, "document-xml", "word/document.xml is missing")
                return {"status": "fail", "docx": str(path), "errors": errors, "warnings": warnings, "metrics": metrics}

            document_bytes = archive.read("word/document.xml")
            document_text = document_bytes.decode("utf-8", errors="replace")
            root = ET.fromstring(document_bytes)
            visible_text = "".join(node.text or "" for node in root.findall(".//w:t", NS))

            metrics["tables"] = len(root.findall(".//w:tbl", NS))
            metrics["drawings"] = len(root.findall(".//w:drawing", NS))
            metrics["zotero_item_fields"] = document_text.count("ZOTERO_ITEM")
            metrics["zotero_bibliography_fields"] = document_text.count("ZOTERO_BIBL")
            metrics["zotero_preferences_fields"] = document_text.count("ZOTERO_PREFS")
            metrics["unresolved_tokens"] = UNRESOLVED_RE.findall(visible_text)

            if metrics["unresolved_tokens"]:
                add_issue(errors, "unresolved-token", "Unresolved manuscript tokens remain", tokens=metrics["unresolved_tokens"])

            if args.expected_tables is not None and metrics["tables"] != args.expected_tables:
                add_issue(errors, "table-count", "Embedded table count differs from expectation", expected=args.expected_tables, actual=metrics["tables"])
            if args.expected_figures is not None and metrics["drawings"] != args.expected_figures:
                add_issue(errors, "figure-count", "Embedded drawing count differs from expectation", expected=args.expected_figures, actual=metrics["drawings"])
            if args.expected_zotero_items is not None and metrics["zotero_item_fields"] != args.expected_zotero_items:
                add_issue(errors, "zotero-item-count", "Zotero item-field count differs from expectation", expected=args.expected_zotero_items, actual=metrics["zotero_item_fields"])

            if args.require_zotero:
                if metrics["zotero_item_fields"] < 1:
                    add_issue(errors, "zotero-items", "No ZOTERO_ITEM fields were found")
                if metrics["zotero_bibliography_fields"] < 1:
                    add_issue(errors, "zotero-bibliography", "No ZOTERO_BIBL field was found")
                if metrics["zotero_preferences_fields"] < 1:
                    add_issue(errors, "zotero-preferences", "No ZOTERO_PREFS field was found")

            fonts: set[str] = set()
            colors: set[str] = set()
            for name in names:
                if name not in {"word/document.xml", "word/styles.xml", "word/numbering.xml"}:
                    continue
                try:
                    part = ET.fromstring(archive.read(name))
                except Exception:  # noqa: BLE001
                    continue
                for node in part.iter():
                    for attr_name, value in node.attrib.items():
                        local = attr_name.rsplit("}", 1)[-1]
                        if local in {"ascii", "hAnsi", "eastAsia", "cs"} and value:
                            fonts.add(value)
                        if node.tag.rsplit("}", 1)[-1] == "color" and local == "val" and value:
                            colors.add(value)
            metrics["declared_fonts"] = sorted(fonts)
            metrics["declared_colors"] = sorted(colors)
            if args.expected_font and args.expected_font.casefold() not in {font.casefold() for font in fonts}:
                add_issue(errors, "font", "Expected font is absent from OOXML declarations", expected=args.expected_font, actual=sorted(fonts))

            media = [name for name in names if name.startswith("word/media/") and not name.endswith("/")]
            metrics["media_files"] = media
            if metrics["drawings"] and not media:
                add_issue(warnings, "media", "Drawings exist but no word/media files were found")

    except zipfile.BadZipFile as exc:
        add_issue(errors, "bad-zip", "File is not a valid DOCX ZIP container", error=str(exc))

    return {
        "status": "fail" if errors else "pass",
        "docx": str(path),
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }


def main() -> int:
    args = parse_args()
    report = audit(args)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        Path(args.json_out).write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
