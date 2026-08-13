---
name: top-journal-data-plan
description: Generate top-journal-level data processing and analysis planning guidance without executing actual analysis. Use when the user asks to design detailed data handling, statistical analysis, causal inference, prediction modeling, validation, interpretation, reporting, or manuscript-grade methods for public health, epidemiology, clinical real-world data, policy, social science, business, platform, sensor, text, or other observational/real-world datasets.
---

# Top Journal Data Plan

## Core Rule

Produce a rigorous data processing and analysis plan only. Do not run statistical analysis, compute final results, fabricate data outputs, or claim findings from data unless the user separately asks for execution and provides data.

Act as a methods designer for a top-tier journal submission: convert a research question into a defensible analysis blueprint covering data construction, bias control, method selection, evaluation, interpretation, sensitivity analysis, and reporting.

## When Using This Skill

Use Chinese by default when the user writes in Chinese. Use a formal, research-facing style.

If the user's question is broad, infer a reasonable study setting and state assumptions briefly. Ask only when the missing detail would change the analysis class, target population, or core design.

For complex or high-stakes tasks, read `references/methodology.md` before producing the plan. Use it as the detailed method library; do not paste it wholesale.

## Output Structure

Unless the user requests another format, produce the plan with these sections:

1. **Research Positioning**
   - Define the target system, target population, analysis unit, time zero, exposure/input, outcome/label, comparator, estimand or target quantity, and intended use.
   - Classify the task as descriptive surveillance, association/risk-factor analysis, causal effect estimation, prediction/screening, dynamic simulation, implementation evaluation, or mixed.

2. **Data Construction Plan**
   - Specify inclusion/exclusion logic, source population, observation windows, feature windows, follow-up windows, event definitions, duplicate handling, linkage rules, and data versioning.
   - Distinguish conceptual definitions from operational definitions for key variables.

3. **Data Generation and Bias Audit**
   - Audit selection, measurement, missingness, time-ordering, aggregation, linkage, and feedback mechanisms.
   - Identify likely biases such as confounding, collider bias, immortal time bias, outcome misclassification, detection bias, informative missingness, label leakage, and digital divide effects.

4. **Primary Analysis Strategy**
   - Choose methods according to the target question, not model fashion.
   - Explain why the chosen method fits the estimand, data structure, and assumptions.
   - Include the adjustment strategy, stratification, interaction, clustering, weighting, or hierarchical structure as needed.

5. **Validation and Evaluation**
   - For descriptive work: assess representativeness, denominator quality, standardization, time comparability, and uncertainty.
   - For causal work: assess exchangeability, positivity, consistency, temporal order, balance, negative controls, placebo tests, or sensitivity to unmeasured confounding.
   - For prediction work: assess discrimination, calibration, threshold performance, external validation, temporal validation, subgroup performance, decision utility, and model drift.
   - For dynamic work: assess back-testing, parameter sensitivity, lag structure, scenario robustness, and intervention timing.

6. **Sensitivity and Robustness Plan**
   - Include alternative exposure/outcome definitions, time windows, missing-data strategies, model forms, covariate sets, sample restrictions, weighting strategies, and subgroup analyses.
   - Separate robustness checks that test the same estimand from exploratory analyses that answer adjacent questions.

7. **Interpretation Rules**
   - State what can and cannot be concluded.
   - Keep prediction language separate from causal language.
   - Define how uncertainty, heterogeneity, subgroup differences, and external validity should be interpreted.

8. **Reporting Blueprint**
   - Specify tables, figures, flow diagrams, bias diagrams, model-performance displays, sensitivity-analysis appendices, and manuscript methods language needed for a top-journal submission.

9. **Reviewer-Ready Risk Points**
   - List the most likely reviewer criticisms and how the analysis plan pre-empts them.

## Method Selection Rules

- Prefer transparent classical or semi-parametric methods when they answer the question well.
- Use machine learning when nonlinearity, high-dimensionality, multimodality, text/image/sensor data, or prediction performance justifies it.
- Do not use feature importance as causal evidence.
- Do not report only AUC for prediction models; calibration and threshold utility are mandatory when decisions depend on predicted risk.
- Do not treat large sample size as protection against bias.
- Do not pool multi-site or multi-source data before checking conceptual comparability and heterogeneity.
- Do not interpret observed labels as true outcomes without label validity discussion.

## Deliverable Standard

The final output should be actionable enough that a researcher could use it to write a statistical analysis plan or manuscript Methods section. Avoid generic phrases such as "clean the data", "run regression", or "validate the model" unless each is specified with purpose, assumptions, and evaluation criteria.

When evidence is insufficient, provide a conservative plan with explicit assumptions rather than broad caveats.
