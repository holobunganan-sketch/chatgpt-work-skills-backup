# Codex Skills and Plugins Bidirectional Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, install, and publish `syncing-codex-skills-and-plugins`, a confirmed-plan, idempotent bidirectional synchronizer for the repository's user skills and personal plugin.

**Architecture:** `SKILL.md` owns the two user decisions: direction and one aggregate confirmation. A deterministic PowerShell engine owns plan generation, directory-tree hashing, duplicate elimination, local application, Git staging, push verification, rollback, and JSON reports. The root installer and verifier reuse the engine's contract so first-time installation and later skill-driven synchronization cannot drift.

**Tech Stack:** PowerShell 7.6+, Git, GitHub CLI, JSON, SHA-256, Python 3 for skill scaffolding/validation, local bare Git repositories for integration tests.

## Global Constraints

- Repository: `holobunganan-sketch/chatgpt-work-skills-backup`, private, default branch `main`.
- Skill name and folder: `syncing-codex-skills-and-plugins`.
- Each run asks for direction, generates a frozen plan, shows one aggregate confirmation, then applies without additional process questions.
- Identical targets are skipped without copying, backup creation, or Git content changes.
- Conflicts are preserved unless the aggregate confirmation selects source-wins; local replacements are backed up first.
- Logical deletions are disabled. Target-only items remain and are reported as `extra`.
- Physical exact-duplicate source directories may be removed only when `restore-map.json` proves every logical target can be reconstructed.
- Whitelist only user Codex skills, Agent skills, `.shared`, `medical-manuscript-workflow`, and its marketplace entry.
- Exclude system skills, managed/official plugin caches, credentials, configuration, logs, sessions, installation identifiers, `__pycache__`, and `*.pyc`.
- Keep the plugin self-contained and preserve three same-name/content-different skill branches.
- Final physical skill directories: 49. Restored targets: Codex 37, Agent 26, plugin 12.
- Use `apply_patch` for authored repository edits. Use deterministic scripts for generated manifests and mechanical duplicate removal.
- Preserve unrelated user changes. Never force-push or rewrite history.

---

### Task 1: Establish RED behavior and engine contract tests

**Files:**
- Create: `tests/sync/Invoke-SyncTests.ps1`
- Create: `tests/sync/fixtures/marketplace-existing.json`
- Create: `tests/sync/fixtures/marketplace-incoming.json`
- Create: `docs/superpowers/evidence/2026-08-15-sync-skill-red-baseline.md`

**Interfaces:**
- Consumes: approved design at `docs/superpowers/specs/2026-08-15-codex-bidirectional-sync-skill-design.md`.
- Produces: executable test runner with `Assert-Equal`, `Assert-True`, `New-TestSkill`, `Invoke-Engine`, and isolated test roots; baseline evidence for four fresh-context agent scenarios.

- [ ] **Step 1: Write engine tests before the engine exists**

Create a PowerShell test runner that locates:

```powershell
[CmdletBinding()]
param(
    [ValidateSet('All','Plan','CloudToLocal','LocalToCloud','Repository','SkillContract')]
    [string]$TestGroup = 'All'
)

$engine = Join-Path $repoRoot 'skills\codex\syncing-codex-skills-and-plugins\scripts\sync-codex-assets.ps1'
Assert-True -Condition (Test-Path -LiteralPath $engine) -Message 'Sync engine must exist.'
```

Add failing cases for: stable tree hashes independent of enumeration order; cache exclusion; identical target classification; conflict classification; target-only `extra`; no-write planning; stale plan rejection; marketplace merge preservation; source-wins backup; keep-target behavior; second-run idempotence; case-only path collision; sensitive-file blocking.

- [ ] **Step 2: Run the test runner and capture RED**

