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
