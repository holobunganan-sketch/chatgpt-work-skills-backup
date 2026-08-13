# Template replication

When the user provides a `.pptx` template:

1. Analyze the original file with `scripts/analyze_template.py`.
2. Build from that same file so the package retains slide masters, theme, layouts, embedded media, and recurring elements.
3. Preserve existing example slides until analysis is complete. Remove them only when the final build begins and the user does not ask to retain them.
4. Select layouts by semantic role and layout name. Prefer a template layout that already matches cover, agenda, section, content, or closing.
5. Extract and reuse theme colors, theme fonts, title/body positions, divider styles, recurring decorations, footer, page numbering, and image treatments.
6. Apply user overrides property by property. Do not discard the rest of the template because one property was changed.
7. When a template contains custom fonts unavailable on the host, warn the user and use an explicitly approved substitute. Do not silently substitute.
8. Render representative pages and compare them with template examples for spacing, hierarchy, color, and recurring elements.

## Limitations

Python libraries can preserve an existing template package and add slides through its layouts. They cannot reliably infer every design intention from arbitrary slide content. Complex custom animations, SmartArt internals, linked Excel objects, macros, and proprietary add-in objects may require PowerPoint itself and manual review.
