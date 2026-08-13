# Delegation Policy

Assign one state to every executable unit.

## SAFE_TO_DELEGATE

Use only when all of the following are true:

- required inputs are identified or mechanically discoverable;
- the action is explicit and bounded;
- success and failure are observable;
- all material branches are defined;
- the executor does not need domain judgment that could change the outcome;
- the action is reversible or has already passed any required high-model/user authorization gate;
- the action stays within the user's approved scope.

Typical examples: read a named file, run a specified command, make an exact text replacement, populate a fixed template from supplied facts, collect defined metadata, run a defined test, compare output against a fixed criterion.

## CONDITIONAL

Use when delegation becomes safe after a mechanical gate. The package must state:

- the condition to test;
- how to test it;
- the exact PASS branch;
- the exact FAIL branch;
- a stop code if neither branch fits.

Example: "If `package.json` contains `build:windows`, run that script. If absent, stop with `E06-DEPENDENCY-MISSING`."

## HIGH_MODEL_REQUIRED

Use when execution still requires material reasoning, judgment, or authorization. Common triggers:

- multiple plausible interpretations change the final outcome;
- strategy, architecture, scientific interpretation, editorial judgment, or prioritization is still open;
- evidence conflicts or quality is uncertain in a consequential way;
- current context materially differs from the compiled specification;
- the action is destructive, externally consequential, or hard to reverse and lacks an already-authorized gate;
- permissions, credentials, identity, security boundaries, or external side effects require a judgment call;
- the executor would need to expand scope or change a user decision;
- the task enters a high-stakes medical, legal, financial, security, or safety judgment not fully specified by authoritative guidance;
- acceptance requires interpretation rather than a defined check.

`HIGH_MODEL_REQUIRED` is an escalation state. It does not mean the overall task is impossible.

## Local discretion budget

The executor may make only immaterial local choices, such as temporary variable names or equivalent command formatting, when the package explicitly permits them. Any choice that can alter scope, meaning, evidence, compatibility, safety, cost, external state, or deliverable quality requires a defined rule or escalation.
