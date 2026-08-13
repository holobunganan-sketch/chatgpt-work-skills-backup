# Installation in Codex

## User-wide installation

Extract the ZIP so this directory exists:

- Windows: `%USERPROFILE%\.agents\skills\gpt-image-to-editable-ppt\SKILL.md`
- macOS/Linux: `~/.agents/skills/gpt-image-to-editable-ppt/SKILL.md`

Restart Codex if the skill does not appear immediately. Invoke it explicitly with:

```text
$gpt-image-to-editable-ppt
```

## Repository installation

Place the skill directory at:

```text
<repository>/.agents/skills/gpt-image-to-editable-ppt/
```

## Dependencies

From the extracted skill folder:

```bash
python -m pip install -r requirements.txt
python scripts/self_test.py --workdir ./self-test-output
```

Rendering review requires LibreOffice or Microsoft PowerPoint. The skill can still build and structurally validate a PPTX without a renderer.