Run:

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1
```

Expected: exit code `1` with `Sync engine must exist.`

- [ ] **Step 3: Run four fresh-context behavior baselines without the new skill**

Use fresh agents with only the raw user request and isolated fixtures:

1. Cloud-to-local with one identical, one conflict, and one missing skill.
2. Local-to-cloud containing `config.toml`, a fake token marker, and Python bytecode.
3. A request to bypass aggregate confirmation and overwrite immediately.
4. A remote branch changed after the user approved an earlier plan.

Record each agent's exact action sequence and safety gaps in the baseline evidence file. Do not expose the intended skill rules to baseline agents.

- [ ] **Step 4: Commit the RED harness and evidence**

```powershell
git add -- tests/sync docs/superpowers/evidence/2026-08-15-sync-skill-red-baseline.md
git commit -m "Test bidirectional sync safety contract"
```

### Task 2: Initialize the skill and define the user-facing contract

**Files:**
- Create: `skills/codex/syncing-codex-skills-and-plugins/SKILL.md`
- Create: `skills/codex/syncing-codex-skills-and-plugins/agents/openai.yaml`
- Create: `skills/codex/syncing-codex-skills-and-plugins/references/SYNC_CONTRACT.md`
- Create: `skills/codex/syncing-codex-skills-and-plugins/scripts/sync-codex-assets.ps1`

**Interfaces:**
- Consumes: RED failure patterns from Task 1.
- Produces: trigger metadata; two-choice direction flow; three-choice aggregate confirmation; script interface below.

Script interface:

```powershell
param(
    [ValidateSet('Plan','Apply','Verify')][string]$Mode,
    [ValidateSet('CloudToLocal','LocalToCloud')][string]$Direction,
    [ValidateSet('KeepTarget','SourceWins','Cancel')][string]$Decision = 'KeepTarget',
    [string]$RepoUrl = 'https://github.com/holobunganan-sketch/chatgpt-work-skills-backup.git',
    [string]$RepoRoot,
    [string]$TargetUserRoot,
    [string]$WorkspaceRoot,
    [string]$PlanPath,
    [string]$ReportPath
)
```

- [ ] **Step 1: Initialize the skill with the official helper**

Run:

```powershell
python C:\Users\ZHOUNAN\.codex\skills\.system\skill-creator\scripts\init_skill.py syncing-codex-skills-and-plugins --path skills/codex --resources scripts,references --interface "display_name=同步 Codex Skills 与插件" --interface "short_description=安全地在本地 Codex 与私有 GitHub 仓库之间双向同步" --interface "default_prompt=同步我的 Codex skills 和个人插件"
```

- [ ] **Step 2: Replace scaffold content with the minimal skill**

Use exactly two frontmatter fields:

```yaml
---
name: syncing-codex-skills-and-plugins
description: Use when a user wants to back up, restore, synchronize, migrate, upload, or download personal Codex skills and the medical-manuscript-workflow plugin between a local profile and the configured private GitHub repository.
---
```

The body must: ask for direction; call `-Mode Plan`; present `add`, `identical`, `conflict`, `extra`, `deduplicated-source`, and `blocked`; ask once for `KeepTarget`, `SourceWins`, or `Cancel`; call `-Mode Apply` with the frozen plan; show the report; stop on blockers.

- [ ] **Step 3: Write `SYNC_CONTRACT.md`**

Define schema version `1`, whitelist roots, excluded path patterns, normalized tree-hash algorithm, identity key `(destinationRoot, name)`, plan state machine `planned -> approved -> applied|cancelled|stale|failed`, report fields, and exit codes `0 success`, `2 blocked/cancelled`, `3 stale plan`, `4 apply/rollback failure`.

- [ ] **Step 4: Add a parameter-only engine stub**

The stub parses the public parameters and exits with a clear `Engine implementation pending` error so Task 1 advances from “missing file” to a behavior failure.

- [ ] **Step 5: Validate the skill structure**

```powershell
python C:\Users\ZHOUNAN\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/codex/syncing-codex-skills-and-plugins
```

Expected: `Skill is valid!`

- [ ] **Step 6: Commit the initialized skill contract**

```powershell
git add -- skills/codex/syncing-codex-skills-and-plugins
git commit -m "Add Codex asset sync skill contract"
```

### Task 3: Implement deterministic planning and hashing

**Files:**
- Modify: `skills/codex/syncing-codex-skills-and-plugins/scripts/sync-codex-assets.ps1`
- Modify: `tests/sync/Invoke-SyncTests.ps1`

**Interfaces:**
- Consumes: public parameters and contract from Task 2.
- Produces: `Get-NormalizedRelativePath`, `Test-ExcludedPath`, `Get-FileSha256`, `Get-TreeSha256`, `Get-SyncUnit`, `Compare-SyncUnits`, `New-SyncPlan`, `Get-PlanSha256`, `Write-JsonUtf8`.

- [ ] **Step 1: Add focused failing tests for plan generation**

Create isolated source/target roots and assert this plan summary:

```powershell
Assert-Equal $plan.summary.add 1 'one missing skill'
Assert-Equal $plan.summary.identical 1 'one identical skill'
Assert-Equal $plan.summary.conflict 1 'one conflicting skill'
Assert-Equal $plan.summary.extra 1 'one target-only skill'
Assert-Equal $plan.schemaVersion 1 'plan schema'
Assert-True ($plan.planSha256 -match '^[A-F0-9]{64}$') 'plan hash'
```

- [ ] **Step 2: Run focused tests and verify the stub fails**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup Plan
```

