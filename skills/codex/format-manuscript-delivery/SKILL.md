---
name: format-manuscript-delivery
description: 将论文、医学共识、研究报告及其图表直接整理为洁净、完整、可投稿的 DOCX 交付包。调用本技能即表示任务进入投稿交付态，必须先逐句判断每句话是否适合出现在目标文种、目标章节和当前位置，再完成内容归位、正式论证、统一排版、图表整理、Zotero 动态引文保护、投稿审计和交付目录清理。用户未声明特定结构时默认执行含 Conclusion 的 IMRAD 结构；默认采用宋体/Times New Roman、12 磅、1.5 倍行距、纯黑文字、三线表、PNG 300 dpi 等规范。用于新建、修订、格式化或投稿前检查论文 DOCX、独立图表、补充材料和投稿包。
---

# 论文投稿交付态

## 调用即投稿交付

调用本技能后，以“接收方可以直接投稿或正式提交”为终点。除非用户明确只要求检查或排版，不以问题清单、审计报告、修改建议或格式化半成品结束任务。

先完成内容层面的投稿适格审读，再做排版、图表和文件层面的处理。排版整齐无法弥补正文中仍存在的内部语言、章节错位、立场稀释、冗余或自我保护式保留。

## 投稿适格逐句审读

对标题、摘要、关键词、正文、题注、脚注、表格单元格和补充材料逐句提出：

> 如果今天投稿，这句话应该出现在这一章节、这一段、这个位置吗？

每句话必须通过以下判断：

1. **文种适格**：符合论文、医学共识或研究报告的正式表达。
2. **章节适格**：承担当前章节应承担的功能，没有跨越 Methods、Results、Discussion 或 Conclusion 的边界。
3. **位置适格**：与前后句形成连续论证或信息序列，放在此处有明确理由。
4. **目标适格**：服务研究问题、用户指定论点和全文主线。
5. **表达适格**：直接、完整、专业，没有编辑语言、协作痕迹、过程说明和内部状态。
6. **必要性**：删除后会削弱研究信息、论证、可复现性、正式责任或投稿完整性。
7. **非重复**：没有机械复述结果、讨论或结论。
8. **非继承**：来源稿中出现过的保留、反方意见和编辑句不因此自动取得成稿资格。

未通过时执行重写、移动、合并或删除。若用户只授权排版或只读检查，记录问题并保持内容不变。

## 论证方向

- 把用户指定的研究主张、核心判断或倡议作为全文写作目标。
- Introduction 建立问题的重要性、现有工作的缺口和本研究必要性。
- Discussion 选择最有力且准确的结果、机制、文献联系和实践意义，形成支持核心判断的递进论证。
- Conclusion 提炼研究价值和前瞻方向，给出清楚、稳健的最终判断。
- 避免把立场型任务写成无结论的中立综述，避免以习惯性保留削弱核心信息。
- 不因执行者自身的风险偏好新增证据边界说明、泛化免责声明或“仍需更多研究”式套话。
- 来源稿中的“有人认为结果可能只是偶然”“目前证据仍有限”“尚不能说明”“仍需更多研究”“仍待进一步验证”等表达默认删除，禁止因原稿已经出现而原样继承或换词保留。
- 只有同时满足以下条件的局限才可进入成稿：指向具体的研究设计、样本、测量、统计分析或外部适用性；能够由研究实际情况支持；位于目标文种规定的局限段落；表达简洁且不重复。
- 无法具体说明限制来源和影响路径的泛化保留不得进入成稿。
- 未来研究仅在用户或目标文种需要时提出，必须给出具体研究对象、方法或验证目标，禁止用其撤回正文已经建立的结论。
- 禁止虚构或篡改研究事实、数据、统计结果、引文和来源。

## 核心目标

把内容适格性、正文排版、图表资产、Zotero 引文和正式交付目录作为一个整体处理。保留源文件，在副本上完成语义修订与格式化，随后执行机器审计和人工视觉复核。只有全部门禁通过的文件才能进入正式交付目录。

