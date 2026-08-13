# Quality Policy

## Hard priority order

1. Factual and functional correctness
2. Completeness against the user's request
3. Explicit user constraints
4. Safety, compliance, and evidence traceability
5. Cross-file and cross-section consistency
6. Usability of the final deliverable
7. Speed
8. Quota utilization and model diversity
9. Cost

Items 7–9 may influence a choice only after every candidate satisfies items 1–6.

## Quality contract

Create the contract before task decomposition:

```json
{
  "objective": "Single statement of the finished outcome",
  "required_deliverables": ["Concrete artifacts or answers"],
  "prohibited_outcomes": ["Failure states that invalidate the work"],
  "factual_requirements": ["Claims, values, definitions, and source rules"],
  "evidence_requirements": ["Source location and traceability rules"],
  "completeness_requirements": ["Required sections, cases, or files"],
  "consistency_requirements": ["Terms, numbers, versions, and interfaces"],
  "formatting_requirements": ["Required form and presentation"],
  "acceptance_criteria": ["Observable pass conditions"],
  "consequences_of_error": "low | medium | high | critical"
}
```

## Delegation gate

Delegate a unit only when all answers are yes:

- Is the objective unambiguous?
- Are the authoritative inputs identified?
- Can the output be bounded?
- Are acceptance criteria observable?
- Is an independent verification method available?
- Does a discovered model satisfy the capability ceiling, modality, category, and reasoning requirements?
- Can the result be integrated without losing global context?

A no answer keeps the unit with the main agent or requires redesign of the unit.

## Forbidden quality tradeoffs

- Assigning work merely because a model has unused quota
- Treating model version numbers as proof of capability
- Giving an unknown model open-ended or high-risk work
- Removing evidence requirements to fit a weaker model
- Accepting a subagent's self-evaluation as validation
- Skipping full integration review because all subtasks reported success
- Allowing parallel writers to edit the same file
- Reassigning a failed task to a weaker model

## Completion rule

The orchestration succeeds only when the final artifact passes the original quality contract. Subagent completion counts, speed, and model utilization are diagnostic metrics, not success criteria.
