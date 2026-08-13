# Quality gates

## Hard failures

- PPTX cannot be opened.
- A native text run is below the resolved minimum font size.
- An object extends beyond the slide canvas.
- A standard content slide lacks the upper-left page title or full-width divider.
- A whole-slide raster image is used without explicit image-deck mode.
- A substantive slide lacks `key_message` or `logic_type`.
- The user supplied a template but the final deck was not built from it.
- Text, numerical values, chart labels, or table content were reconstructed from generated imagery.

## Repair rules

- Too much text: shorten, group, visualize, or split the slide. Do not shrink below 14 pt.
- Low occupancy: enlarge the main visual structure, rebalance blocks, or use a more suitable layout. Do not add decorative clutter.
- High occupancy: simplify or split.
- Harmful overlap: reposition or resize. Deliberate containment is allowed when the text belongs to the shape.
- Template mismatch: rebuild from the template, use the correct layout, and restore recurring elements.
- Font missing: report the missing font and use an approved fallback only after user instruction or an explicit fallback rule.

## Visual comparison

A GPT Image composition is a design reference. Use visual comparison to detect large differences in balance, region allocation, and dominant structure. Do not require pixel equality between an artistic reference and a native slide. Pixel-level comparison is suitable only when the target image was rendered from a known structured specification.
