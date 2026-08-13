# 中立交换协议

## 目录

1. 协议定位
2. 兼容原则
3. 顶层结构
4. 记录字段
5. 状态与导出策略
6. 消费与生成规则
7. 示例

## 1. 协议定位

使用本协议在不同 Skill、代理、脚本或系统之间交换修改项和一致性状态。把协议视为可选接口。缺少协议文件时，直接从原始材料建立产物登记表和变更记录。

本协议只传递结构化事实，不替代原文件、授权决定或实际核验。

## 2. 兼容原则

- 使用 UTF-8 JSON。
- 使用 `protocol_version` 声明版本。
- 接收方必须拒绝无法解析的主版本。
- 接收方可以忽略未知扩展字段，并保留原字段以便再导出。
- 接收方必须重新验证产物身份、授权范围和 `actual_changes` 证据。
- 接收方不得把 `proposed`、`planned` 或 `claimed` 状态提升为 `verified`。
- 协议记录不得隐式扩大写权限。

## 3. 顶层结构

```json
{
  "protocol_version": "1.0",
  "exchange_id": "EX-20260101-001",
  "created_at": "2026-01-01T08:00:00+08:00",
  "producer": {
    "type": "skill",
    "name": "example-skill",
    "version": "1.0"
  },
  "project_ref": "PROJECT-001",
  "records": [],
  "extensions": {}
}
```

顶层必填字段为 `protocol_version`、`exchange_id`、`created_at`、`producer` 和 `records`。

## 4. 记录字段

每条记录表示一个独立反馈、决策或变更单元：

```json
{
  "record_id": "ITEM-001",
  "record_type": "change_request",
  "source": {
    "artifact_id": "feedback-file",
    "locator": "section-2/item-3",
    "verbatim": "原始反馈或要求"
  },
  "issue": {
    "summary": "需要统一术语",
    "dimensions": ["term"],
    "canonical_item_keys": ["term.service_name"]
  },
  "decision": {
    "status": "authorized",
    "authority": "owner",
    "rationale": "采用统一名称",
    "decided_at": "2026-01-01T09:00:00+08:00"
  },
  "authorized_scope": {
    "artifact_ids": ["master", "clean", "marked"],
    "dimensions": ["term"],
    "allow_transitive": true
  },
  "planned_changes": [],
  "actual_changes": [],
  "response": {
    "text": "",
    "status": "not_required"
  },
  "status": "authorized",
  "export_policy": "internal",
  "extensions": {}
}
```

### 4.1 `record_type`

允许使用：

- `feedback`：保真记录外部或内部反馈；
- `decision`：记录具有决定权人员的结论；
- `change_request`：记录待执行变更；
- `change_result`：记录实际改动和验证；
- `audit_finding`：记录一致性问题；
- `release_status`：记录发布门状态。

### 4.2 `source`

保留来源产物、定位和原文。`verbatim` 必须保持来源文字，不执行润色或概括。无法取得原文时，使用 `summary` 并声明 `fidelity: "summary"`。

### 4.3 `decision`

仅由有权决策的来源填充。咨询意见、模型建议和脚本结果不得标记为最终授权。

### 4.4 `authorized_scope`

列出允许修改的产物和维度。空列表代表没有写授权。`allow_transitive` 只允许沿已登记关系计算影响，不自动授权传递目标。

### 4.5 `planned_changes`

记录计划动作：

```json
{
  "artifact_id": "clean",
  "locator": "section-1",
  "action": "replace_term",
  "from": "旧名称",
  "to": "新名称",
  "status": "planned"
}
```

### 4.6 `actual_changes`

记录真实动作：

```json
{
  "artifact_id": "clean",
  "locator": "section-1/paragraph-2",
  "before": "旧名称",
  "after": "新名称",
  "status": "verified",
  "evidence": {
    "method": "text_check",
    "value": "定位后已核对"
  }
}
```

缺少定位、状态或证据时不得标记为 `verified`。

## 5. 状态与导出策略

### 5.1 状态

使用以下状态：

- `proposed`
- `authorized`
- `in_progress`
- `implemented`
- `verified`
- `not_applicable`
- `requires_authorization`
- `blocked`
- `rejected`

### 5.2 导出策略

- `internal`：仅用于内部协调；
- `formal_candidate`：可以转化为正式语言，仍需复核；
- `formal`：已经批准对外使用；
- `restricted`：仅限指定接收者。

默认使用 `internal`。不得把内部理由、人员身份、路径或过程性语言直接复制到正式交付物。

## 6. 消费与生成规则

### 6.1 消费规则

1. 验证协议主版本和必填字段。
2. 验证来源产物是否存在于当前登记表。
3. 重新核对授权范围。
4. 将计划与实际改动分开导入。
5. 对所有 `verified` 记录抽查或重新核验。
6. 将未知产物、未知规范项和越权目标标记为阻断或待授权。

### 6.2 生成规则

1. 保留原始反馈原文和定位。
2. 使用稳定记录 ID。
3. 显式记录决定权来源。
4. 只记录已经观察到的实际改动。
5. 为正式候选内容去除内部信息。
6. 不输出文件系统敏感信息，除非接收方协议明确需要且用户已授权。

## 7. 示例

以下记录表示术语更新已经在一个产物完成，另一个目标等待授权：

```json
{
  "protocol_version": "1.0",
  "exchange_id": "EX-001",
  "created_at": "2026-01-01T08:00:00Z",
  "producer": {"type": "skill", "name": "cross-artifact-consistency", "version": "1.0"},
  "records": [
    {
      "record_id": "ITEM-001",
      "record_type": "change_result",
      "source": {"artifact_id": "request", "locator": "item-1", "verbatim": "统一服务名称"},
      "issue": {"summary": "统一名称", "dimensions": ["term"], "canonical_item_keys": ["term.service_name"]},
      "decision": {"status": "authorized", "authority": "owner"},
      "authorized_scope": {"artifact_ids": ["master"], "dimensions": ["term"], "allow_transitive": true},
      "planned_changes": [
        {"artifact_id": "master", "locator": "heading", "action": "replace_term", "status": "planned"},
        {"artifact_id": "appendix", "locator": "table-1", "action": "replace_term", "status": "requires_authorization"}
      ],
      "actual_changes": [
        {"artifact_id": "master", "locator": "heading", "before": "旧名称", "after": "新名称", "status": "verified", "evidence": {"method": "text_check", "value": "已核对"}}
      ],
      "response": {"text": "", "status": "not_required"},
      "status": "requires_authorization",
      "export_policy": "internal",
      "extensions": {}
    }
  ]
}
```
