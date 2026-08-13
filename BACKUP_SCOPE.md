# 备份范围

生成日期：2026-08-13（Asia/Shanghai）

## 已纳入

- `~/.codex/skills` 下 36 个用户级 skill 目录及其 `.shared` 共享核心。
- `~/.agents/skills` 下的可迁移 skill 目录。
- `~/plugins/medical-manuscript-workflow` 权威源码。
- `~/.agents/plugins/marketplace.json` 中对应的个人插件条目。

个人插件源码与当前安装缓存 `~/.codex/plugins/cache/personal/medical-manuscript-workflow/0.1.0+codex.20260806083632` 的关键文件 SHA-256 一致。仓库采用 `~/plugins/medical-manuscript-workflow` 作为基线。

## 已排除

- `~/.codex/skills/.system` 和 `codex-primary-runtime`：由 ChatGPT Work/Codex 管理并随软件安装恢复。
- `~/.codex/plugins/cache`：安装缓存，可由插件源码重新生成。
- 官方和远程插件：应在新计算机上通过插件目录重新安装。
- `~/.codex/config.toml`、认证令牌、浏览器状态、日志、会话数据、项目记录和安装标识。
- `__pycache__`、`*.pyc`、临时文件和版本控制元数据。

## 兼容性说明

本迁移包面向 Windows PowerShell。skills 和个人插件源码均为普通目录结构，可在其他系统上手工复制到对应的用户目录。插件命令是否可用取决于新计算机上的 ChatGPT Work/Codex 版本；插件界面安装流程可作为兼容路径。
