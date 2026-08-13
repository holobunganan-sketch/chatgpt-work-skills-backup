from __future__ import annotations

import argparse
import copy
import zipfile
from pathlib import Path
from typing import Any, Iterable

from lxml import etree

try:
    from .workflow_common import cli_result, issue
except ImportError:
    from workflow_common import cli_result, issue


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
XML_PART_SUFFIXES = (".xml", ".rels")


def _read_package(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path, "r") as archive:
        return {
            name: archive.read(name)
            for name in archive.namelist()
            if name.startswith("word/")
            or name.startswith("customXml/")
            or name.startswith("_rels/")
            or name == "[Content_Types].xml"
        }


def _parse(data: bytes) -> etree._Element:
    return etree.fromstring(data, parser=etree.XMLParser(remove_blank_text=False, resolve_entities=False))


def _strip_highlight(root: etree._Element) -> etree._Element:
    normalized = copy.deepcopy(root)
    for highlight in normalized.xpath(".//w:highlight", namespaces=NS):
        parent = highlight.getparent()
        parent.remove(highlight)
        if parent.tag == f"{{{W_NS}}}rPr" and len(parent) == 0 and not parent.attrib and not (parent.text or "").strip():
            grandparent = parent.getparent()
            if grandparent is not None:
                grandparent.remove(parent)
    return normalized


def _canonical(element: etree._Element) -> bytes:
    return etree.tostring(element, method="c14n", exclusive=False, with_comments=False)


def _normalized_xml(data: bytes) -> bytes:
    return _canonical(_strip_highlight(_parse(data)))


def _node_signatures(root: etree._Element, xpath: str) -> tuple[bytes, ...]:
    return tuple(_canonical(node) for node in root.xpath(xpath, namespaces=NS))


def _visible_text_signature(root: etree._Element) -> tuple[str, ...]:
    values: list[str] = []
    for node in root.iter():
        if node.tag == f"{{{W_NS}}}t":
            values.append(node.text or "")
        elif node.tag == f"{{{W_NS}}}tab":
            values.append("\t")
        elif node.tag in {f"{{{W_NS}}}br", f"{{{W_NS}}}cr"}:
            values.append("\n")
    return tuple(values)


def _highlight_values(package: dict[str, bytes]) -> list[str]:
    values: list[str] = []
    for name, data in package.items():
        if not name.endswith(".xml"):
            continue
        try:
            root = _parse(data)
        except etree.XMLSyntaxError:
            continue
        for node in root.xpath(".//w:highlight", namespaces=NS):
            values.append(node.get(f"{{{W_NS}}}val", ""))
    return values


def _different_members(clean: dict[str, bytes], highlighted: dict[str, bytes]) -> set[str]:
    names = set(clean) | set(highlighted)
    differences: set[str] = set()
    for name in names:
        if name not in clean or name not in highlighted:
            differences.add(name)
            continue
        clean_data = clean[name]
        highlighted_data = highlighted[name]
        if name.endswith(XML_PART_SUFFIXES):
            try:
                clean_data = _normalized_xml(clean_data)
                highlighted_data = _normalized_xml(highlighted_data)
            except etree.XMLSyntaxError:
                pass
        if clean_data != highlighted_data:
            differences.add(name)
    return differences