## 强制工作流

1. 锁定原始文稿、目标期刊模板、用户明确要求、授权修改范围、正式交付目录和内部工作目录。确认用户或目标期刊是否声明写作结构。
2. 读取 [SPEC.md](references/SPEC.md)；处理 DOCX 时同时读取 [DOCX_WORKFLOW.md](references/DOCX_WORKFLOW.md)。
3. 从 [manuscript-format-profile.json](assets/manuscript-format-profile.json) 读取机器规则。没有结构覆盖要求时启用默认 IMRAD；用户或期刊模板另有要求时，复制配置到项目工作目录后记录覆盖值。禁止改写技能内默认配置。
4. 明确研究问题、用户指定主张、各章节功能和段落主线。按“投稿适格逐句审读”处理全文；结构调整不得改变研究事实。用户授权只读或纯排版时，保留原文并单独报告语义问题。
5. 完成章节归位：Methods 保留研究设计、方法和目的；Results 保留结果；Discussion 承担解释、比较、机制和意义；Conclusion 承担宏观判断与前瞻。
6. 在源文件副本上运行 `enforce_docx_format.py`。不得覆盖唯一源文件。
7. 对图片运行 `audit_figure_assets.py`，再按 [VISUAL_REVIEW.md](references/VISUAL_REVIEW.md) 完成人工视觉检查。
8. 在正式交付目录之外建立 `delivery-manifest.json`，使用 [delivery-manifest.template.json](assets/delivery-manifest.template.json) 登记允许交付的手稿、图、表、补充材料和投稿 Checklist。
9. 运行 `audit_manuscript.py` 和 `audit_delivery_package.py`。错误项必须清零；警告项必须逐项语义复核。
10. 复核 Zotero 动态域数量、内容和位置。格式化前后任何 Zotero 字段发生变化时，停止交付并恢复源副本。
11. 打开最终 DOCX 逐页视觉检查，确认结构、章节边界、字体、分页、表格、题注、图片、页边距和引文显示正常。
12. 从目标期刊编辑、审稿人和专业读者视角完成最后通读，再次逐句回答“这句话应该出现在这里吗”。
13. 只把清单允许的正式文件放入交付目录。审计报告、清单文件、脚本、临时文件和工作记录留在内部工作目录。

## 快速命令

使用 Codex 工作区自带 Python 运行脚本。路径含空格时加引号。

```powershell
python scripts/enforce_docx_format.py 原稿.docx 格式化稿.docx
python scripts/audit_manuscript.py 格式化稿.docx --stage final --json-out 内部报告.json
python scripts/audit_figure_assets.py 图表目录 --json-out 内部图片报告.json
python scripts/audit_delivery_package.py 正式交付目录 --manifest 内部工作目录\delivery-manifest.json --json-out 内部交付报告.json
```

需要检查格式化过程是否保护 Zotero 字段时：

```powershell
python scripts/audit_manuscript.py 格式化稿.docx --compare-source 原稿.docx --stage final
```

## 自动处理边界

自动执行：

- 将正文文字规范为中文宋体、英文/数字/英文标点 Times New Roman、12 磅、纯黑色和 1.5 倍行距；
- 将各节页边距规范为上 2.54 厘米、下 2.54 厘米、左 3.18 厘米、右 3.18 厘米；
- 加粗可识别的小标题；
- 移除首页单独页眉页脚设置；
- 将表格规范为三线表并统一黑色文字；
- 在 P 值列明确时，将 `P<0.05` 的显著性项目整行加粗；
- 居中题注，并纠正紧邻对象但位于错误一侧的表题或图题；
- 保留所有字段代码，尤其是 Zotero 动态引文。

仅审计并要求人工确认：

