# 认知单元规划

读取全部可交付正文段落和分类结果。为每个段落分配一个且仅一个认知单元。按完整研究命题/论证任务切分，禁止按固定段落数量切分。

通用切分信号：讨论对象改变、新问题、新主张、新证据类型、描述转解释、支持转反驳、观点归属切换、新原文标题、新图表论证、推理链闭合。

每个单元生成：`id`、`source_section_id`、`assistant_title`、`rhetorical_functions`、`source_paragraph_ids`、`source_pages`、`understanding_level`、`visual_candidate_ids`。

解释触发：复杂概念、影响可信度的方法、证据到结论的推理跨度、观点归属易混淆、重要限定/替代解释、全文关键转折。普通清楚内容用 `none`。
