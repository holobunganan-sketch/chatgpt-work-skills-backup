from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"


def test_skill_exists_and_has_required_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: kindle-format" in text
    assert "description: Use when" in text


def test_skill_declares_core_kindle_contract():
    text = SKILL.read_text(encoding="utf-8").lower()
    required = [
        "reflowable",
        "single-column",
        "semantic html",
        "relative units",
        "table",
        "image",
        "validator",
        "kindle-html-rules.md",
    ]
    for term in required:
        assert term in text, f"missing contract term: {term}"
