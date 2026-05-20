---
description: "Switch which repository/repositories to focus on. Re-presents the repo selection menu and completely replaces the previous selection."
---

# Focus Command

Switch repository focus mid-session.

## Instructions

### Step 1: Scan Available Repositories

```bash
# List all git repos in repositories/
for dir in repositories/*/; do
  if [ -d "$dir/.git" ]; then
    name=$(basename "$dir")
    branch=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    status=$(git -C "$dir" status --porcelain 2>/dev/null)
    if [ -n "$status" ]; then
      count=$(echo "$status" | wc -l | tr -d ' ')
      hint="$branch, $count uncommitted"
    else
      hint="$branch, clean"
    fi
    printf "  %s. %-30s (%s)\n" "$i" "$name" "$hint"
  fi
done
```

### Step 2: Present the Menu

Show the numbered list:

```
REPOSITORY FOCUS
================
  1. my-project                   (main, clean)
  2. backend-api                  (feature/add-retry, 3 uncommitted)
  3. frontend-app                 (main, clean)

Which repo(s)? (e.g. 1, 1-3, all, all except 2)
```

If there is a current focus, mark it:

```
  2. backend-api                  (feature/add-retry, 3 uncommitted)  [current]
```

### Step 3: Apply Selection

The user's response **completely replaces** the previous focus. Parse their selection:

- `2` → single repo
- `1 3` → multiple repos by number
- `1-3` → range
- `all` → all repos
- `all except 2` → all minus specific ones
- Repo names also work: `backend-api`

### Step 4: Confirm

```
Focused on: backend-api, frontend-app
```

Then continue working. Apply the same focus constraint: only read/modify files in the selected repo(s) unless the user explicitly asks otherwise.

### Step 5: Update tmux Window Name

If running inside tmux, rename the current window to reflect the focused repo(s):

```bash
# Only if inside a tmux session
if [ -n "$TMUX" ]; then
  # Single repo: use repo name
  # Multiple repos: "first-repo+N" where N is the count of additional repos
  tmux rename-window "WINDOW_NAME"
fi
```

Examples:
- 1 repo selected → `tmux rename-window "backend-api"`
- 3 repos selected → `tmux rename-window "backend-api+2"`

If not inside tmux, skip this step silently.

## Important

- This command **replaces** the current focus — it does not add to it
- Always scan the actual `repositories/` directory — never use a cached list
- If only one repo exists, auto-select it and confirm without asking