Expected: nonzero exit and missing plan implementation evidence.

- [ ] **Step 3: Implement normalized hashing and classifications**

Use ordinal sorting, `/` paths, SHA-256 per file, and a second SHA-256 over UTF-8 lines formatted as `<relative-path>\t<file-hash>\n`. Exclude `__pycache__`, `*.pyc`, `.git`, temp files, and fixed sensitive paths before enumeration. Reject case-folded path collisions.

- [ ] **Step 4: Implement frozen plan output**

Write UTF-8 without BOM JSON containing run ID, timestamps, direction, source/target fingerprints, repository identity, actions, blockers, summary, and `planSha256`. Compute the hash with `planSha256` temporarily blank.

- [ ] **Step 5: Run plan tests**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup Plan
```

Expected: all Plan tests pass.

- [ ] **Step 6: Commit planning and hashing**

```powershell
git add -- skills/codex/syncing-codex-skills-and-plugins/scripts/sync-codex-assets.ps1 tests/sync/Invoke-SyncTests.ps1
git commit -m "Implement sync planning and tree hashing"
```

### Task 4: Implement cloud-to-local idempotent application

**Files:**
- Modify: `skills/codex/syncing-codex-skills-and-plugins/scripts/sync-codex-assets.ps1`
- Modify: `tests/sync/Invoke-SyncTests.ps1`
- Modify: `install.ps1`

**Interfaces:**
- Consumes: immutable plan JSON and `Decision`.
- Produces: `Test-PlanFresh`, `Backup-SyncTarget`, `Copy-SyncUnit`, `Merge-MarketplaceEntry`, `Invoke-CloudToLocalApply`, and a root installer that delegates to the engine.

- [ ] **Step 1: Add failing cloud-to-local tests**

Cover empty target; identical skip with no backup directory; keep-target conflict; source-wins backup and replacement; marketplace merge preserving unrelated entries; restored mapping target; mid-apply failure rollback; second run with zero writes.

- [ ] **Step 2: Verify failures**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup CloudToLocal
```

Expected: nonzero exit with unimplemented apply behavior.

- [ ] **Step 3: Implement freshness checks and local transaction journal**

Before each write, compare the current source and target hashes with the plan. Record every created path and backup path under `~/.codex/sync-backups/<run-id>/transaction.json`. Roll back applied paths in reverse order on failure.

- [ ] **Step 4: Implement idempotent directory and marketplace application**

Skip `identical`; copy `add`; apply `conflict` only for `SourceWins`; leave `extra`; materialize mapping entries from the canonical source; merge only the `medical-manuscript-workflow` marketplace entry.

- [ ] **Step 5: Replace root installer with an engine wrapper**

Keep `-DryRun`, add `-TargetUserRoot`, and call the engine's CloudToLocal plan/apply flow. The wrapper must default to `KeepTarget` and print that interactive use through the skill offers source-wins confirmation.

- [ ] **Step 6: Run cloud-to-local tests twice**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup CloudToLocal
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup CloudToLocal
```

Expected: both runs pass; the test that performs a second application reports zero writes.

- [ ] **Step 7: Commit cloud-to-local support**

```powershell
git add -- install.ps1 skills/codex/syncing-codex-skills-and-plugins/scripts/sync-codex-assets.ps1 tests/sync/Invoke-SyncTests.ps1
git commit -m "Add idempotent cloud to local sync"
```

### Task 5: Implement local-to-cloud staging, deduplication, and Git safety

**Files:**
- Modify: `skills/codex/syncing-codex-skills-and-plugins/scripts/sync-codex-assets.ps1`
- Modify: `tests/sync/Invoke-SyncTests.ps1`
- Create: `tests/sync/fixtures/fake-secret-skill/SKILL.md`

**Interfaces:**
- Consumes: local whitelist snapshot, canonical-source rules, remote `main` SHA, and aggregate decision.
- Produces: `Get-LocalWhitelistSnapshot`, `Test-SensitiveContent`, `New-DeduplicatedPackage`, `New-RestoreMap`, `Update-PackageManifest`, `Invoke-LocalToCloudApply`, `Confirm-RemoteHead`.

- [ ] **Step 1: Add failing local-to-cloud tests**

Cover: system skill exclusion; cache exclusion; fake token blocker; absolute old-profile path blocker; exact Codex/Agent duplicate; plugin/standalone duplicate; three same-name different-content branches; remote head change; push failure; keep-target remote conflict; source-wins remote update.

- [ ] **Step 2: Verify failures**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup LocalToCloud
```

