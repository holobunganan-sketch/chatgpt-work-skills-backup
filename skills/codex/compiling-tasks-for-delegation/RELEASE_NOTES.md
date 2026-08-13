# v1.1.0

Adds a dedicated `GPT-5.3-Codex-Spark` compilation path while preserving the generic delegation modes from v1.0.0.

Highlights:

- explicit Spark-target detection and `SPARK_EXECUTION_MODE`;
- Spark-specific execution profile grounded in OpenAI's real-time, targeted-edit workflow guidance;
- chunked Spark packages with one bounded outcome per chunk;
- conservative chunk budgets: up to 6 atomic steps, default up to 3 primary files/resources, and a <=12k-token compiler target for active context;
- mandatory per-chunk verification to compensate for Spark's lightweight default behavior;
- hard continuation gate after every successful non-final chunk: report, stop, and ask the user before reading or executing the next chunk;
- validator support for Spark package structure, chunk limits, target model, mandatory verification, and continuation markers;
- Spark templates, example package, tests, README guidance, and CI/release validation.