- 全文每句话的投稿适格性、章节归属、论证方向和正式语气；
- Discussion 首段是否完整概括研究问题、方法、主要结果及全文意义；
- Discussion 末段是否集中声明目标文种要求的 1–3 点具体局限；
- Conclusion 是否保持宏观、前瞻，并与 Results 和 Discussion 无内容重复；
- Results 中启发式命中的解释性、因果性或文献比较表达；
- 图片是否使用学术配色、是否保留宽边缘、画布是否存在标题；
- 图表内文字是否全部为英文；
- 无法明确识别的显著性行；
- 复杂合并表头、跨页表格和非标准题注；
- 文内图表引用与独立文件之间存在歧义的情形。

## 发布门禁

- [ ] 已逐句完成投稿适格审读，每句话都适合目标文种、章节、段落和当前位置。
- [ ] 全文持续服务研究问题、用户指定主张和正式用途。
- [ ] 没有编辑语言、协作痕迹、过程说明、内部状态、习惯性证据边界说明和自我保护式保留。
- [ ] 原稿中的泛化保留和无来源反方意见没有被原样继承或换词保留。
- [ ] 所有局限均具体、可定位、位于规定段落且篇幅适当。
- [ ] 未收到特定写作结构要求时，正文含 Introduction、Methods、Results、Discussion 和 Conclusion，顺序正确。
- [ ] Introduction 为 3 个自然段，未设置二级及以下小标题。
- [ ] Methods 和 Results 可以设置二级小标题，每个小标题下各有 1 个自然段。
- [ ] Discussion 为 5–7 个自然段，未设置二级及以下小标题；首段概括全文；末段按文种要求集中声明不超过 3 点具体局限。
- [ ] Conclusion 为 1 个宏观、前瞻的自然段，未复述 Results 或 Discussion。
- [ ] Methods 只写研究设计、方法及其目的，不含研究执行后才能得到的实际结果。
- [ ] Results 只报告结果；解释、机制、比较和推论均位于 Discussion。
- [ ] DOCX 可以正常打开，格式化副本与源文件均存在。
- [ ] 页边距、字体、字号、颜色和行距符合用户、期刊或默认配置。
- [ ] 无独立标题页；小标题加粗；正文没有过密项目符号。
- [ ] 表格为三线表；表题在上、图题在下且居中；显著性项目按整行加粗。
- [ ] 图片为 PNG、至少 300 dpi、英文标注、学术配色、无画布标题、保留宽边缘。
- [ ] 图、表、补充图和补充表具有独立文件，并按正文首次出现顺序编号。
- [ ] 正文包含每个图表的对应引用。
- [ ] Zotero 字段完整；同一引文位置不超过 4 篇文献。
- [ ] 正式目录只含手稿、图、表、补充材料和投稿 Checklist。
- [ ] 批注、修订、隐藏文字、过程说明、模型痕迹、内部清单、index、工作记录和审计报告为零。
- [ ] 机器审计无错误；所有警告均已人工复核；整页视觉检查通过。

## 资源导航

- [SPEC.md](references/SPEC.md)：强制规则、逐句投稿门禁、条件规则和冲突优先级。
- [DOCX_WORKFLOW.md](references/DOCX_WORKFLOW.md)：语义审读、DOCX 格式化、Zotero 保护和故障处理。
- [VISUAL_REVIEW.md](references/VISUAL_REVIEW.md)：图片、表格和整页人工检查。
- [DELIVERY_BOUNDARY.md](references/DELIVERY_BOUNDARY.md)：交付允许清单与过程内容禁入规则。
- [EVALUATION_CASES.md](references/EVALUATION_CASES.md)：测试案例和验收标准。
- [manuscript-format-profile.json](assets/manuscript-format-profile.json)：默认机器配置。
- [delivery-manifest.template.json](assets/delivery-manifest.template.json)：正式文件登记模板。
- `scripts/enforce_docx_format.py`：在副本上执行确定性排版。
- `scripts/audit_manuscript.py`：审计正文、表格、题注和 Zotero 字段。
- `scripts/audit_figure_assets.py`：审计 PNG 和 dpi。
- `scripts/audit_delivery_package.py`：审计交付边界和文件允许清单。
- `scripts/self_test.py`：运行技能自检。
