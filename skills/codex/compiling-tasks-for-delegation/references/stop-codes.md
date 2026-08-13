# Stop Codes

Use stable stop codes so a capable model can resume from the exact failure point.

| Code | Meaning |
|---|---|
| `E01-CONTEXT-UNAVAILABLE` | Required current-state context cannot be read. |
| `E02-ENVIRONMENT-MISMATCH` | Observed environment invalidates a compiled assumption. |
| `E03-MISSING-INPUT` | Required file, value, source, or artifact is absent. |
| `E04-PERMISSION-DENIED` | Required permission is unavailable. |
| `E05-TOOL-UNAVAILABLE` | Required tool or named fallback is unavailable. |
| `E06-DEPENDENCY-MISSING` | Required dependency, script, package, or prerequisite is absent. |
| `E07-UNEXPECTED-STATE` | Current state does not match any defined branch. |
| `E08-UNEXPECTED-OUTPUT` | Tool output does not match a defined result class. |
| `E09-VALIDATION-FAILED` | A step-level validation failed. |
| `E10-ACCEPTANCE-FAILED` | Final acceptance criteria were not met. |
| `E11-CONFLICTING-EVIDENCE` | Evidence sources conflict materially. |
| `E12-SCOPE-CHANGE` | Required action would exceed approved scope. |
| `E13-DESTRUCTIVE-ACTION` | A destructive or hard-to-reverse action lacks a completed gate. |
| `E14-CREDENTIALS-REQUIRED` | Execution needs credentials that are not already available through an authorized mechanism. |
| `E15-EXTERNAL-SIDE-EFFECT` | An unplanned external write, send, publish, purchase, deletion, or state change is required. |
| `E16-DECISION-REQUIRED` | A material choice remains undefined. |
| `E17-AMBIGUOUS-INSTRUCTION` | Two or more interpretations would change the result. |
| `E18-HIGH-STAKES-JUDGMENT` | A consequential expert judgment is still required. |
| `E19-SECURITY-BOUNDARY` | Execution would cross an undefined security or trust boundary. |
| `E20-NETWORK-FAILURE` | Required external access failed and no defined retry/fallback remains. |
| `E21-USER-AUTHORIZATION-REQUIRED` | A specifically user-controlled authorization is required before proceeding. |

## Escalation payload

When stopping, report exactly:

```markdown
## STOPPED

Code: E16-DECISION-REQUIRED
Step: STEP 19

### Expected
<state described by the package>

### Observed
<actual state>

### Evidence
<minimal supporting evidence>

### Why execution cannot continue
<one concrete unresolved decision or violated condition>

### Last safe completed step
STEP 18

### No further action taken
Confirmed.
```

Do not continue into later steps after a stop code unless the package explicitly defines a safe independent branch.
