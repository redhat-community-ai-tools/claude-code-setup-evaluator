# Repo Ready Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a skill and command that verify focused repositories are up to date with remote and on the correct branch before starting work.

**Architecture:** A SKILL.md file instructs Claude to (1) read session-start context for sync status and warn/offer to pull, and (2) check the current branch before file edits and warn/offer to create a feature branch. A separate command.md provides manual on-demand sync checking. No scripts or hook changes needed — the skill is pure documentation that Claude follows.

**Tech Stack:** Markdown (SKILL.md, command.md), git CLI commands, workspace transpile scripts for distribution.

**Spec:** `docs/superpowers/specs/2026-05-13-repo-ready-check-design.md`

---

### Task 1: Create the `repo-ready-check` skill

**Files:**
- Create: `skills/repo-ready-check/SKILL.md`

This is the core deliverable. The skill must cover two checks: sync freshness (at session start) and branch protection (before file edits).

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p skills/repo-ready-check
```

- [ ] **Step 2: Write `SKILL.md`**

Create `skills/repo-ready-check/SKILL.md` with the following content:

```markdown
---
name: repo-ready-check
description: Use when starting work on a repository or before making file changes. Checks if focused repos are behind the remote, have uncommitted changes, or are on the default branch (main/master). Warns and offers corrective actions.
---

# Repo Ready Check

Verify focused repositories are ready for work: synced with remote and on the correct branch.

## Check 1: Sync Freshness

**When:** At session start — before doing any work on focused repositories.

**How:** Read the `<repository-status>` data injected by the session-start hook. For each focused repo, check the `behind` and `uncommitted-changes` attributes.

**If a repo is behind the remote (`behind` > 0):**

> Repository `<name>` is **N commits behind** `origin/<branch>`.
> Want me to pull the latest changes before we start?

If user accepts, run:

```bash
cd repositories/<name>
git pull --rebase origin <branch>
```

**If a repo has uncommitted changes (`uncommitted-changes="true"`):**

> Repository `<name>` has **uncommitted changes**.

List changed files:

```bash
cd repositories/<name>
git status --short
```

> Consider committing or stashing these changes before pulling.

**If both behind AND uncommitted changes:**

Show both warnings together. Recommend:

> You have uncommitted changes and are behind the remote. Options:
> 1. Stash changes → pull → unstash: `git stash && git pull --rebase && git stash pop`
> 2. Commit first → then pull: `git add . && git commit -m "wip" && git pull --rebase`

**If everything is up to date:**

> Repo `<name>` is up to date with remote.

Keep this brief — one line, no noise.

## Check 2: Branch Protection

**When:** Before making any file modification (edit, write, create) in a focused repository. Check once per repo per session — do not repeat after the first check.

**How:** Determine the current branch and the default branch for the repo.

```bash
cd repositories/<name>
git rev-parse --abbrev-ref HEAD
```

Compare against the default branch from session context (`default-branch` attribute in `<repository-status>`) or detect it:

```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'
```

If detection fails, assume `main`.

**If on default branch (main/master):**

> You're on `<default-branch>` — making changes directly on the default branch is risky.
> Want me to create a feature branch before making changes? What should I name it?

If user provides a name, run:

```bash
cd repositories/<name>
git checkout -b <branch-name>
```

If user declines, proceed without blocking.

**If already on a feature branch:**

No action, no output. Proceed silently.

## Scope

- Only check repositories selected via `/focus`
- If no repos are focused, check the repo being actively worked in
- Never check non-focused repos under `repositories/`
```

- [ ] **Step 3: Validate the skill**

```bash
uv run .ai-workspace/scripts/transpile-skills.py --validate
```

Expected: validation passes with no errors for `repo-ready-check`.

- [ ] **Step 4: Distribute the skill**

```bash
uv run .ai-workspace/scripts/transpile-skills.py
```

Expected: symlinks created in configured target directories.

- [ ] **Step 5: Commit**

```bash
git add skills/repo-ready-check/SKILL.md
git commit -m "feat: add repo-ready-check skill for sync and branch protection"
```

---

### Task 2: Create the `/repo-sync` command

**Files:**
- Create: `commands/repo-sync/command.md`

This command provides manual on-demand sync checking (Check 1 from the skill). It does not include branch protection — that triggers separately before edits.

- [ ] **Step 1: Create the command directory**

```bash
mkdir -p commands/repo-sync
```

- [ ] **Step 2: Write `command.md`**

Create `commands/repo-sync/command.md` with the following content:

```markdown
---
description: "Check if focused repositories are up to date with the remote. Fetches latest changes and warns about repos that are behind or have uncommitted changes."
---

