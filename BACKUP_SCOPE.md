# 备份范围

更新日期：2026-08-15（Asia/Shanghai）

## 已纳入

- `~/.codex/skills` 白名单中的用户级 skills 与 `.shared` 共享核心。
- `~/.agents/skills` 白名单中的可迁移 skills。
- `~/plugins/medical-manuscript-workflow` 权威源码。
- `~/.agents/plugins/marketplace.json` 中名称为 `medical-manuscript-workflow` 的条目。
- 双向同步技能 `syncing-codex-skills-and-plugins`。

仓库当前保留 49 个实体 skill 源，并用 26 条恢复映射提供 37 个 Codex 与 26 个 Agent 逻辑目标。插件内嵌内容与 standalone 内容完全相同时，插件副本作为权威来源；其余 Codex/Agent 完全相同副本使用 Codex 来源。同名且哈希不同的分支分别保留。

个人插件版本为 `0.1.0+codex.20260806083632`，权威路径为 `plugins/medical-manuscript-workflow/`，共 225 个文件、12 个内嵌 skills。

## 固定排除

- `~/.codex/skills/.system` 与 Codex 主运行时：由 Codex 管理并随软件恢复。
- `~/.codex/plugins/cache`：插件安装缓存，可由权威源码重新生成。
- 官方与远程插件：在新计算机上通过插件目录安装。
- `~/.codex/config.toml`、`.env*`、认证令牌、私钥、浏览器状态、日志、会话数据、项目记录和安装标识。
- `__pycache__`、`*.pyc`、`*.pyo`、临时文件与版本控制元数据。
- 白名单之外的用户目录。

白名单同步单位内出现 `config.toml`、令牌或私钥特征时，本地上传会阻断。被固定排除的缓存与临时文件不会参与树哈希或复制。

## 完整性与兼容性

每个目录使用规范相对路径与两级 SHA-256 树哈希。`restore-map.json` 记录权威来源、逻辑目标和来源树哈希。`verify.ps1` 会先校验结构、映射与实体去重，再校验 `SHA256SUMS.txt`。

本迁移包面向 Windows PowerShell 7。skills 与插件源码采用普通目录结构，其他系统可依据相同白名单和目标路径迁移。插件界面或插件命令的可用性取决于新计算机上的 Codex 版本。
