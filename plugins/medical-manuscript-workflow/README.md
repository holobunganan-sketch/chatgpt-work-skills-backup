# Medical Manuscript Workflow

这是一个面向医学论文写作、返修和投稿交付的 Codex 插件。入口 Skill 会识别项目阶段，按顺序调用证据源包、全文写作、Discussion、主线编辑、人在回路审批、DOCX 精确修改、格式整理、跨文件一致性和独立发布审计等能力。

## 六类入口

- 新论文：建立证据源包，生成全文，再完成格式和投稿目录。
- 现有手稿修改：锁定权威 DOCX，先形成逐条修改意见，审批后执行。
- 审稿返修：完整解析 Reviewer 原文，逐条审批，生成双版本手稿和独立回复文件。
- Discussion 专项：围绕结果组织解释、比较、机制、意义和边界。
- 格式专项：依据用户模板、期刊要求或插件默认格式整理手稿。
- 审计专项：只读检查内容、格式、跨文件一致性和交付边界。

前门入口为 `$manuscript-workflow-orchestrator`。可直接提出“解析审稿意见，逐条交给我审批并完成返修”或“整理为投稿可用目录”等请求。

## 返修控制

插件按 Reviewer 顺序保存完整原文。长自然段拆分为原子化 Comment，Comment 区间与非行动区间共同覆盖全部字符。覆盖率达到 100% 后，系统逐条提交修改建议供用户批准。未获批准的修改不会写入手稿。

每个 Reviewer 对应一个 DOCX 回复文件，文件内循环呈现：

1. Reviewer Comment
2. Response
3. Location of Revision

删除内容从 Clean 和 Highlighted 两份手稿中移除，并在 Response 中说明。两份手稿的正文和受保护 Word 结构必须一致，Highlighted 版本只增加黄色修改高亮。

## 投稿目录边界

返修交付目录采用以下结构：

```text
Submission_Package/
├─ Manuscript_Clean.docx
├─ Manuscript_Highlighted.docx
├─ Main_Figures_and_Tables/
├─ Supplementary_Materials/
├─ Response_to_Reviewers/
└─ Submission_Documents/
```

JSON、Markdown、CSV、日志、脚本、缓存、审计记录、审批记录、中间稿和临时文件保留在内部工作区，不进入投稿目录。Zotero 字段、书签、域、交叉引用、公式、图形和其他受保护结构在修改前后接受完整性检查。

## 自检

在插件根目录运行：

```powershell
python scripts/self_check.py
```

自检覆盖 Skill 清单、JSON Schema、Reviewer 原文覆盖、审批状态、回复文件结构、双版本手稿一致性和投稿目录纯净度。
