---
name: gpt-image-to-editable-ppt
description: Create highly editable PowerPoint decks from structured content, GPT Image visual references or isolated visual assets, and optional user-supplied PPTX templates. Use for AI-generated PPTs, image-to-editable-PPT recreation, template-faithful decks, Chinese 16:9 presentations, or workflows that require native text, shapes, charts, tables, render review, and quality gates. Do not flatten full slides into images unless the user explicitly requests an image-only deck.
---

# GPT Image to Editable PowerPoint

Create a finished `.pptx` whose content and logic remain editable. Treat the structured slide specification as the source of truth. Treat GPT Image output as a visual reference or an isolated asset, never as the authoritative source for text, data, geometry, or object structure.

## Resolve the skill root

The skill root is the directory containing this `SKILL.md`. Resolve it before invoking scripts. Use absolute paths when running scripts from another project.

## Mandatory workflow

1. Inspect all user materials and identify the required output, audience, slide count, language, aspect ratio, template, and requested colors.
2. Run `scripts/preflight.py`. Record missing fonts, Python packages, rendering software, and template limitations.
3. When a PPTX template is supplied, run `scripts/analyze_template.py` before outlining slides. Preserve its masters, layouts, theme, recurring decorations, footer, and geometry by building from the original template.
4. Resolve design settings with `scripts/resolve_design_system.py` using this precedence for each property:
   - explicit user instruction;
   - extracted template property;
   - `assets/default_design_system.yaml`;
   - local layout choice.
5. Build a logical outline. Every substantive slide must have one key message and one declared logic type. Do not create a bullet dump.
6. Create a complete deck specification conforming to `schemas/deck_spec.schema.json`. Give every native element an explicit type, position, size, style, and z-order.
7. Create GPT Image prompts from `prompts/gpt_image_asset_prompt.md` or `prompts/gpt_image_reference_prompt.md`. Use the host image-generation capability when available. When it is unavailable and `OPENAI_API_KEY` is configured, use `scripts/generate_image_asset.py`:
   - generate text-free, isolated assets whenever possible;
   - keep titles, body text, numbers, charts, tables, axes, labels, legends, citations, and page furniture out of generated images;
   - full-page images are references only and must not be inserted as the finished slide.
8. Run `scripts/validate_slide_spec.py`. Repair all hard failures before building.
9. Build the PPTX with `scripts/build_ppt.py`. Native PowerPoint objects are mandatory for all text, numbers, basic shapes, connectors, tables, and data charts.
10. Run `scripts/validate_ppt.py`. Repair hard failures.
11. Render the PPTX with `scripts/render_ppt.py` when LibreOffice or Microsoft PowerPoint is available. Inspect every slide image. Use `scripts/visual_compare.py` only as supporting evidence; a GPT Image reference is not expected to be pixel-identical to the native slide.
12. Repeat build, validate, render, and repair until all hard gates pass.
13. Deliver the PPTX, the resolved design system, the final deck specification, and a brief QA report. Do not expose internal prompts or temporary files unless requested.

## Default design rules

Apply these only when the user or template does not specify the property:

- 16:9 slide size.
- White background on every slide.
- Microsoft YaHei for all text.
- Black text.
- Preferred line spacing: 1.5.
- Minimum font size: 14 pt. Never solve overflow by reducing below 14 pt.
- Standard content-slide title: upper-left, left aligned.
- A horizontal divider spans the content width between the title and body on standard content slides.
- Cover, agenda, section-divider, and closing slides are exempt from the standard title-divider layout.
- Use the unified palette in `assets/default_design_system.yaml` unless the user requests colors.
- Distribute content across the usable canvas. Avoid large accidental empty regions and avoid crowding. Split a slide when required.
- Present relationships, hierarchy, process, comparison, evidence, time, causality, or architecture visually. Slides are not paragraphs placed on a canvas.

## Native editability requirements

Use native PowerPoint objects for:

- all titles, body copy, numbers, labels, footnotes, and citations;
- rectangles, rounded rectangles, circles, arrows, connectors, and dividers;
- tables;
- charts and their underlying data;
- simple diagrams and timelines.

Raster or SVG assets are allowed for photographs, illustrations, textures, complex artistic compositions, maps, and icons that cannot be represented efficiently as native shapes. Do not rasterize a whole slide in the default workflow.

## Template handling

Read `references/template_replication.md` whenever a template is supplied. Start from the actual PPTX file. Do not imitate a template from screenshots when the original PPTX is available. A template instruction from the user can override specific template properties while all unaffected properties remain inherited.

## Logic types

Use one of these as the primary logic type for each substantive slide:

`single_conclusion`, `comparison`, `process`, `timeline`, `hierarchy`, `cause_effect`, `problem_solution`, `matrix`, `cycle`, `evidence_chain`, `before_after`, `spatial_structure`.

Read `references/presentation_architecture.md` before converting an outline into slide specifications.

## Hard gates

A deck must not be released when any of the following is true:

- missing or corrupted PPTX;
- any text below 14 pt without an explicit user exception;
- unrequested non-black text under the default design system;
- objects outside the slide canvas;
- missing standard title or divider on a standard content slide;
- full-slide raster image used as the finished slide without explicit user approval;
- missing key message or logic type;
- unresolved text overflow, harmful overlap, or unreadable contrast;
- user template supplied but not analyzed or preserved;
- numerical or textual content copied from generated imagery instead of the source specification.

## Commands

Install Python dependencies when needed:

```bash
python -m pip install -r <SKILL_ROOT>/requirements.txt
```

Run the self-test:

```bash
python <SKILL_ROOT>/scripts/self_test.py --workdir <OUTPUT_DIR>
```

Run a normal local pipeline:

```bash
python <SKILL_ROOT>/scripts/run_pipeline.py \
  --spec <DECK_SPEC.json> \
  --output <OUTPUT.pptx> \
  --workdir <WORK_DIR> \
  [--template <TEMPLATE.pptx>] \
  [--overrides <USER_OVERRIDES.yaml>]
```

Read `references/image_generation.md` before calling an image API. Read `references/quality_gates.md` when diagnosing validation failures.
