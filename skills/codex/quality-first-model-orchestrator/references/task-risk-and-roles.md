# Task Risk and Roles

## Risk levels

| Level | Characteristics | Examples | Default owner |
|---|---|---|---|
| L0 | Mechanical, deterministic, easily checked | Formatting, fixed-field extraction, filename inventory, placeholder scan | Qualified fast subagent |
| L1 | Bounded interpretation with authoritative inputs and source recheck | PICO extraction, meeting action items, targeted bug fix, table-text reconciliation | Qualified efficient or specialist subagent |
| L2 | Multi-source synthesis, conflict handling, meaningful judgment | Evidence comparison, complex review, root-cause analysis, bounded strategy analysis | Strong subagent plus independent review, or main agent |
| L3 | Final or high-consequence decision requiring global context | Final medical conclusion, study design decision, legal interpretation, release approval, final manuscript or artifact | Current main agent |

The consequences of error can raise a task's level. A simple-looking task becomes L2 or L3 when a mistake is difficult to detect or materially harmful.

## Decomposition rules

A delegated task unit must have:

- one objective;
- authoritative inputs and excluded inputs;
- an output schema;
- acceptance criteria;
- verification method and owner;
- dependencies;
- explicit write set;
- escalation conditions.

Keep the following work whole unless a clear boundary exists:

- final narrative and argument structure;
- core research or system design;
- cross-document terminology decisions;
- decisions depending on several unresolved subtasks;
- final artifact assembly and publication.

## Role catalog

### Explorer

Maps files, sources, concepts, or execution paths. Read-only. Returns locations and evidence without proposing final decisions.

### Evidence extractor

Extracts specified fields from bounded sources. Every material value includes a source location. Uses `not reported` for absent data.

### Classifier or formatter

Applies a fixed taxonomy or transformation. Returns exceptions separately. Does not invent categories or content.

### Targeted worker

Performs a small, understood implementation or document change within an explicit write set. Runs targeted validation.

### Analyst

Compares bounded evidence and identifies conflicts. L2 analysis requires a strong model and independent verification.

### Reviewer

Checks an existing result against the quality contract and original inputs. Does not assume the producer's conclusions are correct.

### Adversarial reviewer

Searches for counterevidence, omissions, overreach, security problems, or regression risks. Returns actionable findings only.

### Integrator and final decider

Reserved for the current main agent. Resolves conflicts, restores global coherence, edits the final artifact, and owns delivery.
