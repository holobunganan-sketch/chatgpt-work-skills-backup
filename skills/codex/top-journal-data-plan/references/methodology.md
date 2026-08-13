# Detailed Methodology Reference

Use this reference when a user needs a deep, top-journal-level data processing or analysis plan. Do not output this reference verbatim. Select the relevant parts for the user's problem.

## 1. Foundational Positioning

Treat data analysis as evidence engineering from a real-world system to an actionable conclusion. Start from the system, not the dataset.

Define three systems:

- Target system: the real population, process, institution, market, platform, or environment the conclusion should apply to.
- Observation system: the mechanism that records data, including instruments, platforms, forms, sensors, logs, coding rules, or human reporting.
- Action system: the decision context in which results will be used, such as screening, surveillance, resource allocation, policy evaluation, risk communication, product decision, workflow triage, or regulatory oversight.

Mismatch among these systems is the main source of invalid inference. Make the mismatch explicit and decide whether weighting, standardization, restriction, linkage, external validation, or sensitivity analysis can reduce the risk.

## 2. Question Classes and Matching Methods

### Descriptive Surveillance

Use when the question is "what is the burden, distribution, trend, or monitored signal?"

Methods: rates, proportions, means, medians, standardized estimates, age/sex/region standardization, survey weights, post-stratification, spatial smoothing, temporal smoothing, Bayesian hierarchical estimates, age-period-cohort analysis, trend decomposition.

Evaluate: denominator quality, sampling coverage, measurement consistency, reporting delay, time comparability, uncertainty intervals, subgroup coverage, missingness.

Interpretation: observed burden is not necessarily true burden if detection, reporting, or denominator quality changes.

### Association and Risk-Factor Analysis

Use when the question is "which variables are associated with an outcome?"

Methods: generalized linear models, generalized additive models, Cox models, mixed-effects models, multilevel models, sparse regression, Bayesian regression, stratified and interaction models.

Evaluate: confounding structure, variable timing, overadjustment, collider control, clustering, nonlinearities, subgroup heterogeneity, missingness, influence points.

Interpretation: association does not imply causation. Variable importance, regression coefficient size, or statistical significance does not prove intervention value.

### Causal Effect Estimation

Use when the question is "what would happen if an exposure or intervention changed?"

Start with target trial emulation:

- Eligibility
- Treatment or exposure strategies
- Assignment time or time zero
- Follow-up window
- Outcome definition
- Causal contrast
- Analysis plan

Methods: matching, propensity score weighting, inverse probability weighting, standardization/g-formula, doubly robust estimation, marginal structural models, difference-in-differences, interrupted time series, synthetic control, regression discontinuity, instrumental variables, negative controls.

Evaluate: exchangeability, positivity, consistency, time ordering, balance, parallel trends, discontinuity assumptions, instrument validity, spillover, sensitivity to unmeasured confounding.

Interpretation: tie every causal claim to population, exposure definition, comparator, time window, and assumptions.

### Prediction, Screening, and Risk Stratification

Use when the question is "who is likely to have or develop an outcome?"

Methods: logistic regression, penalized regression, survival models, risk scores, random forests, gradient boosting, neural networks, text models, image models, multimodal models.

Data construction:

- Define time zero.
- Define feature window before prediction time.
- Define prediction horizon.
- Avoid label leakage and post-outcome variables.
- Separate development, internal validation, temporal validation, and external validation.

Evaluate: discrimination, calibration, calibration-in-the-large, calibration slope, sensitivity, specificity, PPV, NPV, threshold-specific workload, decision curve analysis, external validation, temporal validation, subgroup performance, drift.

Interpretation: prediction explains model use of information, not causes. Feature importance and SHAP values are not causal effects.

### Dynamic Modeling and Scenario Analysis

Use when the question is "how does the system evolve over time, and how would timing or intensity change outcomes?"

Methods: time series, state-space models, epidemic or process models, compartmental models, cohort state-transition models, agent-based models, simulation, scenario analysis.

Evaluate: lag structure, reporting delay, parameter identifiability, back-testing, sensitivity to assumptions, scenario robustness, intervention timing, feedback behavior.

Interpretation: distinguish forecast from scenario. Scenario analysis answers "under these assumptions", not "this will happen."

### Implementation and Governance

Use when the question is "can this method work in the real world?"

Methods: external validation, prospective validation, pragmatic evaluation, A/B testing, interrupted deployment evaluation, model monitoring, human-in-the-loop evaluation, workflow assessment, fairness audit, privacy impact assessment.

Evaluate: usability, workflow fit, cost, time-to-result, accountability, explainability, data drift, model drift, subgroup harm, privacy, auditability.

Interpretation: statistical validity is not implementation validity.

