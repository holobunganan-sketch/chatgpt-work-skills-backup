# 正式修订交换协议

## 目录

1. 目的与独立性
2. 协议标识
3. 最小交换单元
4. 状态与枚举
5. 原文保真与摘要
6. 决定门交换
7. 变更与回应链接
8. 导出边界
9. 兼容与降级

## 1. 目的与独立性

使用本协议在不同 Skill、代理、脚本或系统之间交换修订状态。将协议视为可选互通格式。

- 每个 Skill 必须能够在没有本协议文件时独立完成自身职责。
- 接收兼容台账时应复用已验证事实，避免重复提取和版本漂移。
- 禁止依赖其他 Skill 的内部目录、私有脚本或隐藏状态。
- 无法兼容时应导入最小可验证字段，并记录转换来源和损失。

## 2. 协议标识

在 JSON 顶层使用：

```json
{
  "protocol": "formal-revision-interchange",
  "protocol_version": "1.0"
}
```

采用语义化兼容原则：

- 主版本变化表示不兼容字段或语义变化。
- 次版本变化表示向后兼容的新增字段。
- 读取方必须保留未知字段，禁止在无理由情况下丢弃。

## 3. 最小交换单元

交换台账至少包含：

```json
{
  "ledger_id": "稳定台账标识",
  "task": {
    "title": "任务标题",
    "decision_maker": {"id": "责任决策者标识", "role": "角色"}
  },
  "source_lock": {
    "locked": true,
    "locked_at": "ISO-8601 时间",
    "artifacts": []
  },
  "items": []
}
```

每个 `items[]` 至少包含：

- `item_id`：跨文件稳定且唯一的条目标识。
- `sequence`：来源内顺序。
- `source`：来源文件、原文、原文摘要值和原始定位信息。
- `semantic_location`：语义锚点、定位状态、坐标可靠性和判断依据。
- `interpretation`：核心问题、期望结果和约束。
- `classification`：行动分类和资源需求。
- `relations`：与其他条目的关系。
- `consultations`：咨询意见及其建议性身份。
- `recommendation`：拟议行动和影响范围。
- `decision`：责任决策状态与范围。
- `implementation`：实际变更记录。
- `formal_response`：正式回应及其变更链接。
- `verification`：核查状态与结果。
- `export_policy`：字段导出边界。

允许添加扩展字段。扩展字段应使用清晰命名空间，例如 `academic.*`、`legal.*` 或 `organization_x.*`。

## 4. 状态与枚举

### 决定状态

- `pending`
- `approved`
- `rejected`
- `deferred`

### 实施状态

- `not_started`
- `in_progress`
- `completed`
- `not_required`

### 回应状态

- `not_started`
- `draft`
- `completed`
- `not_required`

### 核查状态

- `not_started`
- `in_progress`
- `completed`

### 定位状态

- `found`
- `distributed`
- `no_direct_location`
- `unresolved`

### 行动分类

- `direct_content_revision`
- `evidence_research`
- `data_or_computation`
- `visual_or_structure`
- `response_only`
- `decision_required`
- `blocked`
- `other`

## 5. 原文保真与摘要

按 UTF-8 编码对 `source.verbatim` 的原始字符串计算 SHA-256，并写入 `source.sha256`。禁止先翻译、概括或修正常见错误后计算摘要。

如提取工具改变换行，应同时保存：

- `verbatim`：进入台账的完整原文；
- `raw_snapshot_ref`：未经规范化的原始快照或资源定位；
- `normalization_note`：发生的换行、空白或编码变换。

文件级源锁采用 `source_lock.artifacts[].content_sha256`。无法计算时使用稳定版本标识，并在 `lock_note` 说明原因。

## 6. 决定门交换

决定门文件至少包含：

- `gate_id`、`ledger_id` 和协议版本；
- 责任决策者；
- 覆盖条目和文件；
- 源锁、分析和关系图复核结果；
- 批准、拒绝和延后条目；
- 条件和未解决冲突；
- `execution_allowed`；
- 决定人和时间。

只有责任决策者或其明确授权代理可以将 `execution_allowed` 设置为 `true`。接收方必须同时验证条目级 `decision.status`。

## 7. 变更与回应链接

为每项实际改动分配 `change_id`。正式回应通过 `formal_response.change_ids` 引用变更。

变更记录至少包含：

```json
{
  "change_id": "CHG-001",
  "artifact_id": "ART-001",
  "location": "稳定位置说明",
  "change_type": "replace",
  "before": "改前内容或摘要",
  "after": "改后内容或摘要",
  "decision_gate_id": "GATE-001"
}
```

正式回应至少包含：

```json
{
  "required": true,
  "status": "completed",
  "text": "正式回应正文",
  "disposition": "accepted",
  "change_ids": ["CHG-001"],
  "locations": ["可核查位置"]
}
```

对无须修改的回应使用空 `change_ids`，并在正文中说明理由。禁止创建虚假变更以满足结构要求。

## 8. 导出边界

使用 `export_policy` 标记字段：

- `internal_only`：内部分析、咨询意见、风险、批注和决策过程。
- `formal_response_allowed`：允许转化为正式回应的事实和最终理由。
- `deliverable_allowed`：允许进入主交付物的正式内容。
- `restricted`：需额外授权方可导出。

任何导出器都应采用允许清单。禁止默认导出整个台账。

## 9. 兼容与降级

1. 验证 `protocol` 和主版本。
2. 验证原文摘要值和稳定编号。
3. 读取能够理解的字段并保留未知字段。
4. 对缺失字段生成诊断，禁止静默猜测。
5. 无法确认决定权时将决定重置为 `pending`。
6. 无法验证变更或回应链接时将核查状态重置为 `not_started`。
7. 将转换日志保存在内部记录中，禁止混入正式交付物。
