# GPT Image → Editable PPT Skill

这是一个可安装到 Codex 的本地 Skill。它将结构化页面蓝图作为唯一内容源，使用 GPT Image 生成视觉参考或独立素材，再用原生 PowerPoint 对象构建可编辑页面。

安装方法见 `references/installation.md`。

首次使用：

```bash
python -m pip install -r requirements.txt
python scripts/self_test.py --workdir ./self-test-output
```

在 Codex 中调用：

```text
$gpt-image-to-editable-ppt
```
