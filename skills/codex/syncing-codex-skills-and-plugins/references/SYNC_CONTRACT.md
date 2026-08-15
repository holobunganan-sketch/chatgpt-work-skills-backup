# 同步契约

## 1. 公共接口

引擎模式：`Plan`、`Apply`、`Verify`。  
方向：`CloudToLocal`、`LocalToCloud`。  
确认决策：`KeepTarget`、`SourceWins`、`Cancel`。

退出码：

- `0`：成功。
- `2`：阻断或取消。
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
| `deduplicated-source` | 物理副本由映射替代 | 从权威源码恢复 |
| `blocked` | 安全或完整性门禁失败 | 停止 |

## 6. 计划状态

状态机：`planned -> approved -> applied | cancelled | stale | failed`。

计划至少包含：`schemaVersion=1`、`runId`、方向、生成时间、仓库、来源指纹、目标指纹、远端提交、规则版本、项目数组、汇总、阻断项和 `planSha256`。计算计划哈希时将 `planSha256` 置为空字符串。

Apply 必须重新计算来源、目标和远端指纹。任何差异都会把计划标记为 `stale`。

## 7. 去重

插件内嵌内容与 standalone 内容完全相同时，以插件为权威源码。其余 Codex/Agent 完全相同副本以 Codex 为权威源码。同名但哈希不同的目录分别保留。每个省略副本写入 `restore-map.json`，包含 `source`、`destinationRoot`、`skillName` 和 `sourceTreeHash`。

## 8. 报告

报告写入 `~/.codex/sync-reports/<run-id>.json`，记录计划哈希、决定、动作、跳过、冲突、备份、阻断、回滚、Git 提交、远端核验和错误。报告不得记录凭据内容。

