# SVG conventions (diagrams that look “slide-native”)

Use SVG for flows, mechanisms, structures, relationships, and abstract diagrams where arrows/labels need precision.

## Style tokens (default)

- Background: white
- Text: `#111827` (near-black)
- Secondary: `#6B7280` (gray)
- Stroke: `#111827` for key lines, `#9CA3AF` for secondary
- Accent: user palette; fallback `#D32F2F` (red)
- Font: `Microsoft YaHei, 微软雅黑, sans-serif`
- Corner radius: 12 (cards), 10 (pills)
- Stroke width: 2 (primary), 1.5 (secondary)
- Arrowheads: simple triangle, consistent size

## Readability rules

- Minimum label size: 18px (prefer 20px+)
- Avoid diagonal text and crowded intersections
- Use whitespace to separate groups; do not rely on color alone
- Keep the diagram to 1 main message; split if multiple mechanisms exist

## Recommended SVG skeleton

When generating SVG, include:
- A `<defs>` section for arrow marker(s)
- Shared CSS in `<style>` for fonts/colors
- Grouping via `<g>` for modules/lanes

If a diagram requires precise alignment, use explicit coordinates and consistent spacing increments (e.g., 24/32/40px steps).

