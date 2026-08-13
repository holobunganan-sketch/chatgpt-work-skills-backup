from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path


def find_soffice():
    path = shutil.which("soffice") or shutil.which("libreoffice")
    if path:
        return path
    if platform.system().lower() == "windows":
        guesses = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "LibreOffice/program/soffice.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "LibreOffice/program/soffice.exe",
        ]
        return next((str(p) for p in guesses if p.exists()), None)
    return None


def export_with_powerpoint(input_path: Path, pdf_path: Path) -> bool:
    if platform.system().lower() != "windows":
        return False
    try:
        import win32com.client  # type: ignore
    except ImportError:
        return False
    app = win32com.client.Dispatch("PowerPoint.Application")
    app.Visible = 1
    presentation = None
    try:
        presentation = app.Presentations.Open(str(input_path.resolve()), WithWindow=False)
        presentation.SaveAs(str(pdf_path.resolve()), 32)
        return pdf_path.exists()
    finally:
        if presentation is not None:
            presentation.Close()
        app.Quit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--dpi", type=int, default=144)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    pdf_path = outdir / f"{input_path.stem}.pdf"
    renderer = None

    soffice = find_soffice()
    if soffice:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(input_path)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            produced = Path(tmp) / f"{input_path.stem}.pdf"
            if not produced.exists():
                raise RuntimeError("LibreOffice did not produce a PDF")
            shutil.copy2(produced, pdf_path)
        renderer = "libreoffice"
    elif export_with_powerpoint(input_path, pdf_path):
        renderer = "powerpoint"
    else:
        raise RuntimeError("No renderer found. Install LibreOffice or use Microsoft PowerPoint with pywin32 on Windows.")

    import fitz
    document = fitz.open(pdf_path)
    zoom = args.dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    images = []
    for index, page in enumerate(document, start=1):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = outdir / f"slide-{index:03d}.png"
        pix.save(str(image_path))
        images.append(str(image_path))
    print(json.dumps({"renderer": renderer, "pdf": str(pdf_path), "images": images}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
