from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".svg"}


def issue(
    issues: list[dict],
    severity: str,
    code: str,
    message: str,
    location: str,
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            "location": location,
        }
    )


def audit(root: Path, minimum_dpi: int) -> dict:
    if not root.is_dir():
        raise NotADirectoryError(root)
    issues: list[dict] = []
    assets = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not assets:
        issue(
            issues,
            "warning",
            "NO_FIGURE_ASSETS",
            "目录中未发现图片资产。",
            str(root.resolve()),
        )

    inspected: list[dict] = []
    for path in assets:
        relative = str(path.relative_to(root))
        suffix = path.suffix.lower()
        record = {"path": relative, "format": suffix.lstrip(".").upper()}
        if suffix != ".png":
            issue(
                issues,
                "error",
                "FIGURE_FORMAT",
                "独立图片应保存为 PNG 格式。",
                relative,
            )
        try:
            with Image.open(path) as image:
                record["pixels"] = [image.width, image.height]
                dpi = image.info.get("dpi")
                if (
                    not dpi
                    or len(dpi) < 2
                    or min(float(dpi[0]), float(dpi[1])) < minimum_dpi - 1
                ):
                    issue(
                        issues,
                        "error",
                        "FIGURE_DPI",
                        f"图片分辨率应至少为 {minimum_dpi} dpi。",
                        relative,
                    )
                    record["dpi"] = list(dpi) if dpi else None
                else:
                    record["dpi"] = [round(float(dpi[0]), 2), round(float(dpi[1]), 2)]
        except (UnidentifiedImageError, OSError) as exc:
            issue(
                issues,
                "error",
                "FIGURE_UNREADABLE",
                f"图片无法读取：{exc}",
                relative,
            )
        inspected.append(record)

    errors = sum(item["severity"] == "error" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    return {
        "status": "pass" if errors == 0 else "fail",
        "directory": str(root.resolve()),
        "counts": {
            "assets": len(assets),
            "errors": errors,
            "warnings": warnings,
        },
        "assets": inspected,
        "issues": issues,
        "manual_review_required": [
            "all figure text is English",
            "academic color palette",
            "no title inside the canvas",
            "wide outer margins",
            "no clipped axes, legends or labels",
            "one complete figure per file",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit independent figure assets.")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--minimum-dpi", type=int, default=300)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        report = audit(args.directory, args.minimum_dpi)
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
