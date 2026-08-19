# 中文学术文献深度伴读 v2.0

面向学术 PDF 的跨学科中文认知伴读 Skill。支持 IMRaD 经验研究、系统综述/Meta、范围综述、叙述/批判综述、理论论文、方法/算法、质性、人文历史、病例/案例、指南/共识、数学证明、Protocol、数据资源以及混合文体。

## 安装

先安装 Python 依赖：`python -m pip install -r requirements.txt`。

安装到通用 Agent Skills：`python install.py --target agents`。
安装到 Codex：`python install.py --target codex`。
安装到 Claude Code：`python install.py --target claude`。
自定义：`python install.py --path D:/skills`。

## 基本运行

`python paper_reader.py prepare paper.pdf --out session`

Agent 按 `SKILL.md` 生成结构化 work 文件并提供图表 bbox 后：

`python paper_reader.py crop-visuals session --bboxes session/work/visual_bboxes.json`
`python paper_reader.py validate session`
`python paper_reader.py render session`

最终文件：`session/output/paper_reader_kindle.html`。

## 稳定性

HTML由固定脚本生成。模型不直接写HTML。原论文图表以页面裁切图片原样插入，不重绘、不转换成HTML表格。最终文件不包含作者名单、作者单位、通讯信息和文末参考文献列表。
