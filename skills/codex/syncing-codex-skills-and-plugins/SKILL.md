---
name: syncing-codex-skills-and-plugins
description: Use when a user wants to back up, restore, synchronize, migrate, upload, or download personal Codex skills and the medical-manuscript-workflow plugin between a local profile and the configured private GitHub repository.
---

# 同步 Codex Skills 与插件

## 核心原则

先生成冻结计划，再统一确认一次，最后自动应用。确认只对当前计划哈希有效。

执行前完整读取 [references/SYNC_CONTRACT.md](references/SYNC_CONTRACT.md)。使用 [scripts/sync-codex-assets.ps1](scripts/sync-codex-assets.ps1) 完成扫描、哈希、写入、Git 操作和报告。

## 工作流

1. 如果用户尚未指定方向，只询问一次：
   - 云端到本地：`CloudToLocal`
   - 本地到云端：`LocalToCloud`
2. 检查 `pwsh`、`git`、`gh` 和 GitHub 登录。缺少身份或权限时停止并说明处理方式。
3. 使用 `-Mode Plan` 生成 JSON 计划。计划阶段不得修改正式目标或推送远端。
4. 用中文展示 `add`、`identical`、`conflict`、`extra`、`deduplicated-source` 和 `blocked` 的数量与必要路径。
5. 每次运行都统一询问一次：
   - `KeepTarget`：保留目标冲突，只新增缺失项目。
   - `SourceWins`：使用来源替换全部冲突；本地替换前备份。
   - `Cancel`：取消。
6. 使用原计划路径和所选决策调用 `-Mode Apply`。计划过期时停止，重新扫描并再次汇总确认。
7. 读取报告，先给出结果，再列出新增、跳过、冲突、备份、阻断、提交和远端核验信息。

## 命令形态

```powershell
pwsh -NoProfile -File <skill-root>\scripts\sync-codex-assets.ps1 `
  -Mode Plan `
  -Direction CloudToLocal `
  -PlanPath <plan.json> `
  -ReportPath <report.json>

pwsh -NoProfile -File <skill-root>\scripts\sync-codex-assets.ps1 `
  -Mode Apply `
  -Direction CloudToLocal `
  -Decision KeepTarget `
  -PlanPath <plan.json> `
  -ReportPath <report.json>
```

仅在测试隔离环境中传入 `-TargetUserRoot`、`-WorkspaceRoot` 或替代仓库地址。

## 停止条件

- 计划含 `blocked` 项。
- 包哈希、插件清单或恢复映射无效。
- 检测到凭据、密钥、受排除配置、超限文件或大小写路径冲突。
- 来源快照、目标内容或远端提交与计划不一致。
- 用户选择 `Cancel`。

停止时保留正式目标，写出报告，不推测冲突优先级。

## 快速参考

| 状态 | 默认动作 |
|---|---|
| `add` | 确认后新增 |
| `identical` | 跳过 |
| `conflict` | 按本次统一决策处理 |
| `extra` | 保留 |
| `deduplicated-source` | 通过恢复映射重建逻辑目标 |
| `blocked` | 停止 |

## 常见错误

- 直接运行复制命令，绕过计划哈希和汇总确认。
- 将 `~/.codex/plugins/cache` 当作个人插件权威源码。
- 合并同名目录并留下来源端已删除的旧文件。
- 在远端提交变化后继续使用旧计划。
- 使用强制推送或把令牌放入命令、计划、报告。

