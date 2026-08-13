from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a GPT Image asset with the OpenAI Images API")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt")
    group.add_argument("--prompt-file")
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--size", default="2048x1152")
    parser.add_argument("--quality", choices=["low", "medium", "high", "auto"], default="medium")
    parser.add_argument("--background", choices=["opaque", "auto", "transparent"], default="auto")
    parser.add_argument("--metadata")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured")
    if args.model.startswith("gpt-image-2") and args.background == "transparent":
        raise ValueError("gpt-image-2 does not support transparent backgrounds; use opaque/auto or a host image tool that supports transparency")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install requirements-image-api.txt before using this script") from exc

    prompt = args.prompt if args.prompt is not None else Path(args.prompt_file).read_text(encoding="utf-8")
    client = OpenAI()
    result = client.images.generate(
        model=args.model,
        prompt=prompt,
        size=args.size,
        quality=args.quality,
        background=args.background,
        output_format="png",
    )
    if not result.data or not result.data[0].b64_json:
        raise RuntimeError("Image API returned no image data")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(result.data[0].b64_json))
    metadata = {
        "model": args.model,
        "size": args.size,
        "quality": args.quality,
        "background": args.background,
        "output": str(output.resolve()),
        "prompt_file": str(Path(args.prompt_file).resolve()) if args.prompt_file else None,
    }
    metadata_path = Path(args.metadata) if args.metadata else output.with_suffix(output.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
