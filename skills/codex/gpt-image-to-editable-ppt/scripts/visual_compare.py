from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def load_image(path: Path):
    return np.asarray(Image.open(path).convert("RGB").resize((512, 288), Image.Resampling.LANCZOS), dtype=np.float32)


def score_images(a_path: Path, b_path: Path):
    a = load_image(a_path)
    b = load_image(b_path)
    mae = float(np.mean(np.abs(a - b)) / 255.0)
    base = max(0.0, 1.0 - mae)
    ag = np.asarray(Image.fromarray(a.astype(np.uint8)).convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    bg = np.asarray(Image.fromarray(b.astype(np.uint8)).convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    edge_mae = float(np.mean(np.abs(ag - bg)) / 255.0)
    edge = max(0.0, 1.0 - edge_mae)
    return {"score": round(base * 0.7 + edge * 0.3, 4), "pixel_similarity": round(base, 4), "edge_similarity": round(edge, 4)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--rendered", required=True)
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--report")
    args = parser.parse_args()

    target = Path(args.target)
    rendered = Path(args.rendered)
    if target.is_file() and rendered.is_file():
        pairs = [(target, rendered)]
    else:
        target_files = sorted(target.glob("*.png"))
        rendered_files = sorted(rendered.glob("*.png"))
        pairs = list(zip(target_files, rendered_files))
    results = []
    for a, b in pairs:
        result = score_images(a, b)
        result.update({"target": str(a), "rendered": str(b)})
        results.append(result)
    average = round(sum(r["score"] for r in results) / len(results), 4) if results else 0.0
    passed = args.threshold is None or average >= args.threshold
    report = {"average_score": average, "threshold": args.threshold, "passed": passed, "pairs": results}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    print(text)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
