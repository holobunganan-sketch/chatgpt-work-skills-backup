---
name: medical-scientific-slides
description: Turn a topic, core message, outline, source material, draft, or data into formal presentation slides for medical communication, medical affairs updates, clinical study interpretation, academic communication, enterprise brand presentations, consulting-style narratives, infographic slides, and market or strategy reports. Use when the user asks to create, rewrite, structure, polish, or generate slide pages, slide outlines, deck plans, slide code, or editable presentation content that must be clear, restrained, evidence-aware, and suitable for formal presenting rather than poster or web-banner design. Also use when the user asks in Chinese for 医学传播, 医学事务汇报, 科研汇报, 临床研究解读, 学术汇报, 企业品牌宣讲, 咨询式汇报, 信息图式表达, 市场策略汇报, 幻灯片生成, PPT制作, 页面结构设计, 图表页, 机制图, 流程图, deck大纲, or 专业演示文稿改写与美化.
---

# Medical Scientific Slides

## Overview

Use this skill to convert raw inputs into structured, presentation-ready slide content with disciplined logic, restrained visual language, and formal professional tone. Optimize for one conclusion per slide, readable delivery in a live presentation, and layouts that can scale into a multi-slide deck.

## Workflow

Follow this sequence unless the user explicitly requests a narrower output.

1. Understand the communication task.
2. Check whether the minimum inputs are clear enough to proceed.
3. Reduce source material into slide logic.
4. Propose a slide outline when the scope is multi-slide or the input is dense.
5. Create a structured slide definition for each page before rendering.
6. Render the requested slide content, code, or deck-ready structure.
7. Run a self-check against clarity, evidence, and tone constraints.

## Check Inputs

Identify these inputs before generating slides:

- slide topic
- core message or desired conclusion
- target audience
- use case
- slide count or page scope
- available copy, draft, data, references, or source material
- citation/source requirement
- bilingual requirement
- logo, footer, or brand-name requirement
- brand color or visual guideline requirement

Ask follow-up questions only when missing information would materially change the result. Batch those questions into one message. If the user says to proceed directly and the missing detail has a safe default, continue with defaults.

Use these defaults when the user does not specify otherwise:

- aspect ratio: `16:9`
- font: `Microsoft YaHei`
- background: white
- headline and emphasis color: professional red
- body text: dark gray to black
- support color: light gray
- style direction: medical-report / consulting-report
- citation area: reserve a source area for any medical, clinical, policy, market, or research claim

If the user does not provide sources for evidence-based claims, mark the source area as `Source pending`.

## Build Slide Logic First

Do not paste raw material directly onto slides. Rewrite the material into presentation logic first.

For each slide, determine:

- the single conclusion
- the supporting evidence
- the needed comparison, process, hierarchy, or cause-effect relationship
- the minimum number of modules required to communicate it clearly

Prefer 2 to 4 supporting modules per slide. Split content across slides when density harms readability.

For multi-slide tasks, present an outline before full rendering. For each slide, give:

- slide title
- core conclusion
- recommended layout
- chart / SVG / CSS module need
- citation need

## Create Structured Slide Definitions

Before writing slide code or polished slide copy, form an internal structured object for each slide. Use this shape or an equivalent:

```json
{
  "slide_type": "evidence-summary",
  "slide_title": "Adult booster education shows a clear protection gap",
  "core_message": "Protection is not continuous across age bands, so hospital training should reinforce adult booster communication.",
  "content_blocks": [
    {
      "type": "summary",
      "title": "Key findings",
      "points": [
        "Childhood vaccination completion does not guarantee adult awareness of continued protection needs.",
        "Hospital training often emphasizes acute management over preventive communication."
      ]
    },
    {
      "type": "data-highlight",
      "title": "Communication focus",
      "points": [
        "Turn the age-band protection gap into a direct training risk message."
      ]
    }
  ],
  "chart_or_svg_need": "bar-chart",
  "citation_need": true,
  "layout_pattern": "chart-plus-conclusion"
}
```

Keep the representation stable across slides so the output can scale into a full deck.

For layout patterns, read [references/layout-patterns.md](./references/layout-patterns.md) when the page type is unclear.

## Render Slides

Render with templates and consistent design tokens instead of designing every slide from scratch.

Use CSS-first rendering for:

- two-column layouts
- card grids
- tables
- summary blocks
- chart captions
- standard text-image combinations

Use SVG-first rendering for:

- mechanisms
- pathways
- relationship maps
- structure diagrams
- multi-node logic
- flow diagrams that would look crude as plain boxes

If the information is too weak for a complex diagram, step down to a simpler layout instead of forcing a graphic.

## Write Slide Copy

Rewrite source material into slide-ready language.

Do:

- make the title specific and judgment-bearing
- compress long sentences
- convert description into argument
- organize content into parallel, progressive, comparative, causal, or hierarchical structures
- keep body copy short, modular, and easy to scan
- highlight key numbers and keywords visually

Do not:

- use vague titles such as `Background`, `Results`, `Related content`, or `Some findings`
- use chatbot phrasing
- use filler transitions
- write long article-style paragraphs
- introduce decorative copy unrelated to the conclusion

## Enforce Visual Rules

Keep the deck looking like a formal presentation, not a poster, webpage, or long infographic.

Use these baseline rules:

- one core conclusion per slide
- 3 to 5 colors per slide at most
- emphasis color only for key numbers, labels, lines, or conclusions
- stable typography, spacing, corner radius, line style, and citation style across the deck
- generous margins and consistent inter-module spacing
- readable contrast at presentation distance

Use this default type scale unless the user provides a style system:

- page title: `30-40px`
- secondary title: `20-28px`
- body: `16-22px`
- note / citation: `10-14px`

## Handle Evidence and Sources

Never fabricate:

- data
- study findings
- references
- policy claims
- market statistics

When the user provides insufficient sourcing, keep the content conditional and mark the source area as `Source pending`.

Reserve a citation or source area at the bottom of slides involving medical, clinical, academic, policy, or market claims.

## Self-Check Before Output

Verify all of the following:

- the slide expresses one conclusion only
- the title states a real judgment, not a vague topic
- the text volume is presentation-friendly
- the layout is not crowded
- the style is restrained and consistent
- the slide does not read like AI chat output
- charts and graphics serve the argument
- a source area exists when evidence is involved

## Output Pattern

Default output order:

1. task understanding
2. necessary follow-up questions, only if required
3. slide outline or structure recommendation
4. generated slide content

For a single slide or a very small page set, it is fine to output directly:

- slide title
- core conclusion
- recommended layout
- slide structure or slide code

## References

Read these only when needed:

- [references/layout-patterns.md](./references/layout-patterns.md): approved slide patterns, use cases, and page-selection rules
- [references/rendering-spec.md](./references/rendering-spec.md): engineering constraints for structured objects, tokens, CSS/SVG consistency, and deck extensibility