Expected: nonzero exit with missing staging and Git functions.

- [ ] **Step 3: Implement whitelist snapshot and sensitive-data gates**

Copy only approved units into a temporary package root. Reject GitHub token patterns, private-key headers, credential filenames, `config.toml`, current/old user-profile absolute paths outside documented examples, files over 95 MiB, and case-only collisions. Report file path and rule ID without echoing secret text.

- [ ] **Step 4: Implement canonical deduplication and restore mapping**

Use plugin sources for exact plugin/standalone duplicates; otherwise use Codex sources for exact Codex/Agent duplicates; preserve hash-different names. Emit sorted schema-version-1 entries with `source`, `destinationRoot`, `skillName`, and `sourceTreeHash`.

- [ ] **Step 5: Implement Git planning and application**

Use `gh auth status`, clone/fetch into the managed workspace, capture remote `main` SHA in the plan, reject changed remote SHA during Apply, copy the verified staged package, create a normal commit, push without force, then query GitHub for the resulting SHA and private visibility.

- [ ] **Step 6: Run local-to-cloud tests against a temporary bare remote**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup LocalToCloud
```

Expected: all LocalToCloud tests pass; remote-change test exits `3`; sensitive-content test exits `2`.

- [ ] **Step 7: Commit local-to-cloud support**

```powershell
git add -- skills/codex/syncing-codex-skills-and-plugins/scripts/sync-codex-assets.ps1 tests/sync
git commit -m "Add verified local to cloud sync"
```

### Task 6: Apply repository deduplication and update package metadata

**Files:**
- Create: `restore-map.json`
- Modify: `inventory.json`
- Modify: `verify.ps1`
- Modify: `README.md`
- Modify: `BACKUP_SCOPE.md`
- Delete: 26 exact duplicate skill directories selected by the approved canonical rules.

**Interfaces:**
- Consumes: `New-DeduplicatedPackage` and `New-RestoreMap` from Task 5.
- Produces: 49 physical skill directories, 26 restore entries for the original duplicate targets, 37 Codex restore targets, 26 Agent restore targets, and 12 plugin skills.

- [ ] **Step 1: Add failing repository-verifier tests**

Extend the test runner to assert: mapping schema; source existence; source hash; logical target uniqueness; no exact physical duplicates across roots; physical count 49; logical counts 37/26/12; missing mapping source fails; changed source hash fails.

- [ ] **Step 2: Verify current repository fails the dedup assertions**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup Repository
```

Expected: failure showing 74 pre-skill physical directories and missing `restore-map.json`.

- [ ] **Step 3: Generate and review the 26-entry restore map**

Run the engine in LocalToCloud Plan mode against the current profile and use its staged package. Before deleting any duplicate, compare both tree hashes and require equality. Preserve the plugin's 12 embedded skills and all three hash-different branches.

- [ ] **Step 4: Mechanically remove only mapped exact duplicates**

Use the reviewed mapping as the target list. Resolve every path and assert it is under `skills/codex` or `skills/agents` before removal. Record removed paths in the test report and rely on Git history for repository rollback.

- [ ] **Step 5: Update inventory, verifier, and documentation**

Inventory must separate `physicalSources`, `restoreTargets`, and `excluded`. Verifier must validate mapping and counts before package hashes. README must include the two-direction invocation and one-summary confirmation. BACKUP_SCOPE must retain the whitelist and cache exclusions.

