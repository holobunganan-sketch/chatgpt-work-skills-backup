# kindle-format

A reusable agent skill for controlling the structure and presentation of Kindle-first long-form HTML.

## Files

- `SKILL.md` — agent-facing trigger and operating contract.
- `references/kindle-html-rules.md` — detailed formatting rules.
- `templates/kindle-reflowable.html` — standalone HTML baseline.
- `scripts/validate_kindle_html.py` — lightweight static validator.
- `tests/` — contract tests, validator tests, and behavior scenarios.

## Install

Copy the entire `kindle-format` directory into the skills directory used by your agent runtime. Keep the directory name and `name: kindle-format` frontmatter unchanged.

## Validate an HTML manuscript

```bash
python scripts/validate_kindle_html.py manuscript.html
```

The validator returns a non-zero exit code when Kindle-hostile errors are found.
