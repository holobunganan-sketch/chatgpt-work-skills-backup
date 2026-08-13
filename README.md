# ChatGPT Work Skills 与个人插件迁移包

本仓库用于把当前计算机上的用户级 skills 和个人插件迁移到另一台 Windows 计算机。仓库建议保持为 GitHub 私有仓库。

## 包含内容

- `skills/codex/`：当前 `~/.codex/skills` 中的用户级 skills。
- `skills/agents/`：当前 `~/.agents/skills` 中的可迁移 skills。
- `plugins/medical-manuscript-workflow/`：个人插件的权威源码。
- `marketplace/marketplace.json`：个人 marketplace 条目。
- `install.ps1`：Windows 一键恢复脚本。
- `verify.ps1`：文件哈希和结构校验脚本。
- `inventory.json`：迁移内容清单。
- `SHA256SUMS.txt`：仓库文件完整性哈希。

详细边界见 [BACKUP_SCOPE.md](BACKUP_SCOPE.md)。

## 在新计算机上恢复

先安装 Git、GitHub CLI、ChatGPT Work/Codex，然后登录 GitHub。克隆本仓库后，在 PowerShell 中运行：

```powershell
git clone <本仓库的 GitHub URL>
Set-Location .\chatgpt-work-skills-backup
powershell -ExecutionPolicy Bypass -File .\verify.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

恢复脚本会执行以下操作：

1. 把 `skills/codex` 合并到 `~/.codex/skills`。
2. 把 `skills/agents` 合并到 `~/.agents/skills`。
3. 把个人插件复制到 `~/plugins/medical-manuscript-workflow`。
4. 将插件条目合并到 `~/.agents/plugins/marketplace.json`。
5. 若目标目录已经存在，在 `~/ChatGPT-Work-migration-backups/` 中保存原内容。

脚本完成后重启 ChatGPT Work。进入插件界面，在 Personal marketplace 中安装或启用 `medical-manuscript-workflow`。支持插件 CLI 的版本也可运行：

```powershell
codex plugin add medical-manuscript-workflow@personal
```

新建一个会话，让 ChatGPT Work 重新加载 skills 和插件。

## 仅预览恢复动作

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
```

## 更新这个备份

在原计算机上重新复制有变更的 skill 或插件文件，随后重新生成 `inventory.json` 和 `SHA256SUMS.txt`，提交并推送到私有仓库。不要提交 `~/.codex/config.toml`、登录令牌、浏览器数据、运行日志或插件缓存。
