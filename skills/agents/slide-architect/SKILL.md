---
name: slide-architect
description: "Professional slide design + structured argumentation for medical communication, scientific research reporting, enterprise brand decks, consulting-style narratives, and infographic slides. Use when the user asks to create or rewrite a PPT/deck/slide outline, convert docs/notes/drafts/data into slide-by-slide pages, improve slide logic and readability, unify visual style, design charts/diagrams/infographics, or generate slide page code (HTML/CSS and SVG) and/or editable .pptx (often via the $slides skill). Enforces: one clear takeaway per slide, structure-first before layout, high readability (sizes/spacing/contrast), consistent style system, and no fabricated medical/scientific/policy/market data (mark missing sources as \"来源待补充\")."
---

# Slide Architect

## Overview

将用户的主题/主旨/资料转化为“可用于演示”的专业幻灯片：先提炼论证结构，再生成页面；每页只讲一个核心结论，用 2–4 个模块支撑，并输出可落地的页面蓝图（版式 + 文案 + 图表/示意图方案 + 来源区）。

## Workflow (always follow)

### 0) Intake: confirm the minimum brief (ask before generating)

Before producing any slides, check whether these are explicit:
- 主题 + 核心主旨（希望观众相信/记住的 1 句话）
- 目标受众（医学/科研/管理层/销售/公众等）与专业深度
- 使用场景（路演/学术报告/内部培训/会议口播；时长；是否现场讲解）
- 页数或页面范围（例如“只做 5 页：封面+目录+3 页正文”）
- 配色方案/品牌规范（含 logo/品牌名/页脚要求）
- 是否已有文案/数据/参考资料（以及是否允许你改写压缩）
- 是否需要参考文献区（是/否；格式偏好）
- 是否需要中英双语（是/否；是否逐页双语或分版本）
- 画面比例（未指定默认 16:9）
- 字体（未指定统一用微软雅黑）

Hard rule:
- If color/brand palette is not provided, you MUST ask for it first. If the user still does not specify after you ask once, use the default professional palette: white background + red accent + dark gray/black text + light gray secondary.

### 1) Structure first: extract the argument
Produce (briefly) one of these, depending on request size:
- 3–7 bullets “主线论证” (Claim → Reasons → Evidence → Implications), or
- A slide outline with 1 sentence takeaway per slide.

Rules:
- Never paste raw notes as-is. Rewrite into slide language (短句、要点、并列/递进/对比/因果结构).
- Title must be a clear judgment aligned with the takeaway; avoid vague titles.
- If user gives too much content for a slide, compress and/or split slides (do not cram).

### 2) Page planning: choose layout modules
For each slide, decide:
- 1 takeaway (single sentence)
- 2–4 supporting modules (cards/columns/sections)
- Visual plan: chart/diagram/table/flow/structure, or “no visual needed”

Preferred layouts:
- Left-right two-column
- Three-card columns
- Top-bottom sections
- Center visual + side explanations
- Chart/diagram + takeaway summary

See `references/layout-patterns.md` when you need a layout quickly.

### 3) Generate slide content (copy-ready)
For each slide output:
- Slide title (结论式标题)
- 2–4 modules with short bullets (each bullet ≤ 16–20 Chinese characters when possible)
- Emphasis: highlight keywords/numbers only (avoid rainbow)
- Footer sources area when the slide uses medical/research/policy/market claims
  - Never fabricate sources, studies, numbers, authors, or conclusions.
  - If sources are missing, mark: “来源待补充（请提供：机构/论文/报告/链接/年份）”.

### 4) Visuals: CSS for simple, SVG for complex
Default canvas assumptions (unless the user provides a different template):
- Ratio: 16:9
- Font: 微软雅黑
- Background: white
- Style: professional / restrained / brandable / infographic-friendly

Choose implementation:
- Use **CSS layout code** for normal text/table/cards and non-complex visuals.
- Use **SVG** for mechanisms, flows, structures, relationships, abstract diagrams, or anything that needs precise arrows/labels.

SVG requirements:
- Keep structure accurate and labels readable.
- Use consistent stroke width, arrow style, corner radius, and label hierarchy.
- SVG must serve the argument (no decorative complexity).

See `references/svg-conventions.md` for a ready-to-copy SVG style setup.

### 5) Credibility: evidence handling
When content touches medicine/clinical/research/policy/market:
- Do not infer missing numbers as facts.
- Separate “事实/数据” vs “判断/建议”.
- If evidence is uncertain, say so and request sources.

### 6) Final self-check (must do before sending)
For every slide:
- One takeaway only; all modules support it.
- Title is explicit and matches the takeaway.
- Text is not overloaded; hierarchy clear; spacing consistent.
- Color count controlled (≤ 3–5); contrast sufficient; accent used sparingly.
- Font统一：微软雅黑；比例默认 16:9。
- Data/sources: no fabrication; missing sources labeled “来源待补充”.

## Output formats (pick what the user needs)

### A) Outline first (default)
1) Task understanding (1–3 lines)  
2) Missing info questions (only what blocks quality; must ask for palette if missing)  
3) Slide outline: `#` slide title + 1 takeaway + 2–4 module headings  

### B) Slide-by-slide blueprint (recommended for production)
Use the blueprint template in `references/blueprint-template.md` to output a consistent per-slide spec.

### C) Build editable `.pptx`
If the user wants an actual PPT file, prefer using the `$slides` skill to generate a `.pptx` from the blueprint, while preserving the same structure/style rules in this skill.

## References
- `references/layout-patterns.md`: layout modules you can mix-and-match
- `references/blueprint-template.md`: strict slide blueprint format (copy-ready)
- `references/svg-conventions.md`: SVG styling rules for consistent diagrams
