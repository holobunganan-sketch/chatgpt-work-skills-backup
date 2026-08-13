# Section Boundary Rules

## Classification model

Classify every candidate statement before drafting:

| Code | Meaning | Destination |
|---|---|---|
| B | Established background or prior evidence | Introduction |
| P | Prespecified protocol, design, or analytical procedure | Methods |
| R | Fact learned by executing the study | Results |
| I | Interpretation through prior evidence | Discussion |
| D | Administrative, ethics, sharing, or disclosure statement | Declarations |

Use the pre-analysis test: if the sentence could not have been written before data processing or analysis, classify it as R.

## Methods permits

- Study design and intended analytical roles.
- Eligibility and exclusion rules.
- Outcome and predictor definitions.
- Prespecified transformations, coding, and missing-data procedures.
- Candidate-model or analysis-generation strategy.
- Prespecified comparison and selection criteria.
- Model-locking, update, and recalibration rules.
- Comparator construction.
- Performance and uncertainty methods.
- Software and settings fixed before execution.
- Ethics and reproducibility procedures.

Numeric procedural settings may remain in Methods only when they were fixed before execution and the publication profile allows them. Data-driven values belong in Results.

## Results requires

- Realized participant counts, events, exclusions, and follow-up.
- Observed completeness, missingness, and data dimensions.
- Actual feature-screening or candidate-search sizes when these describe executed analyses.
- Selected hyperparameters or tuning-path labels.
- Retained variables, coefficients, equations, and model size.
- Data-derived thresholds and their rounding effects.
- Group sizes and outcome distributions.
- Effect estimates, performance estimates, intervals, P values, rankings, and diagnostics.
- Actual resampling counts or evaluation ranges when the locked profile assigns implementation values to Results.

## High-precision examples

| Statement | Class | Reason |
|---|---|---|
| Candidate models were fitted with penalized regression. | P | Procedure known before analysis |
| Candidate models were compared by parsimony and discrimination. | P | Comparison rule |
| The selected mixing parameter was 0.25. | R | Data-driven selection output |
| Eligibility required a recorded outcome and required inputs. | P | Eligibility rule |
| A total of 312 participants met eligibility criteria. | R | Realized flow |
| Missing values were to be multiply imputed. | P | Prespecified handling |
| No missing values were observed. | R | Observed data property |
| Risk groups were defined by the development-score median. | P | Grouping rule |
| The resulting cutoff was 0.8164. | R | Data-derived value |
| Calibration was assessed graphically and by a slope. | P | Evaluation method |
| The calibration slope was 1.34. | R | Performance result |
| The result may reflect platform differences reported previously. | I | Literature-based interpretation |

## Ambiguous cases

### Sample size

Distinguish planned sample-size justification from realized sample size. Put the design calculation in Methods and the number actually analyzed in Results. Under a strict house profile, keep all realized cohort counts out of Methods even if a journal commonly permits duplication.

### Hyperparameters

Put the search strategy and prespecified grid definition in Methods. Put the value selected by tuning in Results. If a value was fixed before analysis, document that provenance and treat it as a method setting.

### Thresholds

Put a prespecified clinical threshold in Methods. Put a threshold estimated from the study data in Results. State the derivation rule in Methods and the realized value in Results.

### Missing data

Put the handling plan in Methods. Put actual missingness, exclusions, convergence, and resulting analysis counts in Results.

### Model equations

Put the generic calculation rule in Methods. Put fitted coefficients, baseline values, calibration constants, and the complete executable equation in Results or the model table.

## Boundary audit procedure

1. Extract abstract Methods and main Methods.
2. Search for study-specific result terms from the result-control ledger.
3. Search for high-precision result patterns: realized counts, selected/final values, estimates, intervals, and result verbs.
4. Review every numeric token manually unless it is documented as prespecified.
5. Move each misplaced statement to the matching Results subsection.
6. Recheck that no result was lost during the move.
7. Re-run the audit after citations, tables, and figures are inserted.

Use `scripts/audit_manuscript.py` for the deterministic portion. Treat its output as an audit aid, not a substitute for sentence-level scientific review.
