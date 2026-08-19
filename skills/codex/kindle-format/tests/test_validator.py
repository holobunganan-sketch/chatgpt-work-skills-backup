from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_kindle_html.py"
FIXTURES = ROOT / "tests" / "fixtures"


def run_validator(name: str):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(FIXTURES / name)],
        capture_output=True,
        text=True,
    )


def test_good_document_passes():
    result = run_validator("good.html")
    assert result.returncode == 0, result.stdout + result.stderr


def test_bad_document_fails_for_kindle_hostile_patterns():
    result = run_validator("bad.html")
    assert result.returncode != 0
    output = (result.stdout + result.stderr).lower()
    for expected in ["script", "position: fixed", "css grid", "fixed pixel width", "wide table"]:
        assert expected in output, output
