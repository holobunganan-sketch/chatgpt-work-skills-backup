from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
INTERNAL_PATTERNS = [
    (r"internal[-_ ]evidence[-_ ]alignment", "internal evidence map"),
    (r"\bupstream_anchor\b|Upstream Anchor", "upstream reasoning field"),
    (r"\bmissing_relation\b|Missing Relation", "missing-relation field"),
    (r"\bdownstream_advance\b|Downstream Advance", "downstream reasoning field"),
    (r"\badaptation_instruction\b|Adaptation Instruction", "adaptation field"),
    (r"mainline[- ]fit|argument[- ]fit|evidence[- ]fit score", "fit score"),
    (r"主线契合度(?:评估|评分)?", "主线契合度评估"),
    (r"上下文承接(?:评估|检查|评分)", "上下文承接评估"),
    (r"论证递进(?:评估|检查|评分)", "论证递进评估"),
    (r"内部证据对齐|内部文献对齐", "内部证据对齐"),
    (r"纳入[／/、和与 ]*排除理由|排除理由", "内部纳入或排除理由"),
    (r"连续性检查结果|语气连续性评估", "连续性评估"),
    (r"我评估了每篇文献|经过内部评估|we evaluated each source", "评估过程说明"),
]


def read_docx_text(path: Path) -> str:
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Invalid DOCX package: {path}")
    with zipfile.ZipFile(path, "r") as archive:
        data = archive.read("word/document.xml")
    root = ElementTree.fromstring(data)
    texts = [
        node.text or ""
        for node in root.iter(f"{{{W_NS}}}t")
    ]
    return "\n".join(texts)


def read_text(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        return read_docx_text(path)
    raise ValueError("Supported formats: .md, .txt, .docx")


def audit(path: Path) -> dict:
    text = read_text(path)
    issues: list[dict] = []
    for pattern, label in INTERNAL_PATTERNS:
        matches = list(re.finditer(pattern, text, flags=re.I))
        for match in matches:
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 70)
            excerpt = " ".join(text[start:end].split())
            issues.append(
                {
                    "severity": "error",
                    "code": "INTERNAL_ALIGNMENT_LEAK",
                    "message": f"Detected {label}.",
                    "excerpt": excerpt,
                }
            )
    return {
        "status": "pass" if not issues else "fail",
        "source_pack": str(path.resolve()),
        "counts": {"errors": len(issues)},
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that internal evidence-alignment reasoning is absent."
    )
    parser.add_argument("source_pack", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        report = audit(args.source_pack)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
