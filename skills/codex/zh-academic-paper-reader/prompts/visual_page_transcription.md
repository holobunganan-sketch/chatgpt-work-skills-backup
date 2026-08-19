# 扫描页 / 低文本页视觉转录

读取 `source/page_manifest.json`。当 `needs_visual_transcription=true`，必须查看对应 `source/pages/page_XXXX.png`。

目标是补齐“原文证据层”，不是直接写中文摘要。按页面自然阅读顺序转录可辨识正文、标题、图表编号与关键脚注，并标记无法辨识区域。不得猜测缺失文字。把补录内容写入 Agent 的工作数据，再纳入认知单元规划和覆盖率检查。
