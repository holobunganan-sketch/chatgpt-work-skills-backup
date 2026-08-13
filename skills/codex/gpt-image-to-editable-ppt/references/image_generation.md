# Image generation integration

Use the image-generation capability exposed by the host when available. This avoids requiring the user to configure a separate API key.

When the host does not expose image generation and `OPENAI_API_KEY` is available, install `requirements-image-api.txt` and run `scripts/generate_image_asset.py`.

Default API model: `gpt-image-2`.

## Asset generation

- Use a landscape size that matches the intended asset region. A full-slide visual reference can use `2048x1152` or another valid 16:9 size.
- Use `quality=medium` for working drafts and `quality=high` for final hero assets when justified.
- GPT Image 2 currently produces opaque or automatic backgrounds. Request a plain white background for assets that will be masked locally, or use another supported model only when the user explicitly accepts that dependency.
- Never ask the image model to render authoritative text, numerical data, labels, tables, charts, citations, or references.
- Save the exact prompt and output file path in the asset manifest.

## API command

```bash
python -m pip install -r <SKILL_ROOT>/requirements-image-api.txt
python <SKILL_ROOT>/scripts/generate_image_asset.py \
  --prompt-file <PROMPT.txt> \
  --output <ASSET.png> \
  --size 2048x1152 \
  --quality medium
```