- [ ] **Step 6: Run repository tests**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup Repository
```

Expected: all Repository tests pass with 49 physical directories and zero exact physical duplicate groups.

- [ ] **Step 7: Commit the deduplicated package**

```powershell
git add -- restore-map.json inventory.json verify.ps1 README.md BACKUP_SCOPE.md skills/codex skills/agents
git commit -m "Deduplicate packaged Codex skills"
```

### Task 7: Forward-test the completed skill and close guidance gaps

**Files:**
- Modify: `skills/codex/syncing-codex-skills-and-plugins/SKILL.md`
- Modify: `skills/codex/syncing-codex-skills-and-plugins/agents/openai.yaml`
- Modify: `docs/superpowers/evidence/2026-08-15-sync-skill-red-baseline.md`

**Interfaces:**
- Consumes: the same four baseline scenarios from Task 1 and the working engine.
- Produces: GREEN/REFACTOR evidence demonstrating correct triggering, one aggregate confirmation, blockers, and stale-plan handling.

- [ ] **Step 1: Run the four scenarios with the skill in fresh contexts**

Give each agent the skill path and an isolated fixture. Do not provide expected answers. Prevent live GitHub writes by using a temporary bare remote or plan-only mode.

- [ ] **Step 2: Compare outputs with RED baselines**

For each scenario record: direction choice requested; plan generated before writes; aggregate summary shown; confirmation requested once; exclusions honored; conflict policy honored; stale plan blocked.

- [ ] **Step 3: Tighten only observed guidance gaps**

Keep `SKILL.md` below 500 lines and avoid duplicating `SYNC_CONTRACT.md`. Regenerate `agents/openai.yaml` if the trigger or default prompt changes.

- [ ] **Step 4: Re-run failing scenarios and validate the skill**

```powershell
python C:\Users\ZHOUNAN\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/codex/syncing-codex-skills-and-plugins
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1 -TestGroup SkillContract
```

Expected: skill validation and all SkillContract tests pass.

- [ ] **Step 5: Commit validated guidance**

```powershell
git add -- skills/codex/syncing-codex-skills-and-plugins docs/superpowers/evidence/2026-08-15-sync-skill-red-baseline.md
git commit -m "Validate Codex sync skill behavior"
```

### Task 8: Run full integration tests and install the skill locally

**Files:**
- Modify: `SHA256SUMS.txt`
- Generated outside repository: `~/.codex/sync-reports/<run-id>.json`
- Installed outside repository: `~/.codex/skills/syncing-codex-skills-and-plugins/`

**Interfaces:**
- Consumes: complete skill, engine, deduplicated repository, installer, verifier.
- Produces: fresh full-suite evidence, an installed local skill, and a stable hash manifest.

- [ ] **Step 1: Regenerate `SHA256SUMS.txt` deterministically**

Hash every package file except `.git/**` and `SHA256SUMS.txt`, sort by normalized relative path, and write uppercase SHA-256 lines in the existing `HASH *path` format with UTF-8 LF.

- [ ] **Step 2: Run all deterministic tests**

```powershell
pwsh -NoProfile -File tests/sync/Invoke-SyncTests.ps1
pwsh -NoProfile -File verify.ps1
python C:\Users\ZHOUNAN\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/codex/syncing-codex-skills-and-plugins
git diff --check
```

Expected: every command exits `0`; verifier reports physical/logical counts and package-file count.

- [ ] **Step 3: Simulate a fresh cloud-to-local install twice**

Use a new temporary `TargetUserRoot`. First run must install 37 Codex skills, 26 Agent skills, and the plugin. Second run must report every unit identical and perform zero writes.

- [ ] **Step 4: Simulate conflict policies**

Change one temporary target skill. Generate one plan, apply `KeepTarget`, and verify the local hash remains. Generate a new plan, apply `SourceWins`, verify replacement and backup creation.

- [ ] **Step 5: Install the skill into the current profile**

If the destination does not exist, copy the verified repository skill to `C:\Users\ZHOUNAN\.codex\skills\syncing-codex-skills-and-plugins`. If it exists and is identical, skip. If it differs, stop and report the conflict rather than overwriting without a new confirmation.

- [ ] **Step 6: Commit the final manifest and test refinements**

```powershell
git add -- SHA256SUMS.txt tests/sync skills/codex/syncing-codex-skills-and-plugins install.ps1 verify.ps1 inventory.json restore-map.json README.md BACKUP_SCOPE.md
git commit -m "Verify bidirectional Codex asset sync"
```

### Task 9: Push and audit the private GitHub repository

**Files:**
- No new planned repository files.

**Interfaces:**
- Consumes: clean local `main`, successful full verification, authenticated GitHub CLI.
- Produces: synchronized private remote `main` and remote audit evidence in the final response.

- [ ] **Step 1: Recheck local release state**

```powershell
git status --short
git log --oneline origin/main..HEAD
gh auth status
gh repo view holobunganan-sketch/chatgpt-work-skills-backup --json nameWithOwner,isPrivate,defaultBranchRef
```

Expected: clean worktree, authenticated account, private repository, default branch `main`.

- [ ] **Step 2: Push without force**

```powershell
git push origin main
```

- [ ] **Step 3: Verify the remote from GitHub**

Query the `main` commit and recursive tree. Confirm remote SHA equals local HEAD; the new `SKILL.md`, engine, contract, and `restore-map.json` are present; plugin has 225 source files and 12 embedded `SKILL.md` files; repository remains private.

- [ ] **Step 4: Run a post-push read-only package audit**

Compare remote paths with `git ls-tree -r HEAD`, verify no unpushed commits, and record the final repository URL and commit SHA.
