# 可追溯台账协议

## 最小结构

```json
{
  "protocol": "formal-revision-traceability/1.0",
  "items": [
    {
      "id": "F-001",
      "source_text": "完整要求",
      "decision": "accept",
      "change_required": true,
      "response": "正式回应",
      "status": "resolved",
      "actual_changes": [
        {
          "artifact": "relative/path.docx",
          "anchor": "章节、页码、行号、对象ID或稳定文本",
          "evidence": "实际修改摘要或原文"
        }
      ]
    }
  ]
}
```

## 字段规则

- `id`：唯一且稳定。
- `source_text`：保持来源原文；不得用概括替代。
- `decision`：`accept`、`partial`、`decline`、`clarify`、`defer` 之一。
- `change_required`：布尔值。
- `response`：面向接收方的正式回应；内部说明另存。
- `status`：`resolved`、`deferred`、`open` 之一。
- `actual_changes`：实际完成操作；不得记录计划中的修改。
- `artifact`：相对交付目录的路径，或带协议的外部标识。
- `anchor`：足以复查的位置。
- `evidence`：支持修改声明的内容。

## 兼容与安全

- 接受主版本 `1`。
- 忽略未知字段并保留原始记录。
- 缺少关键字段时形成审计发现。
- 内部意见、身份和决策过程使用 `internal_*` 字段，并禁止导出到正式回应。
- 台账属于内部审计材料，默认不得进入正式交付目录。
