---
description: "Show available skills, agents, and commands — and recommend which to use based on the current repo and task. Helps new users discover what capabilities are available."
---

# Toolkit Command

Help the user understand what tools are available and which ones to use right now.

## Instructions

### Step 1: Analyze Current Context

Quickly assess where the user is and what they might be working on:

```bash
# What repo are we in?
basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || echo "Not in a git repo"

# What changed recently?
git diff --name-only HEAD 2>/dev/null | head -10
git status --short 2>/dev/null | head -10

# What kind of project is this?
ls *.py pyproject.toml requirements*.txt config.yaml .env.example .mcp.json 2>/dev/null
```

### Step 2: Discover Available Capabilities

Dynamically scan the workspace to find what's actually installed — never use a hardcoded list.

**Find skills:**
```bash
# List all skills and their descriptions
for skill_dir in skills/*/; do
  skill_file="$skill_dir/SKILL.md"
  if [ -f "$skill_file" ]; then
    name=$(basename "$skill_dir")
    desc=$(grep -A1 "^description:" "$skill_file" | tail -1 | sed 's/^[[:space:]]*//' | cut -c1-70)
    printf "  %-25s %s\n" "$name" "$desc"
  fi
done
```

**Find commands:**
```bash
# List all commands and their descriptions
for cmd_dir in commands/*/; do
  cmd_file="$cmd_dir/command.md"
  if [ -f "$cmd_file" ]; then
    name=$(basename "$cmd_dir")
    desc=$(grep "^description:" "$cmd_file" | head -1 | sed 's/description:[[:space:]]*"//;s/"$//' | cut -c1-60)
    printf "  /%-24s %s\n" "$name" "$desc"
  fi
done
```

### Step 3: Present Capabilities

Present a clear overview organized by **how they're used**, populated from the scan results above:

```
WORKSPACE TOOLKIT
=================

SKILLS (activate automatically — you don't need to do anything):
────────────────────────────────────────────────────────────────
  [name]                  [description from SKILL.md]
  ...

COMMANDS (type these to trigger):
─────────────────────────────────
  /[name]              [description from command.md]
  ...

AGENTS (I spawn these automatically for parallel/specialized work):
──────────────────────────────────────────────────────────────────
  Explore            Fast codebase search across many files
  Plan               Design implementation strategies
  general-purpose    Complex multi-step research tasks
```

### Step 4: Recommend Based on Context

Based on what the user is currently doing, suggest specific tools:

**If there are uncommitted changes:**
→ "You have changes ready. Consider `/review` to check quality, then `/quality-gate` before pushing."

**If they just cloned or are new to the repo:**
→ "New to this repo? Ask me to explain how the project works and I'll onboard you."

**If they're in a data pipeline project (Python + JSON/YAML + API calls):**
→ "This looks like a data pipeline. `data-pipeline-patterns` and `python-conventions` will activate automatically when you write pipeline code."

**If there's a `.mcp.json` file:**
→ "MCP is configured here. The `mcp-patterns` agent-doc will help if you build or modify MCP servers."

**If tests exist:**
→ "Found tests. Run `/test-coverage` to see what's untested."

**If there are failing tests or recent errors:**
→ "Looks like something is broken. The `systematic-debugging` skill will activate — it follows a structured root cause analysis instead of guessing."

**If files are large or complex (>300 lines, deep nesting):**
→ "Some files here are getting complex. When you're ready to clean up, `refactoring-patterns` will guide measurement-driven refactoring."

**If there are no changes and no clear task:**
→ "Tell me what you want to work on and I'll suggest which tools to use."

### Step 5: Suggest a Workflow

End with a recommended workflow for their situation:

```
SUGGESTED WORKFLOW:
  1. /plan          — align on approach before coding
  2. (write code)   — skills activate automatically
  3. /review        — check the changes
  4. /verify        — confirm it works
  5. /quality-gate  — pre-push safety check
```

## Important

- **Never hardcode skill or command lists** — always scan `skills/` and `commands/` directories dynamically
- Keep the output scannable — use fixed-width formatting, not walls of text
- Tailor recommendations to what's actually in the repo — don't recommend MCP patterns if there's no `.mcp.json`
- If the user asks about a specific skill, explain it in detail with examples
- This command is primarily for DISCOVERY — help users who don't know what's available
