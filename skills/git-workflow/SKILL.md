---
name: git-workflow
version: "1.0"
description: Team-specific git conventions for GitLab and GitHub workflows and commit practices. Kept short — will be expanded as the team defines more conventions.
---

# Git Workflow — Team Conventions

Team-specific git patterns. Claude already knows git basics — this covers what's specific to our setup.

## When to Activate

- When committing, pushing, or creating MRs/PRs
- When resolving merge conflicts
- When handling git operations across GitLab and GitHub repos

## Platforms

The team uses both **GitLab** (primary, for internal repos) and **GitHub** (for open-source and some projects). Use the appropriate CLI:
- GitLab: `glab` CLI or git push + web UI for MRs
- GitHub: `gh` CLI for PRs

## Working in Repositories

Repos in `repositories/` are regular clones — not submodules. Commit and push directly from within the repo:

```bash
cd repositories/<repo>
git add <files> && git commit -m "message"
git push origin <branch>
```

Changes push to that repo's own remote. The workspace repo is not involved.

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
