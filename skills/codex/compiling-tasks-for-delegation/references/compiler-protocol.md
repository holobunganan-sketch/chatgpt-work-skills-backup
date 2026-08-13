# Compiler Protocol

Use this protocol to convert a raw request into a deterministic handoff.

## 1. Capture the contract

Extract and preserve:

- final goal;
- required deliverables and formats;
- explicit constraints and prohibited actions;
- already-made user decisions;
- deadlines, versions, branches, paths, identities, and environments when relevant;
- success criteria stated by the user;
- dependencies on files, connected sources, accounts, tools, or external state.

If the user's language leaves multiple materially different outcomes possible, resolve the ambiguity with available context. Ask the user only when the intended outcome cannot be established safely and no conservative default preserves intent. Do not make a material product, scientific, legal, financial, publishing, or architecture decision on the user's behalf without sufficient evidence.

## 2. Decide whether the scene must be inspected

Inspect live context before compilation whenever any of these can change the steps:

- current repository or branch state;
- existing files, schemas, document structure, or artifacts;
- installed tools, available connectors, permissions, credentials, or network access;
- current versions, APIs, laws, policies, schedules, prices, or public facts;
- previous work products that the task must extend;
- actual data shape, size, quality, or encoding.

Record only the context the executor needs. Keep irrelevant exploration out of the handoff.

## 3. Separate facts, decisions, and assumptions

Use three buckets:

- **Known facts:** directly observed or supplied.
- **Compiler decisions:** choices made by the capable model with rationale when the choice affects execution.
- **Assumptions:** low-risk defaults that can be verified or reversed. Attach a condition or stop branch when an assumption could fail.

Never convert an unknown into a fact.

## 4. Build the platform-independent task specification

Define:

- Goal
- Deliverables
- Scope
- Inputs
- Constraints
- Prohibitions
- Dependencies
- Decision log
- Delegation summary
- Acceptance criteria

This layer describes what must happen without depending on a particular shell, connector, agent product, or UI.

## 5. Adapt to the current environment

Map every abstract operation to a concrete tool, path, command, API action, file edit, or UI operation. Verify that the named capability exists. Read `environment-adaptation.md`.

## 6. Compile atomic execution steps

Use `execution-step-spec.md`. Remove verbs that hide decisions such as "handle", "fix", "clean up", "make appropriate", "optimize", "review as needed", "choose suitable", or "etc." unless the exact decision rule follows immediately.

## 7. Define exceptions before handoff

For every step, ask:

1. What result means PASS?
2. What known alternative result can occur?
3. What action is permitted for each alternative?
4. Which result requires escalation?

Use stop codes for escalation.

## 8. Define proof and acceptance

Each important result must have observable evidence. Final acceptance must be computable from that evidence where possible.

## 9. Simulate the executor

Mentally run the package from the first step. At each branch ask: "Can an executor with weaker reasoning select the next action without inventing a material decision?" If the answer is no, compilation is incomplete.
