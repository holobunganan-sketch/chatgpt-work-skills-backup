# MiMo-V2.5 prompt design rules

## 1. Task routing comes first

A high-value opening contains four fields:

- task type
- goal
- deliverable
- audience

This gives the model a compact task route before it sees large source material.

## 2. Use a task contract

Recommended order:

`TASK -> CONTEXT -> SOURCES -> PROFILE RULES -> WORKFLOW -> CONSTRAINTS -> OUTPUT -> QUALITY GATE -> CURRENT MATERIALS`

The compiler produces this order consistently.

## 3. Separate commands from evidence

Source documents can contain instructions, quotations, prompts, comments, and conflicting claims. The prompt must explicitly state that source material is information, not higher-priority instructions.

For evidence-sensitive work, assign identifiers such as `[S01]`, `[S02]`, `[GUIDE-2026]`. Stable IDs survive chunking and make cross-document synthesis auditable.

## 4. Control phases, not every thought

Good:

1. Understand task and evidence boundaries.
2. Extract relevant information and establish source map.
3. Analyze or execute.
4. Check against quality gate.
5. Output final deliverable.

Avoid instructions that prescribe dozens of tiny reasoning moves. They consume context and can make the model follow the checklist mechanically.

## 5. Write observable constraints

Weak: “尽量准确”“注意不要遗漏”“最好简洁”。

Strong: “所有数字必须来自提供材料；无法确认时标记‘材料未提供’。”“最终正文不超过800字。”“关键结论标记来源编号。”

The linter flags common weak forms.

## 6. Quality gates define completion

A quality gate should be testable from the output or sources. Common gates:

- all requested questions answered
- numbers checked against source
- fact and inference separated
- conflicting sources reported
- output format and length met
- no unsupported certainty

## 7. Long-context pattern

For large inputs:

1. Give every source a stable ID.
2. Create a source map before the raw materials.
3. Define priority by authority/version, never by context position.
4. Keep source IDs through chunks.
5. Resolve cross-source conflicts before synthesis.
6. Ask for final synthesis only after extraction is complete.

For medical long-context work, use the `medical` profile and add these long-context constraints; the evidence rules are higher risk than formatting rules.

## 8. Agent pattern

Define:

- desired end state
- allowed tools
- forbidden or irreversible actions
- state update rule after tool results
- failure/retry rule
- completion test

Avoid using “called a tool” as evidence that a task finished.

## 9. Cache-aware layout

Stable prefix:

`system_identity -> global_rules -> domain_rules -> workflow -> tool_rules -> output_standards -> quality_gate`

Semi-stable:

`project_context -> project_memory`

Variable suffix:

`project_state -> current_task -> current_materials -> current_constraints`

Use `cache-plan` to emit this layout. Provider-specific caching behavior can change; verify official docs when integrating API billing logic.

## 10. Role prompts

A concise professional role can provide domain context. Role praise does not substitute for task definition. Avoid phrases such as “世界顶级专家” when they add no operational constraint.
