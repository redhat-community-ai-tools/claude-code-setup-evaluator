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

### Step 2: Show All Available Capabilities

Present a clear overview organized by **how they're used**:

**Format the output like this:**

```
WORKSPACE TOOLKIT
=================

AUTOMATIC (I use these on my own — you don't need to do anything):
─────────────────────────────────────────────────────────────────
  verification-loop       Unified engine for /verify, /review, /quality-gate
  security-check          Credential leaks, LLM security, insecure code
  data-pipeline-patterns  Stage design, validation, debugging, circuit breakers
  api-client-patterns     Retry logic, rate limiting, API integration
  python-testing          TDD workflow + DS testing patterns
  python-patterns         Team dotenv conventions
  git-workflow            GitLab/GitHub, submodule workflow
  mcp-patterns            MCP server design, security, auth patterns
  codebase-onboarding     Analyze unfamiliar repos, map architecture
  compound-engineering    Captures session patterns as persistent memories
  deep-research         Multi-source research and analysis

COMMANDS (type these to trigger):
─────────────────────────────────
  /plan              Plan before complex work (search first, then design)
  /review            Review changed code for issues
  /verify            Confirm changes work end-to-end
  /test-coverage     Find untested code and coverage gaps
  /quality-gate      Pre-push check (tests + secrets + lint)
  /toolkit           This command — show what's available

AGENTS (I spawn these automatically for parallel/specialized work):
──────────────────────────────────────────────────────────────────
  Explore            Fast codebase search across many files
  Plan               Design implementation strategies
  general-purpose    Complex multi-step research tasks
```

### Step 3: Recommend Based on Context

Based on what the user is currently doing, suggest specific tools:

**If there are uncommitted changes:**
→ "You have changes ready. Consider `/review` to check quality, then `/quality-gate` before pushing."

**If they just cloned or are new to the repo:**
→ "New to this repo? The `codebase-onboarding` skill will activate if you ask me to explain how the project works."

**If they're in a data pipeline project (Python + JSON/YAML + API calls):**
→ "This looks like a data pipeline. `data-pipeline-patterns` and `api-client-patterns` will activate automatically when you write pipeline code."

**If there's a `.mcp.json` file:**
→ "MCP is configured here. `mcp-patterns` will help if you build or modify MCP servers."

**If tests exist:**
→ "Found tests. Run `/test-coverage` to see what's untested. `python-testing` activates automatically when writing tests."

**If there are no changes and no clear task:**
→ "Tell me what you want to work on and I'll suggest which tools to use."

### Step 4: Suggest a Workflow

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

- Keep the output scannable — use fixed-width formatting, not walls of text
- Tailor recommendations to what's actually in the repo — don't recommend MCP patterns if there's no `.mcp.json`
- If the user asks about a specific skill, explain it in detail with examples
- This command is primarily for DISCOVERY — help users who don't know what's available