## 3. Data Generation Audit

Audit seven mechanisms for every plan.

### Entry Mechanism

Who enters the dataset? Does entry depend on exposure, outcome, risk, behavior, access, willingness, platform activity, clinician ordering, policy, or device ownership?

Common methods: sampling weights, inverse probability weighting, post-stratification, restriction, external benchmark comparison, sensitivity analysis.

### Measurement Mechanism

Is each variable a direct measurement or a proxy? Does measurement error vary by subgroup or time?

Common methods: validation subsample, gold-standard comparison, repeated measures, alternative definitions, misclassification sensitivity analysis.

### Time Mechanism

Are exposure, covariates, labels, and outcomes temporally ordered? Are there delays, backfills, or future information leakage?

Common methods: time-zero definition, feature-window restriction, landmarking, lagged variables, washout periods, time-varying models.

### Missingness Mechanism

Is missingness random, conditionally random, or informative?

Common methods: missingness table, missingness models, multiple imputation, inverse probability of censoring weights, pattern-mixture sensitivity, complete-case justification.

### Aggregation Mechanism

Are data individual-level, group-level, area-level, site-level, or time-level?

Common methods: multilevel models, cluster-robust standard errors, ecological-bias warning, within-site estimation, random effects, spatial correlation.

### Linkage Mechanism

How are sources connected? Are linkage errors differential?

Common methods: linkage success analysis, duplicate handling, probabilistic linkage rules, source-priority hierarchy, conflict resolution, unlinked-sample comparison.

### Feedback Mechanism

Will a model, policy, recommendation, or risk score change future data?

Common methods: drift monitoring, post-deployment audit, pre/post threshold monitoring, recalibration rules, human override review.

## 4. Bias Map

Include likely biases and prevention strategies:

- Confounding: define causal structure and adjustment set.
- Collider bias: avoid conditioning on variables caused by both exposure and outcome.
- Selection bias: audit entry, participation, testing, treatment, platform activity, and follow-up.
- Detection bias: account for differential measurement or surveillance intensity.
- Immortal time bias: align time zero and exposure assignment.
- Label leakage: prevent post-outcome or future variables from entering prediction features.
- Outcome misclassification: validate labels or assess sensitivity.
- Informative censoring: model dropout or censoring probability.
- Digital divide bias: assess device ownership, access, literacy, and subgroup coverage.
- Site or platform bias: evaluate heterogeneity before pooling.

## 5. Evaluation Matrix

Match evaluation to the goal.

Descriptive: coverage, denominator validity, standardization, subgroup completeness, uncertainty.

Association: robustness to covariates, nonlinearities, interactions, missingness, clustering.

Causal: assumptions, balance, negative controls, placebo tests, sensitivity to unmeasured confounding.

Prediction: discrimination, calibration, threshold utility, temporal validation, external validation, subgroup performance.

Dynamic: back-testing, lag assumptions, scenario sensitivity, parameter identifiability.

Implementation: workflow fit, cost, explainability, fairness, privacy, drift, auditability.

## 6. Reporting Blueprint

Recommend the following when relevant:

- Population flow diagram.
- Data-generation diagram.
- Target trial table for causal work.
- Time-window diagram for prediction or longitudinal work.
- DAG for causal assumptions.
- Table 1 comparing included, excluded, missing, and target populations.
- Outcome and exposure definition table.
- Missingness and linkage table.
- Main estimate table with uncertainty.
- Robustness and sensitivity table.
- Calibration plot, ROC/PR curve, decision curve, threshold workload table for prediction.
- Subgroup and fairness table.
- External validation table.
- Limitations organized by data, design, model, implementation, and external validity.

## 7. Reviewer-Ready Critique Checklist

Pre-empt these criticisms:

- The target population is unclear.
- The sample is not representative.
- The outcome or label is not valid.
- Time zero is ambiguous.
- The analysis uses future information.
- Covariate adjustment induces collider bias.
- Confounding is insufficiently addressed.
- Missingness is informative.
- External validation is missing.
- Calibration is not reported.
- Average performance masks subgroup failure.
- The model cannot be implemented in the claimed setting.
- Privacy or governance affects data quality or auditability.
- The conclusion uses causal language without causal design.

## 8. Writing Guidance

Use precise language:

- "Observed in the recorded data" for descriptive findings.
- "Associated with" for association.
- "Estimated effect under specified assumptions" for causal analysis.
- "Predicted risk of the recorded outcome" for prediction.
- "Scenario under assumptions" for simulation.
- "Implementation readiness" for deployment claims.

Avoid vague instructions. Replace "clean the data" with concrete checks; replace "build a model" with target quantity, candidate methods, validation design, and interpretation boundaries.
