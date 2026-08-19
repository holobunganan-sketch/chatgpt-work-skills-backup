# MiMo-V2.5 model profile

Verified: 2026-08-18.

## Properties relevant to prompt design

1. MiMo-V2.5 is a sparse MoE model with about 310B total parameters and about 15B activated parameters per token. Its language backbone uses hybrid sliding-window and full attention.
2. The released MiMo-V2.5 supports up to a 1M-token context window.
3. Xiaomi describes MiMo-V2.5 as a native multimodal model with text, image, video, and audio understanding.
4. Post-training includes SFT, large-scale agentic RL, and Multi-Teacher On-Policy Distillation (MOPD), with emphasis on agentic execution.
5. Xiaomi's API documentation exposes cache-hit pricing and documents cache behavior. For repeated requests, stable-prefix design is economically relevant.
6. In thinking/tool-use conversations, Xiaomi documents preserving `reasoning_content` in relevant multi-round histories. This is an API integration rule; do not attempt to recreate private reasoning in prompt text.

## Prompt implications

- Define goal and completion state clearly; MiMo has enough agentic training to plan within a bounded stage.
- Avoid unnecessary micro-steps. Use phase-level workflow plus quality gates.
- 1M context is capacity, not information architecture. Use source IDs, source maps, explicit priority, and version labels.
- Keep stable system rules before volatile project state when using a provider that reuses prompt prefixes.
- Tool-using agents should update state after each tool result and check completion independently from tool invocation count.

## Official sources

- XiaomiMiMo model card: https://huggingface.co/XiaomiMiMo/MiMo-V2.5
- Xiaomi MiMo-V2.5 model page: https://mimo.mi.com/models/zh-CN/mimo-v2.5
- Xiaomi model quick start: https://mimo.mi.com/docs/en-US/quick-start/model
- Xiaomi reasoning-content guide: https://mimo.mi.com/docs/usage-guide/passing-back-reasoning_content

Treat provider-specific limits, prices, cache rules, and API fields as time-sensitive. Re-check official documentation before changing integration logic.
