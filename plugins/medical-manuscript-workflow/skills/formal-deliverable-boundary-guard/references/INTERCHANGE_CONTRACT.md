# 可选交换协议

本 Skill 可以独立运行。存在其他工具生成的登记表时，接受下列最小结构：

```json
{
  "protocol": "formal-revision-artifact/1.0",
  "artifacts": [
    {
      "id": "A-001",
      "path": "relative/path.docx",
      "role": "formal",
      "status": "candidate",
      "export_allowed": true,
      "derived_from": ["A-000"]
    }
  ]
}
```

## 兼容规则

- 读取 `protocol` 主版本为 `1` 的记录。
- 忽略未知字段，不删除原始数据。
- 缺少字段时标记 `review`，不得推断发布许可。
- `export_allowed` 缺失时按 `false` 处理。
- 输出发现时采用：`artifact_id`、`rule_id`、`severity`、`evidence`、`status`、`resolution`。
- 将内部扫描报告标记为 `role: internal-audit` 与 `export_allowed: false`。
