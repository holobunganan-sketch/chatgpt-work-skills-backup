# 审稿返修

## 解析要求

按 Reviewer 顺序保存完整原文。连续自然段先建立来源区块，再按独立请求拆分 Comment。每个 Comment 保存逐字原文、半开区间 `[start, end)`、核心请求、建议行动、影响范围和状态。

所有字符必须被 Comment 区间或 `non_action_segments` 覆盖。标题、问候、肯定性评价和背景陈述也要登记。上下文句可以被多个 Comment 重复引用，来源区间必须准确。

## 审批卡片

逐条向用户呈现：

1. Reviewer 原文；
2. 核心问题；
3. 建议修改；
4. 影响文件；
5. 推荐决定。

记录批准、拒绝、延后或附条件批准。未获批准不得修改。附条件批准只有在条件证据满足后进入实施状态。

## 实施和传导

每项修改绑定 `comment_id` 和 `change_id`。先修改权威手稿，再沿影响图更新摘要、章节、图表、补充材料、Clean、Highlighted 和 Response。实际修改保存改前、改后、位置和文件摘要值。

## Response 格式

每位 Reviewer 一个 DOCX，按原始顺序循环：

```text
Reviewer Comment
[逐字原文]

Response
[接受程度、实际行动或理由]

Location of Revision
[章节、小标题、页码、段落、定位原句]
```

删除内容在 Response 中说明。Location 记录原位置及删除后的相邻锚点。拒绝、部分接受和无需正文修改的意见也保留完整循环。

## 发布条件

- 覆盖率 100%；
- 每项意见有终局决定；
- 每项批准修改有落实证据；
- 每项 Response 处理核心问题；
- 每项 Location 可定位；
- Reviewer 文件数量与 Reviewer 数量一致。

