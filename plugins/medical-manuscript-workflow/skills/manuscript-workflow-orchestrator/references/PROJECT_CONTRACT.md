# 项目合同

在 `Internal_Workspace/project-contract.json` 中登记以下字段：

| 字段 | 要求 |
|---|---|
| project_id | 稳定项目标识 |
| task_type | 六类路线之一 |
| article_type | 文章类型 |
| research_question | 研究问题 |
| target_journal | 目标期刊或 null |
| format_source | user、journal 或 default |
| source_root | 原始材料目录 |
| internal_root | 内部工作目录 |
| delivery_root | 投稿目录 |
| authoritative_manuscript | 权威手稿路径和摘要值 |
| reviewer_sources | Reviewer 原文路径和摘要值 |
| zotero_status | existing、available、missing 或 not_required |
| protected_elements | Zotero、域、书签、批注、修订、公式等 |
| authorized_reads | 允许读取对象 |
| authorized_writes | 允许修改对象 |
| formal_allowlist | 允许发布的相对路径 |
| blockers | 阻断条件 |

新建或新增 Zotero 引文时，`zotero_status` 必须为 `available`。现有手稿返修时，原有字段必须登记并保持完整。缺少本地集成条件时阻止最终交付，不用普通文本冒充 Zotero 字段。

来源文件摘要值变化时关闭合同当前基线。重新登记受影响文件，废止依赖旧基线的审批、位置和发布结果。

