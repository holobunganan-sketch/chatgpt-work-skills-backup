# Task Packets

## Task manifest

Use this minimal shape for routing:

```json
{
  "version": 1,
  "domain": "code | non-code | mixed",
  "main_model_id": "optional exact current model id",
  "tasks": [
    {
      "id": "unique-id",
      "role": "evidence-extractor",
      "category": "extraction",
      "risk": "L1",
      "allow_delegation": true,
      "critical_output": false,
      "required_modalities": ["text"],
      "required_traits": ["structured-output", "source-traceability"],
      "forbidden_models": []
    }
  ]
}
```

## Full task packet

Every spawned agent receives these fields in clear prose or structured form:

```json
{
  "task_id": "unique-id",
  "role": "narrow role",
  "objective": "one finished outcome",
  "context_summary": "only context needed for this unit",
  "authoritative_inputs": ["files, sources, prior verified outputs"],
  "excluded_inputs": ["material that must not influence the task"],
  "allowed_actions": ["read, analyze, edit named files, run named checks"],
  "forbidden_actions": ["scope expansion, inference, external writes"],
  "output_schema": "exact fields and order",
  "acceptance_criteria": ["observable pass conditions"],
  "verification_requirements": ["evidence and checks to return"],
  "stop_conditions": ["conditions requiring escalation"],
  "write_set": ["exclusive files or artifacts"],
  "dependencies": ["verified prerequisite task ids"]
}
```

## Prompt adaptation

### Fast specialist, mini, or probationary model

Use a narrow, stepwise packet:

1. State one objective.
2. Name every allowed source.
3. List fields to produce in order.
4. Require source locations for every claim.
5. Use `not reported` or `cannot determine` for missing information.
6. Prohibit synthesis beyond the specified source set.
7. Define a stop condition for ambiguity or conflict.

### Balanced or strong model

Provide the quality contract subset, relevant context manifest, comparison dimensions, known uncertainties, and an explicit review method. Keep final decisions with the main agent.

### Reviewer

Give the original quality contract and original inputs. Ask for independent checking. Do not provide hidden chain-of-thought or ask the reviewer to approve the producer's reasoning style.

## Required result shape

```json
{
  "task_id": "unique-id",
  "status": "complete | blocked | failed",
  "findings": [],
  "evidence": [],
  "inputs_used": [],
  "files_modified": [],
  "validation_performed": [],
  "assumptions": [],
  "uncertainties": [],
  "unresolved_issues": [],
  "confidence": "low | medium | high"
}
```

Confidence is metadata for triage. It does not replace verification.

## Orchestration plan

Before spawning, combine the quality contract, full tasks, selected assignments, reasoning efforts, verification owners, dependencies, write sets, escalation rules, and final gate. Validate it with `validate_orchestration_plan.py`.
