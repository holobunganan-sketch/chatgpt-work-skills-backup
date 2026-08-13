# GPT Image isolated asset prompt

Generate one isolated visual asset for a PowerPoint slide.

- Purpose: {{asset_purpose}}
- Visual subject: {{visual_subject}}
- Style: {{style}}
- Palette: {{palette}}
- Canvas: {{canvas_width}} × {{canvas_height}}
- Intended placement: {{placement}}
- Required empty area: {{empty_area}}
- Background: transparent when supported; otherwise solid {{background_color}}

Mandatory exclusions:

- no words, letters, numbers, symbols, labels, axes, legends, captions, logos, UI text, or watermarks;
- no fake charts, fake tables, fake citations, or decorative pseudo-text;
- no full-slide frame unless the asset is explicitly a background;
- do not place important details outside the intended placement region.

The final PowerPoint will add all text, numbers, diagrams, tables, and charts as native editable objects.
