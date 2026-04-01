---
name: git-workflow
version: "1.0"
description: Team-specific git conventions for GitLab and GitHub workflows, submodule handling, and commit practices. Kept short — will be expanded as the team defines more conventions.
---

# Git Workflow — Team Conventions

Team-specific git patterns. Claude already knows git basics — this covers what's specific to our setup.

## When to Activate

- When committing, pushing, or creating MRs/PRs
- When working with submodules
- When resolving merge conflicts
- When handling git operations across GitLab and GitHub repos

## Platforms

The team uses both **GitLab** (primary, for internal repos) and **GitHub** (for open-source and some projects). Use the appropriate CLI:
- GitLab: `glab` CLI or git push + web UI for MRs
- GitHub: `gh` CLI for PRs

## Submodule Workflow

This workspace uses git submodules. **Always push submodule before parent:**

```bash
# 1. Commit and push inside the submodule
cd repositories/<submodule>
git add <files> && git commit -m "message"
git push origin main

# 2. Then update parent
cd ../..
git add repositories/<submodule>
git commit -m "Update <submodule> reference"
git push origin main
```

**Common submodule pitfalls:**
- **Detached HEAD**: If you're in detached HEAD inside a submodule, create a branch first: `git checkout -b <branch>`
- **Forgot to push submodule**: Just push the submodule now — parent reference is already correct
- **Don't run** `git submodule update --remote` during regular work — it updates pinned references

## Commit Conventions

<!-- TODO: Team to define preferred commit message format -->
- Keep commits focused — one logical change per commit
- Write clear commit messages explaining **why**, not just what
- For multi-file refactors, consider separate commits per script for easier review

## Branch Conventions

<!-- TODO: Team to define branching strategy -->
- Work on feature branches, not main
- Open MRs/PRs for code review before merging

## Conflict Resolution

- When conflicts happen, investigate before discarding changes
- For generated files (reports, data): usually keep the newer version
- For code: resolve manually, understanding both sides
- After resolving: `git add <resolved-files> && git rebase --continue`
