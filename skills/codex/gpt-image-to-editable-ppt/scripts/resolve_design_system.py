from __future__ import annotations

import argparse
from pathlib import Path

from common import deep_merge, load_data, save_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve defaults, template design, and user overrides")
    parser.add_argument("--defaults", required=True)
    parser.add_argument("--template-profile")
    parser.add_argument("--overrides")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    resolved = load_data(args.defaults)
    provenance = {"defaults": str(Path(args.defaults).resolve())}

    if args.template_profile:
        profile = load_data(args.template_profile)
        template_design = profile.get("design_system", profile.get("design_overrides", {}))
        resolved = deep_merge(resolved, template_design)
        provenance["template_profile"] = str(Path(args.template_profile).resolve())

    if args.overrides:
        resolved = deep_merge(resolved, load_data(args.overrides))
        provenance["user_overrides"] = str(Path(args.overrides).resolve())

    resolved["_provenance"] = provenance
    save_data(args.out, resolved)
    print(f"Resolved design system: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
