from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    output = work / "sample-output.pptx"
    command = [
        sys.executable, str(root / "scripts/run_pipeline.py"),
        "--spec", str(root / "examples/sample_deck.json"),
        "--output", str(output),
        "--workdir", str(work),
    ]
    result = subprocess.run(command)
    if result.returncode:
        return result.returncode
    print(f"Self-test passed: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
