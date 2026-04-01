---
name: compound-engineering
version: "1.0"
description: Captures engineering patterns, mistakes, corrections, and workarounds from work sessions and saves them as persistent memory for future sessions. Turns individual learning into team knowledge.
---

# Compound Engineering Skill

Learn from sessions — capture what went wrong, what worked, and why, so the same mistakes aren't repeated.

## When to Activate

- At the end of a significant work session (when `/learn` or `/recap` is run)
- When the AI notices a pattern worth remembering (error resolved in a non-obvious way, user correction, workaround discovered)
- When the user says "remember this" or "don't do that again"

## What to Capture

### 1. Error Resolutions (highest value)

When an error took multiple attempts to resolve, capture:
- What the error was
- What was tried that didn't work
- What finally fixed it
- Why (the root cause)

**Example:**
```markdown
---
name: gitignore-negation-requires-wildcard
description: Git negation patterns (!) don't work when parent uses bare directory name
type: feedback
---

When using `!` negation in .gitignore to un-ignore specific files, the parent
directory must be ignored with `data/*` (wildcard) not `data/` (bare name).
Bare directory ignores cannot be negated.

**Why:** `data/` tells git to ignore the directory itself, so git never looks
inside it to find negated entries. `data/*` ignores the contents, allowing
negation to work on specific paths within.

**How to apply:** When writing .gitignore rules with exceptions, always use
`dirname/*` pattern for the parent, never `dirname/`.
```

### 2. User Corrections (high value)

When the user corrects the AI's approach:
- What the AI did wrong
- What the user wanted instead
- The principle behind the correction

**Example:**
```markdown
---
name: separate-commits-per-script
description: User prefers individual commits and pushes per script file, not one big commit
type: feedback
---

When pushing changes, commit and push each script separately rather than
bundling everything into one commit.

**Why:** Individual commits make it easier to review, revert, and understand
changes in the git history. Each script change should be traceable independently.

**How to apply:** After a refactoring session with multiple file changes,
ask the user if they want separate commits per file before committing.
```

### 3. Workarounds (medium value)

Non-obvious solutions to recurring problems:

**Example:**
```markdown
---
name: weasyprint-logging-suppress
description: WeasyPrint floods logs with CSS warnings — suppress with logging level
type: feedback
---

When using weasyprint for PDF generation, it produces many CSS-related warnings.
Suppress with: `logging.getLogger('weasyprint').setLevel(logging.ERROR)`

**Why:** Default weasyprint logging is very verbose and obscures real errors.

**How to apply:** Add the logging suppression right before any weasyprint calls.
```

### 4. Successful Approaches (low but important)

When an unusual approach worked well and was confirmed by the user:

**Example:**
```markdown
---
name: parallel-review-agents-effective
description: Running 3 review agents in parallel (reuse, quality, efficiency) catches more issues
type: feedback
---

Running /simplify with 3 parallel agents (code reuse, code quality, efficiency)
is effective — caught an inconsistent status-set bug that manual review missed.

**Why:** Each agent has a different focus, so they find different classes of issues.

**How to apply:** After significant code changes, run /simplify to launch
parallel review agents before pushing.
```

## How to Capture

### Step 1: Scan the Session

Review the conversation for:
- Errors that took >1 attempt to resolve
- User corrections ("no", "don't", "instead", "that's wrong")
- User confirmations of non-obvious approaches ("yes exactly", "perfect")
- Workarounds or tricks discovered
- Tool/library quirks encountered

### Step 2: Filter for Reusability

Only capture patterns that are:
- **Reusable** — will likely come up again in future sessions
- **Non-obvious** — can't be derived from reading the code or docs
- **Actionable** — tells the AI what to do differently next time

Skip patterns that are:
- One-time fixes (typos, missing imports)
- Already documented in CLAUDE.md or README
- Specific to one file/function (not generalizable)
- Obvious from context

### Step 3: Write Memory Files

For each pattern worth saving:

1. Write a memory file to the project memory directory:
   `~/.claude/projects/<project>/memory/<name>.md`

2. Add an entry to `MEMORY.md` index:
   `- [Title](filename.md) — one-line description`

3. Use the correct type:
   - `feedback` — corrections, preferences, approaches
   - `project` — project-specific facts or decisions
   - `user` — user preferences or working style

### Step 4: Report

Tell the user what was captured:
```
PATTERNS CAPTURED:
  1. [name] — one-line description
  2. [name] — one-line description

These will be available in future sessions.
```

## How to Trigger

This skill activates automatically when the AI notices reusable patterns. Users can also trigger it explicitly:
- Say "learn from this session" or "capture what we learned"
- Say `/learn` to scan the full session
- Say `/learn errors` to focus only on error resolutions
- Say `/learn corrections` to focus only on user corrections

## Anti-Patterns

- Don't capture trivial fixes (typo corrections, missing commas)
- Don't duplicate what's already in CLAUDE.md
- Don't save patterns that only apply to the current conversation
- Don't save code snippets — save the principle behind the code
- Keep memory files small (under 20 lines each)
- Update existing memories instead of creating duplicates
