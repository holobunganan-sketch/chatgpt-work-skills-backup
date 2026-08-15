# Codex Skills 与个人插件双向同步仓库

本私有仓库用于在多台 Windows 计算机之间同步个人 Codex skills、Agent skills 与 `medical-manuscript-workflow` 插件。仓库采用实体去重、恢复映射、冻结计划和一次汇总确认。

## 当前内容

- 49 个实体 skill 源。
- 26 条 `restore-map.json` 恢复映射。
- 可恢复 37 个 Codex skills 与 26 个 Agent skills。
- `plugins/medical-manuscript-workflow/` 为个人插件权威源码，内含 12 个 skills。
- `syncing-codex-skills-and-plugins` 提供云端到本地、本地到云端两种自动同步方向。

仓库不会保存 Codex 系统 skills、官方或远程插件缓存、登录信息、`config.toml`、`.env*`、日志、会话和浏览器状态。详细边界见 [BACKUP_SCOPE.md](BACKUP_SCOPE.md)。

## 在另一台计算机首次安装

先安装 Git、GitHub CLI 和 Codex，并登录同一个 GitHub 账号。随后在 PowerShell 运行：

```powershell
gh auth status
gh repo clone holobunganan-sketch/chatgpt-work-skills-backup "$env:USERPROFILE\Documents\Codex\chatgpt-work-skills-backup"
pwsh -NoProfile -File "$env:USERPROFILE\Documents\Codex\chatgpt-work-skills-backup\verify.ps1"
pwsh -NoProfile -File "$env:USERPROFILE\Documents\Codex\chatgpt-work-skills-backup\install.ps1"
```

首次安装采用 `KeepTarget`：安装缺失项，跳过相同项，保留已有冲突与额外内容。安装完成后重启 Codex，让新技能与插件元数据重新加载。

若只想预览：

```powershell
pwsh -NoProfile -File "$env:USERPROFILE\Documents\Codex\chatgpt-work-skills-backup\install.ps1" -DryRun
```

## 以后在 Codex 中使用

云端同步到本地：

```text
使用 syncing-codex-skills-and-plugins，把私有 GitHub 仓库同步到本地。先给我汇总，我统一确认一次；相同项跳过，冲突默认保留本地。
```

本地上传到云端：

```text
使用 syncing-codex-skills-and-plugins，把本地个人 skills 和 medical-manuscript-workflow 插件同步到私有 GitHub 仓库。先给我汇总，我统一确认一次；完全相同的副本去重。
```

每次运行会先校验仓库并生成冻结计划，展示 `add`、`identical`、`conflict`、`extra`、`deduplicated-source` 和 `blocked`。无阻断时只需选择一次：

- `KeepTarget`：保留目标冲突，只新增缺失项。
- `SourceWins`：使用来源覆盖全部冲突；本地覆盖前自动备份。
- `Cancel`：取消本次计划。

确认后流程自动完成。计划内容或 `origin/main` 发生变化时，旧确认失效；系统重新扫描、汇总并再次确认。上传使用普通提交与普通推送，不使用强制推送。

## 文件说明

- `skills/codex/`、`skills/agents/`：保留的实体 skill 源。
- `plugins/medical-manuscript-workflow/`：个人插件权威源码。
- `restore-map.json`：省略副本到权威来源的恢复映射。
- `inventory.json`：实体源、逻辑目标与排除范围清单。
- `verify.ps1`：结构、映射、去重、敏感内容和 SHA-256 校验。
- `install.ps1`：首次安全恢复脚本。
- `SHA256SUMS.txt`：仓库文件完整性清单。

