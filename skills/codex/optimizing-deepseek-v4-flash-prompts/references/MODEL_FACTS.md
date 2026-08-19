# DeepSeek V4 Flash model facts used by this skill

Reviewed: 2026-08-18.

## Release target

The prompt rules target the current DeepSeek V4 Flash family and use `DeepSeek-V4-Flash-0731` as the behavioral reference release. DeepSeek describes 0731 as the official release that superseded the preview and substantially enhanced agentic capabilities.

## Architecture and context

The V4 preview technical report/model card describes V4 Flash as a Mixture-of-Experts model with 284B total parameters and 13B activated parameters, using hybrid Compressed Sparse Attention (CSA) + Heavily Compressed Attention (HCA), Manifold-Constrained Hyper-Connections (mHC), and a 1M-token context window. The V4 series was pretrained on more than 32T tokens and post-trained using domain-specific expert cultivation followed by unified on-policy distillation.

Practical prompt implication: state the task domain, objective, evidence boundary and deliverable explicitly. This is a prompt-engineering choice aligned with the model's domain-specialized post-training; it is not a claim that prompts directly control MoE expert routing.

## Reasoning controls

The current official API exposes thinking on/off and `reasoning_effort` values `high` and `max`. Compatibility mappings send low/medium to high and xhigh to max. For the 0731 local model card, DeepSeek recommends temperature 1.0 and top_p 0.95 for agentic scenarios, top_p 1.0 otherwise. DeepSeek recommends a large output budget for high/max in local serving and documents a maximum API output of 384K tokens.

Prompt implication: route reasoning. Use non-thinking for routine low-risk work, high for most analytical work, and max for complex/high-risk agentic work. Max is a scarce deliberation budget and should not be hard-coded globally.

## Agent behavior

The 0731 model card reports large gains on terminal, tool-use and code-agent benchmarks. DeepSeek evaluated public code-agent tasks with a minimal DeepSeek Harness configuration using max reasoning effort.

Prompt implication: use goal/state/tool/verification/stop-condition contracts. Give the model room to select the next justified action. Enforce evidence-based completion claims.

## Cache behavior

DeepSeek's official API enables disk context caching by default. Reuse depends on fully matching cached prefix units. The API exposes `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens`.

Prompt implication: put stable instructions, stable skill rules and repeatedly queried documents first. Put current task details and volatile data after the reusable prefix. Avoid timestamps/request IDs in the reusable prefix.

## Primary sources

- DeepSeek official Hugging Face model card: deepseek-ai/DeepSeek-V4-Flash-0731
- DeepSeek V4 technical report/model card: deepseek-ai/DeepSeek-V4-Flash
- DeepSeek API Docs: Create Chat Completion
- DeepSeek API Docs: Models & Pricing
- DeepSeek API Docs: Context Caching
- DeepSeek API Docs: Pi integration example for DeepSeek V4
