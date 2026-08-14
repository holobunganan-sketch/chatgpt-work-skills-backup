# ChatGPT Work Skill 去重设计

日期：2026-08-14  
基线提交：`2a065f2c44574a0b7dbc55b60562d4549116f37f`

## 目标

减少仓库中内容完全相同的 skill 目录，同时保持新计算机恢复后的发现路径、skill 数量和个人插件结构不变。

完成后的功能不变量：

- `~/.codex/skills` 恢复 36 个用户级 skills，并保留 `.shared` 共享核心。
- `~/.agents/skills` 恢复 26 个有效 skills。
- `~/plugins/medical-manuscript-workflow/skills` 保留 12 个内嵌 skills。
- 同名但内容不同的 `docx-precision-edit`、`submission-grade-medical-research-pipeline` 和 `submission-grade-scientific-research-pipeline` 分别保留各自版本。
- marketplace、插件清单、缓存排除和备份策略保持有效。

## 基线审计

当前仓库包含 74 个物理 skill 目录、45 个唯一名称、27 组同名目录。24 组内容完全相同，3 组同名目录内容不同。

Git 能复用内容相同的 blob，当前检出目录仍存在重复文件。去重后计划保留 48 个物理 skill 目录，对应 45 个唯一名称和 3 个有意保留的内容分支。

## 方案比较

### 方案 A：单一源码与恢复映射（采用）

为每组内容完全相同的 skill 指定一个仓库内权威源码。新增 `restore-map.json`，记录源码相对路径、目标根目录和 skill 名称。安装脚本先复制现存源码目录，再按映射生成被省略的目标副本。

优点：Windows、Git、GitHub ZIP 和插件安装均可使用；检出目录获得实际去重；恢复结果可程序化验证。代价：安装脚本和校验脚本需要识别映射。

### 方案 B：符号链接或硬链接

重复目录用文件系统链接指向权威目录。该方案依赖 Windows 开发者模式、权限和 Git 链接配置；GitHub ZIP 及插件归档中的行为也容易出现差异，因此不采用。

### 方案 C：维持目录并依赖 Git blob 复用

继续保存所有路径，由 Git 对相同文件内容进行对象级复用。该方案改动最少，无法减少工作区和下载 ZIP 解压后的重复目录，因此不采用。

## 权威源码规则

1. 个人插件必须保持自包含。插件内嵌 skill 与 standalone 副本完全相同时，以插件目录为权威源码，删除对应 standalone 副本。
2. `.codex` 与 `.agents` 的同名目录完全相同且未由插件提供时，以 `skills/codex/<name>` 为权威源码，删除 `skills/agents/<name>` 副本。
3. 同名目录的树哈希不同，保留各自源码，不创建去重映射。
4. `.shared` 共享核心保持在 `skills/codex/.shared`，不参与 skill 名称去重。

## 恢复映射

新增根目录文件 `restore-map.json`：

```json
{
  "schemaVersion": 1,
  "entries": [
    {
      "source": "skills/codex/example-skill",
      "destinationRoot": "agents",
      "skillName": "example-skill",
      "sourceTreeHash": "SHA256"
    }
  ]
}
```

约束：

- `source` 必须位于仓库内，且必须包含 `SKILL.md`。
- `destinationRoot` 只允许 `codex` 或 `agents`。
- `skillName` 必须与目标目录名一致。
- `(destinationRoot, skillName)` 在物理目录与映射条目组成的目标集合中必须唯一。
- `sourceTreeHash` 用于证明删除副本前后内容一致，并在安装前校验来源未漂移。

## 文件影响图

`restore-map.json` 是去重关系的权威源。变更传导顺序如下：

1. 依据目录树哈希生成并审核映射。
2. 删除映射覆盖的完全相同副本。
3. 更新 `install.ps1`，复制物理目录后应用映射。
4. 更新 `verify.ps1`，校验映射、来源树哈希、目标唯一性和恢复计数。
5. 更新 `inventory.json`，区分打包源码与恢复目标。
6. 更新 `README.md` 和 `BACKUP_SCOPE.md`，说明去重结构与恢复行为。
7. 重新生成 `SHA256SUMS.txt`。

## 安装行为

`install.ps1` 继续备份已存在的同名目标。新增映射阶段后，安装顺序为：

1. 验证迁移包。
2. 安装 `skills/codex` 中的物理目录与 `.shared`。
3. 安装 `skills/agents` 中的物理目录。
4. 安装个人插件源码。
5. 按 `restore-map.json` 生成省略的 standalone skill 目录。
6. 合并个人 marketplace。

新增可选参数 `-TargetUserRoot`，便于在临时目录中执行完整恢复测试；默认值仍为当前用户目录。

## 错误处理

- 映射来源缺失、树哈希不一致、目标重复或目标根目录非法时，安装立即停止。
- 删除副本前再次比较树哈希；任何差异都会阻断删除。
- 恢复目标已存在时沿用现有备份机制，再写入新内容。
- Git 历史保留去重前提交，可用于完整回滚。

## 验证方案

1. 运行 `verify.ps1`，要求哈希、映射结构、来源树哈希和目标计数全部通过。
2. 在临时用户根目录执行 `install.ps1 -TargetUserRoot <temp>`。
3. 检查临时目录中 Codex skills 为 36、Agent skills 为 26、插件 skills 为 12。
4. 比较每个映射恢复目录与权威源码的树哈希。
5. 审计仓库中的物理 skill 目录，要求 48 个；完全相同的跨根目录副本组为 0。
6. 复查凭据特征、旧计算机绝对路径、Python 字节码和 GitHub 单文件大小限制。
7. 推送后核对远程提交、blob 数量、私有可见性和本地前后差异。

## 发布与回滚

实施变更提交到 `main` 并推送私有仓库。若恢复测试或远程核验失败，停止发布后续声明，使用 Git 历史回到基线提交，保留失败证据用于修正。

