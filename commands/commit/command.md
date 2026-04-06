---
description: "Generate an accurate, context-aware commit message from the diff and conversation context, then commit after approval."
---

# Smart Commit

Generate a commit message that explains **why** the changes were made, not just what changed. Use the conversation context from this session to understand intent.

## Instructions

### Step 1: Gather Context

```bash
# What changed
git diff --stat
git diff
git diff --cached --stat
git diff --cached

# What branch (may contain ticket ID)
git branch --show-current

# Untracked files that might need staging
git status --short
```

### Step 2: Check Scope

Look at the changes. Do they cover **one concern** or **multiple unrelated concerns**?

**If multiple concerns:**
Tell the user:
> "These changes touch multiple unrelated things: [list them]. I recommend splitting into separate commits. Want me to help stage them in groups?"

If the user agrees, help them stage one group at a time and run through Steps 3-5 for each group.

If the user says commit everything together, proceed.

### Step 3: Categorize

Based on the diff AND the conversation context from this session, determine the nature of the changes:

- **Add** — wholly new feature, file, or capability
- **Fix** — correcting broken behavior
- **Update** — enhancing or modifying existing functionality
- **Refactor** — restructuring without changing behavior
- **Remove** — deleting code, files, or features
- **Docs** — documentation only
- **Test** — test additions or changes only
- **Chore** — config, dependencies, CI, tooling

Use conversation context to get this right. If the user spent the session debugging a crash, it's a "Fix", not an "Update".

### Step 4: Generate Message

**Subject line:**
- Imperative mood ("Add retry logic" not "Added retry logic")
- Under 72 characters
- Starts with the category verb from Step 3
- Specific — name the thing that changed

**Body (when changes are non-trivial):**
- Explain **why** the change was made — the motivation, the problem it solves
- Use conversation context — you know why because you were part of the session
- Skip the body for trivial changes (typo fixes, single-line config changes)

**Ticket reference:**
- Extract ticket ID from branch name if present (e.g., `DATA-456-add-retry` -> `DATA-456`)
- Append to subject or body if found

### Step 5: Present for Approval

Show the full commit preview:

```
COMMIT PREVIEW
══════════════
Branch: [branch name]
Ticket: [ticket ID if found, or "none"]

  [commit message]

Files to stage:
  [list of files]

Commit with this message? (yes / edit / cancel)
```

**If "yes":** Stage the listed files by name (NEVER use `git add -A` or `git add .`) and commit.

**If "edit":** Ask what to change, update the message, show preview again.

**If "cancel":** Stop. Do not commit.

## Important

- **Never commit without showing the preview first.**
- **Never stage with `git add -A` or `git add .`** — always stage specific files by name.
- **Never stage `.env` files, credentials, or secrets.** If these appear in the diff, warn the user and exclude them.
- **Use conversation context.** The biggest advantage you have over a diff-only tool is that you know WHY changes were made. Use it.
- The user may pass arguments: `/commit just the tests` or `/commit only jira_client.py` — respect scope restrictions.

## Arguments

$ARGUMENTS can specify:
- Scope restriction: `/commit only src/` or `/commit just the tests`
- Quick mode: `/commit quick` — skip the preview, commit immediately (still generate a good message)
