# Repo Ready Check — Design Spec

## Problem

When starting work on a repository, there's no guardrail to ensure:
1. The local branch is up to date with the remote (avoiding conflicts and stale work)
2. The developer isn't about to make changes directly on the default branch (main/master)

The workspace's session-start hook already fetches from remotes and reports sync status in the session context (`<repository-status>` XML), but nothing acts on that data to warn the user or offer corrective actions.

## Solution

A single skill (`repo-ready-check`) that covers two pre-work validations for focused repositories, plus a command (`/repo-sync`) for manual on-demand sync checks.

## Components

| Component | Path | Purpose |
|-----------|------|---------|
| Skill | `skills/repo-ready-check/SKILL.md` | Instructions for Claude: sync check at session start + branch protection before edits |
| Command | `commands/repo-sync/command.md` | Manual trigger for on-demand sync check |

## Behavior

### Check 1: Sync Freshness (session start + manual)

**Trigger:** At session start (automatic, via skill reading session context) or on `/repo-sync` invocation.

**Scope:** Only focused repositories (selected via `/focus`). If none selected, the repo being actively worked in.

**When repo is behind the remote:**
- Warn: "Repository `<name>` is **N commits behind** `origin/<branch>`"
- Offer: "Want me to pull the latest changes before we start?"
- If accepted: run `git pull --rebase origin <branch>`

**When repo has uncommitted changes:**
- Warn: "Repository `<name>` has **uncommitted changes**"
- List changed files briefly
- Note: "Consider committing or stashing before pulling"

**When both conditions exist:**
- Show both warnings together
- Recommend: stash → pull → unstash, or commit first → pull

**When everything is up to date:**
- Brief confirmation: "Repo is up to date with remote" (no noise)

### Check 2: Branch Protection (before file changes)

**Trigger:** Before Claude makes any file modification (edit, write, create) in a focused repo.

**Scope:** Only focused repositories.

**When on default branch (main/master):**
- Warn: "You're on `main` — changes directly on the default branch are risky"
- Offer: "Want me to create a feature branch before making changes? What should I name it?"
- If accepted: run `git checkout -b <branch-name>`
- If declined: proceed without blocking (user's choice)

**When already on a feature branch:**
- No action, no output.

### Manual Command: `/repo-sync`

Runs the sync freshness check (Check 1) on demand. Does not include the branch protection check (that triggers separately before edits).

**Steps:**
1. Identify focused repo(s)
2. Run `git fetch` on each
3. Check behind count and uncommitted status
4. Present warnings and offer to pull (same flow as session-start check)

## Data Sources

- **Session start:** The existing `SessionStart` hook injects `<repository-status>` with `behind="N"` and `uncommitted-changes="true/false"` per repo. The skill reads this data — no hook changes needed.
- **Manual `/repo-sync`:** Runs `git fetch`, `git rev-list --count HEAD..@{u}`, and `git status --porcelain` directly.
- **Branch protection:** Runs `git rev-parse --abbrev-ref HEAD` and compares against the default branch (from session context or `git symbolic-ref refs/remotes/origin/HEAD`).

## What This Does NOT Do

- Does not modify the session-start hook or any existing scripts
- Does not auto-pull without user consent
- Does not block work — warns and offers
- Does not check non-focused repos
- Does not enforce server-side branch protection

## Flow

```
Session start
  → Session hook reports repo status in context
  → Skill reads context for focused repos
  → If behind or dirty → warn + offer to pull
  → If clean → brief confirmation

Before file changes in focused repo
  → Skill checks current branch
  → If on default branch → warn + offer to create feature branch
  → If on feature branch → proceed silently

Manual /repo-sync
  → Fetch + check focused repos
  → Same warn + offer flow as session start
```