# Repo Sync Check

Check focused repositories for sync freshness with the remote.

## Instructions

### 1. Identify Focused Repos

Determine which repositories to check:
- If repos are selected via `/focus`, check those
- If no repos are focused, check the repo the user is currently working in
- If no repo context is available, ask the user which repo to check

### 2. Fetch and Check Each Repo

For each repo, run:

```bash
cd repositories/<name>
git fetch --quiet
```

Then check behind count:

```bash
git rev-list --count HEAD..@{u} 2>/dev/null || echo "no upstream"
```

And check for uncommitted changes:

```bash
git status --porcelain
```

### 3. Report Results

**If behind the remote:**

> Repository `<name>` is **N commits behind** `origin/<branch>`.
> Want me to pull the latest changes?

If user accepts:

```bash
git pull --rebase origin <branch>
```

**If uncommitted changes exist:**

> Repository `<name>` has **uncommitted changes**:

Show the output of `git status --short`.

> Consider committing or stashing before pulling.

**If both behind AND dirty:**

Show both warnings. Recommend stash → pull → unstash or commit → pull.

**If up to date and clean:**

> Repository `<name>` is up to date with remote. No uncommitted changes.

### 4. Summary

If checking multiple repos, end with a summary:

```
Repo Sync Summary
=================
repo-a:    UP TO DATE
repo-b:    3 commits behind (offered to pull)
repo-c:    UP TO DATE, 2 uncommitted changes
```

## Arguments

$ARGUMENTS can be:
- A repo name or path (e.g., `lab` or `repositories/lab`) — check that repo specifically
- Empty — check all focused repos
```

- [ ] **Step 3: Validate the command**

```bash
uv run .ai-workspace/scripts/transpile-commands.py --validate
```

Expected: validation passes with no errors for `repo-sync`.

- [ ] **Step 4: Distribute the command**

```bash
uv run .ai-workspace/scripts/transpile-commands.py
```

Expected: symlinks created in `.claude/commands/`.

- [ ] **Step 5: Commit**

```bash
git add commands/repo-sync/command.md
git commit -m "feat: add /repo-sync command for manual sync checking"
```

---

### Task 3: Regenerate workspace files and final validation

**Files:**
- Modify: `CLAUDE.md` (auto-generated by align script — will pick up new skill/command)

- [ ] **Step 1: Regenerate workspace files**

```bash
uv run .ai-workspace/scripts/align-workspace.py
```

Expected: CLAUDE.md is regenerated with the new skill listed in the skills section and the new command listed in the commands section.

- [ ] **Step 2: Verify CLAUDE.md includes the new components**

```bash
grep -c "repo-ready-check\|repo-sync" CLAUDE.md
```

Expected: at least 1 match (confirms the new skill/command appears).

- [ ] **Step 3: Run pre-commit to validate everything**

```bash
uv run pre-commit run --all-files
```

Expected: all checks pass.

- [ ] **Step 4: Commit any generated changes**

```bash
git add -A
git commit -m "chore: regenerate workspace files with repo-ready-check skill"
```

---

### Task 4: Manual smoke test

No automated tests for a documentation-only skill — validate by exercising the behavior manually.

- [ ] **Step 1: Verify skill is listed**

Start a new Claude Code session or check that `repo-ready-check` appears in the available skills list.

- [ ] **Step 2: Test sync check**

Pick a repo that is behind its remote (e.g., `repositories/claude_code` which shows `behind="40"` in the current session context). Verify Claude warns about it and offers to pull.

- [ ] **Step 3: Test branch protection**

Switch to `main` in a focused repo and attempt a file edit. Verify Claude warns about being on the default branch and offers to create a feature branch.

- [ ] **Step 4: Test `/repo-sync` command**

Run `/repo-sync` manually and verify it fetches, checks, and reports sync status for focused repos.
