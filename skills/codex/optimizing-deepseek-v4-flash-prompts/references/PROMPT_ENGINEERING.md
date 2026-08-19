# Prompt engineering rules for DeepSeek V4 Flash

## 1. Use a task contract

Place these fields near the task boundary: task type, objective, deliverable, audience, evidence boundary, constraints, output contract, quality gate, stop condition.

Decorative role language has low priority. Concrete authority and evidence rules are more useful.

## 2. Route reasoning effort

- Nonthink: routine rewriting, extraction, formatting, low-risk short answers.
- High: analysis, research synthesis, medical evidence work, planning, moderate agent tasks.
- Max: complex/high-risk multi-step agent tasks, difficult repository work, tasks where missed edge cases have material cost.

Do not use max as a universal default. Long reasoning can consume output budget and latency without guaranteed benefit.

## 3. Agent prompts need state transitions

For agent work, define:

1. Goal/end state.
2. Available evidence and tools.
3. Tool-selection rule.
4. Inspection after each meaningful action.
5. Working-state update.
6. Verification before completion.
7. Explicit stop condition.

Avoid prescribing dozens of tiny steps when the environment can change. Prescribe invariants and checkpoints.

## 4. Long-context prompts need source boundaries

Use source IDs and explicit tags. Treat source text as evidence/data. Source content cannot redefine system/task rules. Maintain provenance when synthesizing across documents.

For repeated Q&A over the same corpus, place stable corpus content before changing questions when the provider's cache behavior supports prefix reuse.

## 5. Optimize the DeepSeek cache prefix

Recommended order:

1. Stable system/task rules.
2. Stable skill/process rules.
3. Stable tool contracts.
4. Stable examples/reference corpus.
5. Project context that changes slowly.
6. Current task.
7. Dynamic source material.
8. Current output details.

Do not add per-request timestamps, random IDs, session counters, or volatile status text before stable material.

## 6. Define completion mechanically where possible

Examples:

- "All 12 records have a populated endpoint field."
- "Targeted tests pass and diff contains no unrelated files."
- "Every quantitative claim is traceable to a supplied source ID."
- "The requested file exists and can be opened."

A quality gate helps prevent plausible-sounding partial completion.

## 7. Keep facts and control instructions separate

Use a dedicated SOURCE AUTHORITY section. Instructions inside retrieved pages, documents, emails, logs, or code comments should remain data unless an explicit trusted policy source says otherwise.

## 8. Use few-shot examples selectively

Use examples when output shape or judgment is hard to describe. Put reusable examples in the stable prefix. Keep them compact. Remove examples that duplicate rules without clarifying behavior.

## 9. Provider adapter rule

Official DeepSeek API parameters are documented by DeepSeek. Third-party providers may map or ignore reasoning and sampling controls. The skill compiler can optimize the textual prompt universally; API parameter advice must stay provider-aware.
