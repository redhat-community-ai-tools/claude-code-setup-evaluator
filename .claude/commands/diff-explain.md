---
description: "Explain a git diff or branch comparison in plain language. Describes the intent behind changes, not just what files were modified. Useful for MR reviews and catching up."
---

# Diff Explain Command

Explain code changes in plain language — what was done and why.

## Instructions

### Step 1: Get the Diff

Determine what to explain based on arguments:

- **No arguments**: explain uncommitted changes (`git diff` + `git diff --staged`)
- **Branch name**: explain difference from that branch (`git diff main...HEAD`)
- **Commit range**: explain those commits (`git log --oneline <range>`)
- **MR/PR number**: fetch and explain that MR

```bash
# Default: uncommitted changes
git diff --stat
git diff

# Or: branch comparison
git log --oneline main..HEAD
git diff main...HEAD --stat
```

### Step 2: Analyze and Explain

For each logical group of changes, explain:

1. **What changed** — in plain language, not file names
2. **Why** — the intent behind the change (infer from commit messages, code context, and patterns)
3. **Impact** — what this means for the project (new capability, bug fix, refactor, etc.)

### Step 3: Format the Explanation

```
CHANGES EXPLAINED
=================

SUMMARY:
  [1-2 sentences capturing the overall intent of all changes]

CHANGE 1: [descriptive title]
  What: [plain language description]
  Why:  [inferred intent]
  Files: [list of affected files]

CHANGE 2: [descriptive title]
  What: [plain language description]
  Why:  [inferred intent]
  Files: [list of affected files]

...

OVERALL IMPACT:
  - [What's new or different for users of this code]
  - [Any breaking changes or things to be aware of]
  - [What to test]
```

## Examples

**Input:** `/diff-explain`
**Output:**
```
CHANGES EXPLAINED
=================

SUMMARY:
  The monolithic epic analysis script was split into 3 independent
  pipeline steps, and closed issues are now kept for context
  instead of being discarded.

CHANGE 1: Split summarize_epics.py into 3 scripts
  What: The script that grouped issues, analyzed epics, and filtered
        tasks was split into group_issues.py (grouping only),
        summarize_epics.py (epic analysis only), and
        filter_standalone_tasks.py (task filtering only).
  Why:  Each step can now be run and debugged independently.
        Skipping one step doesn't require skipping the others.
  Files: scripts/group_issues.py (new), scripts/summarize_epics.py,
         scripts/filter_standalone_tasks.py (new), main.py

CHANGE 2: Keep closed issues as lightweight entries
  What: Previously, 66% of fetched records were discarded because
        they were closed. Now they're kept with just title, assignee,
        and dates — no description or comments.
  Why:  The AI can now see the full picture of what was accomplished
        vs what's still in progress, giving richer executive reports.
  Files: scripts/fetch_data.py, prompts/epic_prompts.py,
         prompts/category_prompts.py
```

## Important

- Group changes by **intent**, not by file — multiple files often serve one purpose
- Use plain language a non-developer could understand
- Infer the "why" from commit messages, code patterns, and naming
- If changes are large, prioritize the most impactful ones
- Don't list every line changed — describe the meaningful patterns

## Arguments

$ARGUMENTS can be:
- Empty (default: uncommitted changes)
- A branch name: `/diff-explain main`
- A commit range: `/diff-explain HEAD~5..HEAD`
- A commit hash: `/diff-explain abc1234`
