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
