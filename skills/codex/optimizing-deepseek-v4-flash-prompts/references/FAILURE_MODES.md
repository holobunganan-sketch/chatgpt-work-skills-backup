# Failure modes and mitigations

| Failure mode | Symptom | Mitigation |
|---|---|---|
| Max-everywhere | High latency, huge reasoning, little quality gain on routine work | Route nonthink/high/max by risk and complexity |
| Completion without evidence | Agent says a change/search/test is done without observable proof | Require action evidence and end-state verification |
| Endless agent loop | Repeated tool calls after deliverable is already satisfied | Add explicit stop condition and working-state update |
| Long-context provenance loss | Correct-looking synthesis with unclear source origin | Source IDs, evidence map, claim-to-source check |
| Source instruction leakage | Retrieved/source text changes task behavior | SOURCE AUTHORITY boundary; source text is data |
| Cache fragmentation | Low cache hit despite repeated large context | Stable prefix first; remove volatile fields from prefix |
| Prompt over-specification | Brittle task execution when environment differs | Specify invariants/checkpoints; allow local planning |
| Weak output contract | Useful analysis returned in unusable form | State destination, format, length, audience, acceptance checks |
