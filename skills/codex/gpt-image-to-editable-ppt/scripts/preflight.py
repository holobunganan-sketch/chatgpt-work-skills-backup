from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path

REQUIRED_MODULES = {
    "pptx": "python-pptx",
    "PIL": "Pillow",
    "yaml": "PyYAML",
    "jsonschema": "jsonschema",
    "lxml": "lxml",
    "numpy": "numpy",
    "fitz": "PyMuPDF",
}


def find_font() -> dict:
    candidates = []
    system = platform.system().lower()
    if system == "windows":
        font_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        candidates.extend([font_dir / "msyh.ttc", font_dir / "msyhbd.ttc", font_dir / "msyhl.ttc"])
    elif system == "darwin":
        candidates.extend([Path("/System/Library/Fonts/PingFang.ttc"), Path("/Library/Fonts/Microsoft YaHei.ttf")])
    else:
        for root in [Path("/usr/share/fonts"), Path.home() / ".fonts", Path.home() / ".local/share/fonts"]:
            if root.exists():
                candidates.extend(root.rglob("*YaHei*"))
                candidates.extend(root.rglob("msyh*"))
    existing = [str(p) for p in candidates if p.exists()]
    return {"requested": "Microsoft YaHei", "found": bool(existing), "paths": existing[:10]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    packages = {}
    missing = []
    for module, package in REQUIRED_MODULES.items():
        ok = importlib.util.find_spec(module) is not None
        packages[package] = ok
        if not ok:
            missing.append(package)

    renderer = shutil.which("soffice") or shutil.which("libreoffice")
    if platform.system().lower() == "windows" and not renderer:
        for guess in [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "LibreOffice/program/soffice.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "LibreOffice/program/soffice.exe",
        ]:
            if guess.exists():
                renderer = str(guess)
                break

    result = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
        "missing_packages": missing,
        "renderer": renderer,
        "font": find_font(),
        "can_build": not missing,
        "can_render_with_libreoffice": bool(renderer),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
