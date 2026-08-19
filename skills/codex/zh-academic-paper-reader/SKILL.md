---
name: zh-academic-paper-reader
description: Use when a user uploads an academic PDF and wants a faithful Chinese reading companion, especially when continuous understanding, cross-discipline paper structures, Kindle-friendly output, or original figure/table preservation matters.
---

# 中文学术文献深度伴读

中文调用名：**中文学术文献深度伴读**。兼容“中文医学文献伴读”“学术论文伴读”“英文学术论文深读”“Kindle 论文伴读”。

## 核心原则

先理解整篇论文的知识任务和论证结构，再翻译。自然段只作为内部证据与校验单位；交付物按照完整研究命题/论证任务组成“认知单元”，保持连续阅读。忠实翻译、理解说明、全文综合必须分开。

**必须使用脚本生成 HTML。禁止 Agent 自由编写最终 HTML。**

## 工作流

1. 运行 `python paper_reader.py prepare <PDF> --out <session>`，读取 `source/document.json`、`source/paragraphs.jsonl`、页面图和视觉候选。
2. 阅读 `references/methodology.md`。按 `prompts/classify.md` 生成 `work/classification.json`，允许多标签适配器。
3. 按 `prompts/plan_units.md` 生成 `work/unit_plan.json`。认知单元按语义/论证边界切分，禁止固定按自然段数量切分。
4. 按 `prompts/translate_unit.md` 逐单元完成忠实中文翻译和必要解释。Introduction/Methods 类内容优先连续；IMRaD Results 最详细；Discussion 中等详细。非 IMRaD 论文按对应适配器处理。
5. 对 Figure/Table：查看 `source/pages/*.png`，给出规范化 bbox；运行 `crop-visuals` 原样裁切。不得重绘、重排或改成 HTML 表格。每个图表只写一个连续“图表解读”段落。
6. 按 `prompts/synthesize.md` 完成七要素和全文串联，合并为 `work/paper_bundle.json`。
7. 运行 `validate`。有 errors 时必须修复；warnings 需要人工检查。
8. 运行 `render` 生成固定格式 `paper_reader_kindle.html`。

## 硬性边界

最终交付物排除作者名单、作者单位、通讯信息和文末参考文献列表。正文引用编号可以保留。不得改变原文结论强度；`may/suggest/associated` 不得升级为“证实/导致”。Protocol 不得虚构结果。图表必须保持原图像素内容，只允许裁切和等比例缩放。

## 固定输出

顶层顺序永远为：论文题目 → 阅读前先建立框架 → 文献类型与阅读路线 → 正文伴读 → 全文串联理解 → 术语与符号说明。

详细跨文体方法论见 `references/methodology.md`；适配器约束见 `adapters/`。


## 快速参考

| 情况 | 处理 |
|---|---|
| IMRaD经验研究 | 引言/方法连续，结果详细，讨论中等 |
| 综述/理论/方法/人文等 | 先判定知识任务，再调用对应适配器 |
| 扫描页或文本极少 | 查看 `source/page_manifest.json`，用页面图视觉转录并回填原文段落 |
| Figure/Table | 原样裁切图片，只写一个图表解读段落 |
| 类型不确定 | 使用 `general-mixed` + 七要素框架 |

## 常见错误

- 机械逐自然段翻译、逐段解释，导致阅读割裂。
- 因章节名类似 IMRaD 就忽略论文实际知识任务。
- 为了“易懂”而改变原文限定词、因果强度或统计含义。
- 重绘表格、拆表、重新配色或把论文表格转换成 HTML 表格。
- 让 Agent 自由写 HTML，导致不同模型输出结构漂移。
- 扫描页文本提取为空后直接跳过。必须通过页面图视觉读取补齐。

## 最短调用示例

用户说“调用中文学术文献深度伴读处理这份PDF”。Agent应先 `prepare`，再完成分类、认知单元规划、翻译/理解、图表原样裁切、全文综合、`validate`，最后由 `render` 输出 Kindle HTML。
