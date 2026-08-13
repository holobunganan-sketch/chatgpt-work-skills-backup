# Examples

## Example 1: Graphic-Led Deck Build

### User Request Pattern

"根据这份零散素材，帮我做一个面向医院管理层的 12 页汇报，先把逻辑理顺。"

### Expected Handling

1. Route to `Full Deck Generation` with `Structure-First Mode`.
2. Extract audience, objective, and source completeness.
3. Test each section for graphic-first eligibility.
4. Build an argument-page sequence instead of default agenda/issue/roadmap pages.
5. Produce blueprint for key slides before any final page drafting.

### Expected Output Shape

- central presentation claim
- 10-12 argument-page sequence
- graphic-first page type per slide
- blueprint for high-value slides
- flagged missing facts

## Example 2: Graphic-First Mechanism Slide

### User Request Pattern

"我要一页机制解释图，讲清楚 A 如何经过三步影响 B，再导致 C。先别急着出整页，先告诉我怎么排。"

### Expected Handling

1. Route to `Single-Slide Generation` with `Graphic-First Mode`.
2. Choose a graphic-led page type such as `Multi-Stage Path Page`.
3. Choose `Pathway Chain` or `Multi-Stage Flow`.
4. Produce blueprint.
5. State SVG scope and native PPT scope separately.

### Expected Output Shape

- one-sentence core message
- page blueprint
- graphic module choice
- `what_must_be_seen_first`
- `information_loss_if_text_only`
- SVG scope: nodes, arrows, checkpoints
- native PPT scope: title, side explanation, takeaway, references
- `待用户确认` markers for uncertain steps
