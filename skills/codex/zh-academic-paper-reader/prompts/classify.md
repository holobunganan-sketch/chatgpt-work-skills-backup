# 分类任务

完整浏览论文标题、摘要、章节树、正文开头与结尾，识别“作者通过本文完成什么知识任务”。允许一个主适配器和0-3个辅助适配器。不得因为看见 Introduction/Methods/Results 字样就自动判定 empirical-imrad；需结合证据形式和核心产出。

输出 `work/classification.json`，字段固定为：`primary_adapter`、`secondary_adapters`、`knowledge_tasks`、`confidence`、`reasoning_summary`。适配器必须来自 `adapters/`。
