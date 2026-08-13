---
name: manuscript-workflow-orchestrator
description: Use when a medical or life-science manuscript project needs routing across evidence preparation, full drafting, Discussion writing, controlled revision, reviewer-response processing, DOCX or Zotero preservation, journal formatting, submission packaging, or release auditing, especially when task order depends on project stage and deliverables must remain traceable and submission-ready.
---

# 医学论文工作流编排

## 核心契约

先识别项目阶段、授权范围、权威文件和正式交付目标，再选择最小充分工作流。把 `Source/`、`Internal_Workspace/` 和 `Submission_Package/` 作为隔离区域。所有内部台账、审计记录、JSON、Markdown、日志和临时文件留在内部工作区。

规则优先级：用户当前要求 → 目标期刊要求 → 已批准项目合同 → `format-manuscript-delivery` 默认规则。

## 建立项目合同

开始前读取 [PROJECT_CONTRACT.md](references/PROJECT_CONTRACT.md)，登记：

- 写作对象、研究问题、目标期刊和预期交付；
- 原始文件、权威来源、派生物及受保护元素；
- 允许读取、修改和发布的范围；
- Zotero 来源或现有 Zotero 字段；
- 正文图表、独立图表、补充材料和投稿文件；
- 当前阶段、缺失输入和阻断条件。

在唯一原件上禁止写入。检测到来源变动时关闭旧基线并重新评估下游状态。

## 选择路线

读取 [ROUTING.md](references/ROUTING.md)，从以下路线中选择：

| 路线 | 触发条件 | 核心顺序 |
|---|---|---|
| 新建论文 | 从研究材料、结果和文献开始 | Source Pack → 全文写作 → Discussion 专项 → 主线编辑 → 格式交付 → 发布审计 |
| 普通修订 | 已有手稿需要内容或格式修改 | 人工审批 → 主线或章节专项修改 → DOCX 精修 → 跨文件同步 → 格式交付 |
| 审稿返修 | 存在编辑或 Reviewer 意见 | 零遗漏解析 → 逐条审批 → 正文修改 → Response → 双版本手稿 → 发布审计 |
| Discussion 专项 | 只处理 Discussion | 结果中心 Discussion → 主线编辑 → DOCX 精修 → 格式检查 |
| 投稿交付 | 内容已完成，需要正式目录 | 格式交付 → 跨文件核验 → 边界门禁 → 发布审计 |
| 只读审计 | 用户只要求检查 | 期刊格式审计或可追溯审计，保持正式文件只读 |

跳过阶段时必须确认其退出门禁已经由当前项目证据满足。

## 执行审稿返修

审稿返修必须完整读取 [REVIEWER_REVISION.md](references/REVIEWER_REVISION.md)。

Reviewer 原文覆盖率必须为 100%。连续自然段拆分为原子意见时，保留逐字原文、来源区间、Reviewer、顺序和上下文。每个原始字符都要进入一个 Comment 或明确登记为无需回应区间。

状态顺序：

`已采集 → 已解析 → 等待审批 → 已批准/拒绝/延后/附条件批准 → 已实施 → 已回应 → 已验证 → 已发布`

未获批准不得修改。用户沉默、缺少批注、咨询意见和探索性表态均不构成批准。修改范围扩大时创建新的审批条目。

每位 Reviewer 生成一个独立 DOCX，并重复以下三项：

1. Reviewer Comment
2. Response
3. Location of Revision

删除内容不进入 Clean 或 Highlighted 手稿，在 Response 中说明删除内容、理由、原位置和最终相邻锚点。

## 调用专业 Skill

- 证据源包：`source-pack-builder`
- 全文写作：`write-evidence-grounded-manuscript`
- Discussion：`writing-result-centered-discussion`
- 主线编辑：`argument-centered-formal-editor`
- 人工审批：`human-in-loop-revision`
- DOCX 局部安全修改：`docx-precision-edit`
- 投稿格式：`format-manuscript-delivery`
- 期刊只读检查：`journal-format-reviewer`
- 跨文件同步：`cross-artifact-consistency`
- 独立发布审计：`traceable-release-auditor`
- 正式交付边界：`formal-deliverable-boundary-guard`

调用前完整读取相应 Skill。跨 Skill 传递稳定 ID、版本、授权状态、实际修改证据和受影响文件，不依赖口头状态。

## 生成双版本手稿

以 `Manuscript_Clean.docx` 为权威修订稿，从同一内容生成 `Manuscript_Highlighted.docx`。默认使用 Word 黄色高亮标记新增或改写后仍存在的文字。删除内容不呈现。

清除高亮属性后，两份文件的可见文字、段落、样式、图表、题注、书签、交叉引用、表格和 Zotero 字段必须一致。发现非展示性差异时放弃 Highlighted 文件并重新生成。

## 发布投稿目录

读取 [DELIVERY_BOUNDARY.md](references/DELIVERY_BOUNDARY.md)。正式目录名称固定为 `Submission_Package`，仅允许：

- `Manuscript_Clean.docx`
- `Manuscript_Highlighted.docx`（返修项目）
- `Main_Figures_and_Tables/`
- `Supplementary_Materials/`
- `Response_to_Reviewers/`（返修项目）
- `Submission_Documents/`

使用允许清单组装目录。未登记文件、过程文件和内部元数据命中时停止发布。

## 执行发布门禁

完整读取 [QUALITY_GATES.md](references/QUALITY_GATES.md)。发布前运行插件脚本：

```powershell
python scripts/validate_reviewer_coverage.py reviewer-ledger.json
python scripts/validate_revision_release.py reviewer-ledger.json
python scripts/compare_manuscript_variants.py Manuscript_Clean.docx Manuscript_Highlighted.docx
python scripts/validate_submission_package.py Submission_Package delivery-policy.json
```

插件根目录以当前 Skill 的上两级目录确定。内部报告输出到 `Internal_Workspace/`。

只有以下条件全部满足时发布：Reviewer 覆盖率 100%，未授权修改为零，Response 漏项为零，Location 有效，双版本非展示性差异为零，Zotero 和受保护元素异常为零，白名单外文件为零，独立审计 Critical 和 Major 问题为零。

## 异常处理

- 来源变化：关闭旧基线并重新分析。
- 覆盖率不足：停止审批并重新拆分。
- 受保护元素变化：恢复上一验证副本。
- Response 无落实证据：阻止发布。
- Location 因排版变化失效：最终排版后重新定位。
- 双版本不一致：重新生成 Highlighted 文件。
- 投稿目录污染：从允许清单重新组装。
- 学术判断或授权范围变化：返回用户决定。
