from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(command, allow_failure=False):
    print("+", " ".join(str(c) for c in command))
    result = subprocess.run(command)
    if result.returncode and not allow_failure:
        raise SystemExit(result.returncode)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--template")
    parser.add_argument("--overrides")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    profile = work / "template_profile.json"
    resolved = work / "resolved_design_system.yaml"
    spec_report = work / "slide_spec_validation.json"
    ppt_report = work / "ppt_validation.json"

    if args.template:
        run([py, str(root / "scripts/analyze_template.py"), "--template", args.template, "--out", str(profile)])
    command = [py, str(root / "scripts/resolve_design_system.py"), "--defaults", str(root / "assets/default_design_system.yaml"), "--out", str(resolved)]
    if args.template:
        command += ["--template-profile", str(profile)]
    if args.overrides:
        command += ["--overrides", args.overrides]
    run(command)

    run([py, str(root / "scripts/validate_slide_spec.py"), "--spec", args.spec, "--schema", str(root / "schemas/deck_spec.schema.json"), "--design", str(resolved), "--report", str(spec_report)])
    command = [py, str(root / "scripts/build_ppt.py"), "--spec", args.spec, "--design", str(resolved), "--output", args.output]
    if args.template:
        command += ["--template", args.template]
    run(command)
    run([py, str(root / "scripts/validate_ppt.py"), "--pptx", args.output, "--design", str(resolved), "--spec", args.spec, "--report", str(ppt_report)])

    render_status = "not_requested"
    if args.render:
        rc = run([py, str(root / "scripts/render_ppt.py"), "--input", args.output, "--outdir", str(work / "rendered")], allow_failure=True)
        render_status = "success" if rc == 0 else "renderer_unavailable_or_failed"

    summary = {
        "output": str(Path(args.output).resolve()),
        "resolved_design": str(resolved),
        "spec_report": str(spec_report),
        "ppt_report": str(ppt_report),
        "render_status": render_status,
    }
    (work / "pipeline_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
