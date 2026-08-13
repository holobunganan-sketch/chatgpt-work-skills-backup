# 交付边界

## 区域

```text
Project/
├─ Source/
├─ Internal_Workspace/
└─ Submission_Package/
```

`Source/` 只读。`Internal_Workspace/` 保存台账、JSON、Markdown、CSV、日志、脚本输出、XML、缓存、中间稿、备份、预览和审计记录。`Submission_Package/` 只保存正式投稿文件。

## 正式目录

```text
Submission_Package/
├─ Manuscript_Clean.docx
├─ Manuscript_Highlighted.docx
├─ Main_Figures_and_Tables/
├─ Supplementary_Materials/
├─ Response_to_Reviewers/
└─ Submission_Documents/
```

返修项目要求两份手稿。正文图和补充图默认每张一个至少 300 dpi 的 PNG；期刊指定其他格式时覆盖默认值。正文表和补充表默认每表一个可编辑 DOCX。

`Response_to_Reviewers/` 每位 Reviewer 一个 DOCX。`Submission_Documents/` 只保存期刊正式要求的 Checklist、Cover Letter、作者信息和声明。

## 禁入对象

- JSON、Markdown、CSV、日志、脚本和缓存；
- 审计记录、审批记录、执行记录和过程说明；
- 临时文件、备份、旧稿、中间稿和失败稿；
- 解包 XML、修改差异、渲染预览和检查截图；
- 隐藏文件、系统文件、本地路径和模型信息；
- 待办标记、占位符、未授权批注、修订和隐藏文字。

使用内部允许清单组装投稿目录。扫描报告和允许清单自身留在内部工作区。发现未知文件时停止发布并重新组装。
