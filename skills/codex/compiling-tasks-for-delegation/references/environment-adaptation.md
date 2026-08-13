# Environment Adaptation

The platform-independent task contract must be translated into instructions that match the executor's real environment.

## Inspect these dimensions when relevant

- operating system and shell;
- working directory and path syntax;
- repository and branch state;
- available CLI tools and versions;
- connected apps, MCP servers, plugins, or APIs;
- file formats and available artifact tools;
- authentication and permission scope;
- network availability;
- runtime limits and sandbox restrictions;
- current date/time or external state when freshness matters.

## Adaptation rules

1. Name the exact tool or command the executor should use.
2. Use observed paths, refs, IDs, and versions. Do not invent them.
3. If an operation can be done through multiple tools, choose one and encode the reason only when the choice affects reliability.
4. Keep fallbacks explicit. Example: primary tool unavailable -> use named fallback; fallback unavailable -> stop with `E05-TOOL-UNAVAILABLE`.
5. Preserve platform independence in `TASK.md`; put environment-specific instructions in `CONTEXT.md`, `STEPS.md`, or the single-file Environment section.
6. Credentials and secrets must never be copied into the package. Record only the required permission or account identity.
7. If the executor environment is unknown, make environment discovery the first conditional step or classify environment-specific actions as `CONDITIONAL`.

## Environment mismatch rule

If the observed environment contradicts an assumption that changes commands, file targets, compatibility, permissions, or safety, stop with `E02-ENVIRONMENT-MISMATCH`. Include the expected state, observed state, and evidence. Do not silently rewrite the plan during execution.
