# compiling-tasks-for-delegation

一个面向多模型协作的 Agent Skill。它让高能力模型承担需求理解、决策、风险判断、任务拆解和验收设计，再把工作编译成低能力模型可以逐步执行的确定性执行包。

核心目标：**Think once, execute mechanically.**

## 适合什么场景

当你希望把复杂任务从高能力模型下放给成本更低、推理能力更弱或上下文更小的模型时使用，例如：

- GitHub / 代码仓库修改、测试、构建、发布；
- 文献提取、研究资料整理、证据表；
- Word / PPT / Excel / PDF 等知识工作；
- 数据清洗与固定分析流程；
- 文件批处理；
- 需要严格步骤、证据链和异常升级的运营任务。

## 核心机制

Skill 会强制建立以下控制层：

1. **现场检查**：只要当前文件、仓库、工具、版本、权限或外部状态可能改变执行方案，就先读取现场。
2. **三档执行资格**：`SAFE_TO_DELEGATE`、`CONDITIONAL`、`HIGH_MODEL_REQUIRED`。
3. **双层编译**：先写平台无关任务契约，再写针对当前环境的具体动作。
4. **零隐含决策**：低能力模型不能自行解释需求、选择重大方案或扩展范围。
5. **原子步骤**：每一步包含 Purpose、Input、Action、Expected Result、Evidence、Verdict、Exception Handling。
6. **Stop Code**：计划外分支、环境偏差、权限问题、冲突证据和高风险动作会停止并交回高能力模型。
7. **证据链**：`ACTION -> EXPECTED -> OBSERVED -> EVIDENCE -> VERDICT`。
8. **编译器自审**：交付前模拟低能力执行者逐步运行整个计划。
9. **机械校验**：内置 Python 校验器检查执行包结构。

## GPT-5.3-Codex-Spark 特例

当用户明确指定任务最终交给 `GPT-5.3-Codex-Spark` 执行时，Skill 会进入 `SPARK_EXECUTION_MODE`。`Codex`、`小模型`、`快速模型` 等泛称不会触发该模式。

OpenAI 将 Codex-Spark 定位为 Codex 中面向实时协作、定向修改和快速迭代的模型，并说明其默认工作风格较轻量，除非明确要求，否则不会自动运行测试。OpenAI 发布时记录的规格为 128k 上下文、text-only。Skill 因此采用保守的上下文预算和强制验证机制，不把最大上下文当作单次任务的填充目标。

Spark 模式固定生成分片执行包：

```text
spark-execution-package/
├── TASK.md
├── CONTEXT.md
├── SPARK_MASTER_INDEX.md
├── ACCEPTANCE.md
├── EXECUTION_REPORT.md
└── chunks/
    ├── CHUNK-001.md
    ├── CHUNK-002.md
    └── ...
```

每个 Chunk 默认遵守：

- 1 个主要结果；
- 最多 6 个原子步骤；
- 默认最多 3 个主要文件/资源；
- 当前 Chunk 加明确要求的上下文，编译目标不超过约 12,000 input tokens；
- 必须写出并实际执行 `Mandatory Verification`；
- 完成当前 Chunk 后立即停止；
- 成功状态下先汇报修改、验证和证据，再询问用户是否进入下一 Chunk；
- 未获得用户明确同意，不得预读、执行或部分开始下一 Chunk；
- `BLOCKED`、`FAILED`、`HIGH_MODEL_REQUIRED` 状态只汇报和升级，不进入下一 Chunk。

推荐调用方式：

```text
使用 $compiling-tasks-for-delegation。
这个任务最终要交给 GPT-5.3-Codex-Spark 执行。
请使用 Spark 专用分片执行协议编译以下任务：
<任务内容>
```

Spark 专用规则见 `references/gpt-5.3-codex-spark-profile.md`。

OpenAI 官方资料：

- https://openai.com/index/introducing-gpt-5-3-codex-spark/

## 输出模式

### GPT-5.3-Codex-Spark 任务

始终生成 Spark 分片目录式执行包。

### 简单任务

生成一个文件：

```text
EXECUTION_PLAN.md
```

### 复杂任务

生成目录式执行包：

```text
execution-package/
├── TASK.md
├── CONTEXT.md
├── STEPS.md
├── ACCEPTANCE.md
├── EXECUTION_REPORT.md
└── phases/                 # 仅在分阶段能明显降低执行上下文时使用
```

## 安装到 Codex

OpenAI 当前的 Codex Skill 结构以 `SKILL.md` 为必需文件，并推荐 `agents/openai.yaml` 作为 UI 元数据。Codex 的 Skill installer 会把第三方 Skill 安装到 `$CODEX_HOME/skills/<skill-name>`；未设置 `CODEX_HOME` 时通常为 `~/.codex/skills/<skill-name>`。

推荐直接在 Codex 中使用内置 `$skill-installer`，并提供本仓库：

```text
$skill-installer install https://github.com/holobunganan-sketch/compiling-tasks-for-delegation
```

也可以从 Releases 下载 ZIP，解压后确保目录结构为：

```text
$CODEX_HOME/skills/compiling-tasks-for-delegation/SKILL.md
```

安装后重启或重新加载 Codex Skills。

OpenAI 参考资料：

- https://openai.com/academy/skills/
- https://github.com/openai/skills
- https://github.com/openai/codex

## 使用

显式调用示例：

```text
Use $compiling-tasks-for-delegation to compile this task for a lower-capability executor:
<你的任务>
```

中文也可以：

```text
使用 $compiling-tasks-for-delegation，把下面这个任务编译成低等级模型可以严格执行的执行包：
<任务内容>
```

Skill 会根据复杂度选择单文件或目录式执行包。

## 仓库结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── compiler-protocol.md
│   ├── delegation-policy.md
│   ├── task-taxonomy.md
│   ├── gpt-5.3-codex-spark-profile.md
│   ├── environment-adaptation.md
│   ├── execution-step-spec.md
│   ├── evidence-policy.md
│   ├── stop-codes.md
│   └── compiler-audit.md
├── templates/
│   ├── EXECUTION_PLAN.md
│   ├── TASK.md
│   ├── CONTEXT.md
│   ├── STEPS.md
│   ├── ACCEPTANCE.md
│   ├── EXECUTION_REPORT.md
│   └── spark/
│       ├── TASK.md
│       ├── CONTEXT.md
│       ├── SPARK_MASTER_INDEX.md
│       ├── CHUNK.md
│       ├── ACCEPTANCE.md
│       └── EXECUTION_REPORT.md
├── scripts/
│   └── validate_execution_pack.py
├── examples/
├── evals/
└── tests/
```

## 校验执行包

```bash
python scripts/validate_execution_pack.py /path/to/execution-package
```

合法时：

```text
VALID
```

不合法时返回非 0 exit code，并列出缺失的文件、字段、Delegation 状态或遗留占位符。

机器可读输出：

```bash
python scripts/validate_execution_pack.py /path/to/execution-package --json
```

## 设计边界

这个 Skill 负责任务编译和执行资格控制。它不会自动把某一步交给特定模型，也不会替代模型路由器。你可以把生成的执行包交给任意较低等级的模型、Agent 或后续会话。

当执行现场出现计划没有覆盖的重大分支时，执行模型应停止并返回 Stop Code，由更高能力模型重新编译受影响部分。

## 版本

当前版本：`v1.1.0`

## License

MIT
