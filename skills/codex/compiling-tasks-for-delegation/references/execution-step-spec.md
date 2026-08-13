# Execution Step Specification

Every executable step uses the following structure.

```markdown
### STEP 07 — Check the Windows build entry
Delegation: SAFE_TO_DELEGATE

#### Purpose
Confirm the existing Windows desktop build command before any build attempt.

#### Input
`package.json` in the repository root.

#### Action
1. Open `package.json`.
2. Read the `scripts` object.
3. Record scripts whose names or commands contain `build`, `desktop`, `windows`, or `tauri`.
4. Do not modify the file.

#### Expected Result
A list of existing candidate build commands with exact script names and command strings.

#### Evidence
Record the file path and the matching script entries verbatim.

#### Verdict
- PASS: at least one unambiguous Windows desktop build entry exists.
- STOP: no matching entry exists or multiple candidates require a material choice.

#### Exception Handling
- No candidate: `E06-DEPENDENCY-MISSING`.
- Multiple materially different candidates: `E16-DECISION-REQUIRED`.
```

## Atomicity rules

- One step should have one verifiable purpose.
- Number sub-actions when order matters.
- Name exact inputs, files, ranges, commands, query terms, or source locations.
- State mutation scope. If a step is read-only, say so.
- State what must remain unchanged when preservation matters.
- Give expected exit codes, counts, strings, file existence, schema shape, or other observable conditions when available.
- Repeat critical details when an executor may read a phase in isolation. Avoid "same as above" for required parameters.

## Hidden-decision test

Reject or rewrite a step if it contains an unresolved instruction such as:

- choose the best approach;
- fix related issues;
- clean up the code;
- use an appropriate method;
- improve the wording;
- review the results and proceed;
- handle errors as needed;
- optimize performance;
- search for relevant sources.

Each phrase is acceptable only when followed by a deterministic selection rule, bounded source scope, concrete target, or escalation branch.

## Branching rules

A branch condition must be observable. Each branch must point to a named next step, a defined retry, or a stop code. Do not use open-ended branches such as "otherwise investigate".