def compare_variants(clean_path: Path, highlighted_path: Path) -> list[dict[str, Any]]:
    clean_path = Path(clean_path)
    highlighted_path = Path(highlighted_path)
    issues: list[dict[str, Any]] = []
    try:
        clean_package = _read_package(clean_path)
        highlighted_package = _read_package(highlighted_path)
    except (FileNotFoundError, zipfile.BadZipFile) as exc:
        return [issue("invalid_docx", f"Unable to read DOCX package: {exc}", "manuscript_variants")]

    clean_highlights = _highlight_values(clean_package)
    highlighted_highlights = _highlight_values(highlighted_package)
    if clean_highlights:
        issues.append(issue("clean_contains_highlight", "Clean manuscript must not contain revision highlights.", str(clean_path), colors=clean_highlights))
    invalid_colors = sorted({value for value in highlighted_highlights if value.lower() != "yellow"})
    if invalid_colors:
        issues.append(issue("invalid_highlight_color", "Highlighted manuscript may use yellow revision highlights only.", str(highlighted_path), colors=invalid_colors))

    document_name = "word/document.xml"
    if document_name not in clean_package or document_name not in highlighted_package:
        issues.append(issue("missing_document_xml", "Both DOCX files must contain word/document.xml.", document_name))
        return issues

    clean_root = _strip_highlight(_parse(clean_package[document_name]))
    highlighted_root = _strip_highlight(_parse(highlighted_package[document_name]))
    comparisons: list[tuple[str, str, Any, Any]] = [
        (
            "visible_text_mismatch",
            "Visible manuscript text differs after highlight normalization.",
            _visible_text_signature(clean_root),
            _visible_text_signature(highlighted_root),
        ),
        (
            "style_mismatch",
            "Paragraph, run, or table style structures differ.",
            _node_signatures(clean_root, ".//w:pPr | .//w:rPr | .//w:tblPr"),
            _node_signatures(highlighted_root, ".//w:pPr | .//w:rPr | .//w:tblPr"),
        ),
        (
            "field_mismatch",
            "Word field structures differ.",
            _node_signatures(clean_root, ".//w:fldChar | .//w:instrText | .//w:fldSimple"),
            _node_signatures(highlighted_root, ".//w:fldChar | .//w:instrText | .//w:fldSimple"),
        ),
        (
            "bookmark_mismatch",
            "Bookmark structures differ.",
            _node_signatures(clean_root, ".//w:bookmarkStart | .//w:bookmarkEnd"),
            _node_signatures(highlighted_root, ".//w:bookmarkStart | .//w:bookmarkEnd"),
        ),
        (
            "drawing_mismatch",
            "Drawing structures differ.",
            _node_signatures(clean_root, ".//w:drawing | .//w:pict"),
            _node_signatures(highlighted_root, ".//w:drawing | .//w:pict"),
        ),
        (
            "table_mismatch",
            "Table structures or contents differ.",
            _node_signatures(clean_root, ".//w:tbl"),
            _node_signatures(highlighted_root, ".//w:tbl"),
        ),
    ]
    for code, message, clean_value, highlighted_value in comparisons:
        if clean_value != highlighted_value:
            issues.append(issue(code, message, document_name))

    different_members = _different_members(clean_package, highlighted_package)
    media_differences = sorted(name for name in different_members if name.startswith("word/media/"))
    relationship_differences = sorted(name for name in different_members if name.endswith(".rels"))
    custom_xml_differences = sorted(name for name in different_members if name.startswith("customXml/"))
    if media_differences or relationship_differences:
        if not any(item["code"] == "drawing_mismatch" for item in issues):
            issues.append(
                issue(
                    "drawing_mismatch",
                    "Embedded drawing media or relationships differ.",
                    "word/",
                    members=media_differences + relationship_differences,
                )
            )
    if custom_xml_differences:
        issues.append(
            issue(
                "custom_xml_mismatch",
                "Custom XML citation or document data differs between manuscript variants.",
                "customXml/",
                members=custom_xml_differences,
            )
        )
    classified = {document_name, *media_differences, *relationship_differences, *custom_xml_differences}
    unclassified = sorted(different_members - classified)
    if unclassified:
        issues.append(issue("word_package_mismatch", "Word package parts differ outside the allowed highlight layer.", "word/", members=unclassified))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Clean and Highlighted manuscript DOCX variants.")
    parser.add_argument("clean")
    parser.add_argument("highlighted")
    args = parser.parse_args()
    return cli_result(compare_variants(Path(args.clean), Path(args.highlighted)))


if __name__ == "__main__":
    raise SystemExit(main())
