# 同步契约

## 1. 公共接口

引擎模式：`Verify`、`Plan`、`Apply`。`Verify` 只读校验仓库结构、插件清单、恢复映射、实体去重与敏感内容门禁。  
方向：`CloudToLocal`、`LocalToCloud`。  
确认决策：`KeepTarget`、`SourceWins`、`Cancel`。

退出码：

- `0`：成功。
- `2`：校验失败、阻断或取消。
- `3`：计划过期。
- `4`：应用或回滚失败。

## 2. 白名单

- `~/.codex/skills` 中含 `SKILL.md` 的直接子目录。
- `~/.codex/skills/.shared`。
- `~/.agents/skills` 中含 `SKILL.md` 的直接子目录。
- `~/plugins/medical-manuscript-workflow`。
- `~/.agents/plugins/marketplace.json` 中名称为 `medical-manuscript-workflow` 的条目。

## 3. 固定排除

- `.git`、`.system`、`__pycache__`、`*.pyc`、`*.pyo` 和临时文件。
- Codex 插件缓存、系统 skills、官方及远程插件。
- `config.toml`、`.env*`、凭据、令牌、私钥、日志、会话和安装标识。
- 白名单之外的用户目录。

哈希计算会忽略固定排除项。本地上传时，白名单同步单位内出现 `config.toml`、令牌或私钥特征会形成独立 `blocked` 门禁；`.env*` 不读取、不复制。项目仍保留其 `add` 或 `conflict` 分类，因此分类汇总与阻断数可以同时计数。仓库校验发现阻断内容时同样停止。白名单之外的内容不扫描、不上传。

## 4. 身份与哈希

同步单位身份为 `<destinationRoot>/<name>`。`destinationRoot` 取 `codex`、`agents`、`plugin`、`marketplace` 或 `shared`。

目录树哈希步骤：应用排除规则；将相对路径规范为 `/`；按序数排序；计算每个文件 SHA-256；对 `<path>\t<hash>\n` 序列再次计算 SHA-256。发现仅大小写不同的路径时阻断。

## 5. 分类与动作

| 分类 | 含义 | 动作 |
|---|---|---|
| `add` | 仅来源存在 | 确认后新增 |
| `identical` | 双方树哈希相同 | 跳过 |
| `conflict` | 同一身份、哈希不同 | 按统一决策处理 |
| `extra` | 仅目标存在 | 保留 |
| `deduplicated-source` | 物理副本由映射替代的来源标记 | 目标仍按 `add`、`identical` 或 `conflict` 处理 |
| `blocked` | 安全或完整性门禁失败 | 停止 |

统一决定适用于当次计划中 skill、插件和 marketplace 的全部 `conflict`。恢复映射目标已存在时，先按树哈希分类：相同则跳过，不同则服从 `KeepTarget` 或 `SourceWins`。

## 6. 计划状态

计划 JSON 保持不可变的 `planned` 状态。用户决定写入应用报告；应用结果为 `applied`、`cancelled`、`stale` 或 `failed`。

计划至少包含：`schemaVersion=1`、`runId`、方向、生成时间、仓库、来源指纹、目标指纹、远端提交、规则版本、项目数组、汇总、阻断项和 `planSha256`。计算计划哈希时将 `planSha256` 置为空字符串。

Apply 必须重新计算来源、目标和 `origin/main` 提交。两个方向在 Plan 与 Apply 前都刷新托管工作区并以只允许快进的方式对齐 `origin/main`；网络失败、ref 缺失、无法快进或远端变化都会停止。任何快照差异都会把计划标记为 `stale`。调用方随后创建新 `runId` 和新计划文件，先展示过期报告，再展示新汇总并重新确认。旧计划保持可审计，禁止覆盖或复用。

## 7. 去重

插件内嵌内容与 standalone 内容完全相同时，以插件为权威源码。其余 Codex/Agent 完全相同副本以 Codex 为权威源码。同名但哈希不同的目录分别保留。每个省略副本写入 `restore-map.json`，包含 `source`、`destinationRoot`、`skillName` 和 `sourceTreeHash`。

`source` 是仓库根目录内、位于允许 skill 根下的规范相对路径。`destinationRoot/skillName` 必须唯一，目标不得仍有实体副本，来源必须含 `SKILL.md`，树哈希必须匹配。云端下载直接从仓库快照的权威来源复制到每个逻辑目标；同一来源的多目标写入归入一次本地事务，失败时按报告中的事务记录回滚。

## 8. 报告

报告写入 `~/.codex/sync-reports/<run-id>.json`，记录计划哈希、决定、动作、跳过、冲突、备份、阻断、回滚、Git 提交、远端核验和错误。报告不得记录凭据内容。阻断路径可以报告，检测到疑似敏感文件名时只保留同步单位身份和规则编号。

本地到云端要求干净工作树，使用普通提交并推送 `origin/main`，禁止强制推送。`SourceWins` 的云端旧内容由 Git 历史保留。推送失败时保留本地提交和干净工作树，报告提交号与失败状态；后续重试仍需重新计划。
