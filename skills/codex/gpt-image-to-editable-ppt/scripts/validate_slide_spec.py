from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from common import load_data, occupancy_ratio, rect_intersection

LOGIC_TYPES = {
    "single_conclusion", "comparison", "process", "timeline", "hierarchy", "cause_effect",
    "problem_solution", "matrix", "cycle", "evidence_chain", "before_after", "spatial_structure"
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()

    spec = load_data(args.spec)
    schema = load_data(args.schema)
    design = load_data(args.design)
    errors = []
    warnings = []

    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(spec), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in err.path)
        errors.append({"code": "schema", "location": location, "message": err.message})

    slide_cfg = design.get("slide", {})
    sw = float(slide_cfg.get("width_in", 13.333333))
    sh = float(slide_cfg.get("height_in", 7.5))
    min_font = float(design.get("typography", {}).get("minimum_font_size_pt", 14))
    density = design.get("layout_density", {})
    min_occ = float(density.get("minimum_occupancy", 0.50))
    max_occ = float(density.get("maximum_occupancy", 0.86))
    mode = spec.get("deck", {}).get("delivery_mode", "hybrid")

    for index, slide in enumerate(spec.get("slides", []), start=1):
        sid = slide.get("id", index)
        page_type = slide.get("page_type")
        if page_type == "content":
            if not slide.get("key_message", "").strip():
                errors.append({"code": "missing_key_message", "slide": sid})
            if slide.get("logic_type") not in LOGIC_TYPES:
                errors.append({"code": "invalid_logic_type", "slide": sid})
        rects = []
        text_area = 0.0
        full_slide_images = 0
        elements = sorted(slide.get("elements", []), key=lambda e: e.get("z", 0))
        for element in elements:
            eid = element.get("id", "?")
            x, y, w, h = [float(element.get(k, 0)) for k in ("x", "y", "w", "h")]
            if x < 0 or y < 0 or x + w > sw + 0.01 or y + h > sh + 0.01:
                errors.append({"code": "out_of_bounds", "slide": sid, "element": eid, "box": [x, y, w, h]})
            if element.get("type") == "text":
                fs = float(element.get("font_size_pt", design.get("typography", {}).get("body_font_size_pt", 18)))
                if fs < min_font:
                    errors.append({"code": "font_too_small", "slide": sid, "element": eid, "font_size_pt": fs})
                text_area += w * h
            if element.get("type") == "image" and w * h >= sw * sh * 0.92:
                full_slide_images += 1
            if element.get("type") != "line":
                rects.append((x, y, w, h))

        if full_slide_images and mode != "image":
            errors.append({"code": "full_slide_raster_forbidden", "slide": sid})

        occ = occupancy_ratio(rects, sw, sh)
        if page_type == "content" and occ < min_occ:
            warnings.append({"code": "low_occupancy", "slide": sid, "value": round(occ, 3), "minimum": min_occ})
        if occ > max_occ:
            warnings.append({"code": "high_occupancy", "slide": sid, "value": round(occ, 3), "maximum": max_occ})
        if text_area / (sw * sh) > float(density.get("maximum_text_area_ratio", 0.48)):
            warnings.append({"code": "text_area_high", "slide": sid, "ratio": round(text_area / (sw * sh), 3)})

        for i, a in enumerate(elements):
            if a.get("allow_overlap") or a.get("type") == "line":
                continue
            ar = (a.get("x", 0), a.get("y", 0), a.get("x", 0) + a.get("w", 0), a.get("y", 0) + a.get("h", 0))
            aa = max(1e-9, a.get("w", 0) * a.get("h", 0))
            for b in elements[i + 1:]:
                if b.get("allow_overlap") or b.get("type") == "line":
                    continue
                br = (b.get("x", 0), b.get("y", 0), b.get("x", 0) + b.get("w", 0), b.get("y", 0) + b.get("h", 0))
                ba = max(1e-9, b.get("w", 0) * b.get("h", 0))
                overlap = rect_intersection(ar, br)
                if overlap / min(aa, ba) > 0.25:
                    warnings.append({"code": "possible_overlap", "slide": sid, "elements": [a.get("id"), b.get("id")], "ratio": round(overlap / min(aa, ba), 3)})

    report = {"valid": not errors, "errors": errors, "warnings": warnings}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    print(text)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
