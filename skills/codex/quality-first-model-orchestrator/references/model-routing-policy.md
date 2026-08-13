# Model Routing Policy

## Runtime discovery

Use `scripts/discover_models.py` to query Codex App Server `model/list`. The normalized catalog includes model id, display name, supported reasoning efforts, input modalities, hidden status, default status, and upgrade metadata when supplied by the client.

The catalog confirms availability and declared capabilities. It does not prove domain quality, writing quality, reliability, or remaining quota.

## Conservative registry

`scripts/build_model_registry.py` applies conservative family rules:

- Spark and other speed-specialist variants: L0–L1 bounded work
- Nano-class variants: L0 only
- Mini or Luna-class variants: L0–L1 bounded work
- Terra, full GPT-5.4, GPT-5.5, and frontier-class variants: eligible for L2 when the task traits match and independent review exists
- GPT-5.3 Codex-class variants: L2 for coding work, L1 ceiling for non-code work unless a stronger runtime-specific evaluation is added
- Unknown models: probation, L0 only

These ceilings are protective defaults. Local history may lower a ceiling after repeated failures. Local history never raises a ceiling automatically.

## Candidate filtering

A subagent candidate must satisfy every item:

- present in the runtime catalog;
- available and permitted by probation status;
- risk ceiling at or above the task risk;
- task category included in allowed categories;
- all required input modalities supported;
- all required traits present;
- reasoning effort supported;
- no task-specific exclusion.

When no candidate remains, assign the task to the main agent.

## Tie-breakers after the quality gate

Use these soft preferences in order:

1. A non-main model when it passes the same hard gate
2. Lower current-plan usage to diversify independent failure modes
3. Higher efficiency
4. Larger quality margin

Model diversity is useful only among qualified candidates. Do not allocate one task to every available model by default.

## Reasoning effort

- L0: low when supported
- L1: medium when supported
- L2: high or the strongest supported setting appropriate to the task
- L3: selected and executed by the current main agent

A higher reasoning setting cannot repair a model-task mismatch. Choose another model or keep the task with the main agent.

## Hot replacement

A model can be selected when a subagent is spawned or between completed turns. Do not attempt to change the model in the middle of an active generation. Stop or finish the current turn, preserve verified evidence, then spawn a replacement with the upgraded model.

## Project history

`record_outcome.py` stores only:

- model id;
- task category and risk;
- pass or fail;
- repair count;
- validation failure count;
- timestamp.

Do not store prompts, source text, output content, filenames, personal data, or confidential project details in model history.
