# How Evaluate-Setup Works

This document explains what happens when you run `/evaluate-setup` — the health check for your Claude Code setup.

---

## Step 0: Ask one question

Claude asks: **"Terminal or file?"** That's the only question. Then it starts.

If you choose file, the report is saved to `evaluation-results/evaluate-setup-YYYY-MM-DD-HHMM.md`.

---

## Step 1: Layer 1 — the Python tool runs

Claude runs one command:

```bash
uv run --project "$PROJECT_DIR" evaluate-setup scan .
```

Behind that one command, a Python project does this:

### Discovery

It walks the directory tree and finds everything in your setup:

- `SKILL.md` files → skills
- `commands/*/command.md` files → commands (skips the evaluator's own commands)
- `CLAUDE.md` / `CLAUDE.local.md` → CLAUDE.md files (also checks parent directory)
- `.claude/settings.json` / `.claude/settings.local.json` → hooks
- `agents/*.md` files → agents (also detects agents by frontmatter if no `agents/` directory exists)

It skips anything inside a nested git repo (cloned projects, submodules) — those aren't part of your setup.

### Rules

Each item gets checked by a set of Python rules — 21 rules across 5 file types. Every rule checks one specific thing mechanically — no AI involved, fully deterministic, same input always produces same output.

**Skills get 9 rules:**

| Rule | What it checks |
|------|---------------|
| SKILL.md exists | The skill directory contains a SKILL.md file |
| Description required | Description field exists and is not empty |
| Description quality | Third-person POV, includes use-case context ("use when", "applies to"), length between 20 and 1,024 characters |
| Frontmatter valid | YAML frontmatter parses correctly, name matches directory |
| Token budget | SKILL.md is under the token limit and under 500 lines |
| Broken references | All file links and references point to files that exist |
| Duplicate detection | No other skill is >85% similar (TF-IDF cosine similarity) |
| No prompt injection | No patterns that could hijack Claude's behavior (context-aware: downgrades in code blocks) |
| No credential access | No references to ~/.ssh, ~/.aws, $API_KEY, sudo, chmod 777, dangerous commands |

**Commands get 6 rules:**

| Rule | What it checks |
|------|---------------|
| Description required | Description field exists for the UI menu, not too vague |
| Script exists | Referenced script files actually exist |
| Skill overlap | No command is >60% similar to a skill body (cross-type duplication) |
| Duplicate detection | No other command is >85% similar (TF-IDF cosine similarity) |
| No prompt injection | Same pattern check as skills |
| No credential access | Same credential/dangerous command check as skills |

**CLAUDE.md gets 2 rules:**

| Rule | What it checks |
|------|---------------|
| File exists | CLAUDE.md is present in the project |
| Skill duplication | No section has high word overlap with a skill body (wasted tokens) |

**Hooks get 1 rule:**

| Rule | What it checks |
|------|---------------|
| Valid structure | Commands exist, no dangerous patterns (rm -rf, git push --force, curl\|bash), scripts exist |

**Agents get 6 rules:**

| Rule | What it checks |
|------|---------------|
| Description required | Description field exists and is not empty |
| Referenced skills exist | Every skill listed in frontmatter has a matching SKILL.md |
| DisallowedTools format | Entries match ToolName or ToolName(pattern) format |
| Constraint-body match | Body constraints ("cannot push") are backed by disallowedTools |
| No prompt injection | Same pattern check as skills |
| No credential access | Same credential check as skills |

### Output

The tool outputs JSON — every item with its diagnostics (rule ID, severity, message, file, line number), token counts, and error/warning totals.

---

## Step 2: Claude reads everything

Claude takes the JSON from Layer 1, then reads the actual files:

- Every SKILL.md
- Every reference file in `skills/` subdirectories (the detailed content behind progressive disclosure)
- Every `guidelines.md` (behavioral rules)
- Every command.md
- Every agent .md file
- Every hook entry in settings.json
- The CLAUDE.md

Layer 1 catches mechanical issues. Claude needs the actual content to judge quality.

---

## Step 3: Layer 2 — Claude scores everything

Claude follows rubric instructions and scores each item on weighted dimensions.

### Skills get 5 dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Specificity | 0.25 | Are instructions concrete and actionable? |
| Redundancy | 0.25 | Does this teach Claude something it doesn't already know? |
| Trigger quality | 0.20 | Will the description activate at the right time? |
| Token efficiency | 0.15 | Is the size justified by the value? |
| Content quality | 0.15 | Structure, examples, error handling? |

Weighted average → star rating → verdict: **KEEP** (4-5 stars), **REVIEW** (3 stars), **REMOVE** (1-2 stars).

### Commands get 7 dimensions:

Description quality, instruction clarity, script integrity, scope appropriateness, token efficiency, redundancy with defaults, robustness.

### CLAUDE.md gets 5 dimensions:

Conciseness, signal-to-noise, skill separation, structure, conflict-free.

### Hooks get checked for:

Purpose, script existence, dangerous patterns, and whether a hook is the right mechanism.

### Agents get 5 dimensions:

Specificity, constraint clarity, zero-trust integrity, token efficiency, content quality.

---

## Step 4: Cross-type analysis — the full picture

Claude looks at the whole setup together and runs 21 checks:

### Transformations (11 checks)

| # | Check | Question |
|---|-------|----------|
| 1 | Skill → Hook | Should any skill be a hook instead? (advisory vs. guaranteed) |
| 2 | Skill → Command | Should any skill be a command instead? (passive vs. user-triggered) |
| 3 | Command → Skill | Should any command be a skill instead? (explicit trigger vs. auto-trigger) |
| 4 | Skill content → CLAUDE.md | Are there universal rules in skills that belong in CLAUDE.md? |
| 5 | CLAUDE.md content → Skill | Are there domain-specific rules in CLAUDE.md that waste context every session? |
| 6 | CLAUDE.md content → Hook | Are there rules Claude sometimes forgets that should be deterministic hooks? |
| 7 | Agent ↔ Skill consistency | Do agent-referenced skills exist? Do instructions conflict? |
| 8 | Agent ↔ Agent overlap | Do multiple agents share large identical text blocks? |
| 9 | Agent ↔ CLAUDE.md | Are rules placed in the right layer? |
| 10 | Skill structure optimization | Should any large skill split into thin SKILL.md + reference files? |
| 11 | Guidelines extraction | Should any skill extract hard limits to a separate guidelines.md? |

### Setup-wide (7 checks)

| # | Check | Question |
|---|-------|----------|
| 12 | Merge candidates | Are there skills covering related topics that would be stronger combined? |
| 13 | Overlapping triggers | Do multiple skill descriptions trigger on the same tasks? |
| 14 | Coverage gaps | Are there obvious missing areas based on what's present? |
| 15 | Total context budget | Do all skills + CLAUDE.md + commands exceed 20% of context window? |
| 16 | Redundancy across types | Does the same instruction appear in both CLAUDE.md and a skill? |
| 17 | Conflicts across types | Does CLAUDE.md say one thing while a skill says the opposite? |
| 18 | Command shadows built-in | Does any command share a name with a Claude Code built-in slash command? |

### Behavioral patterns (3 checks)

| # | Check | Question |
|---|-------|----------|
| 19 | Mandate stacking | Do >2 skills use coercive language (MUST/ALWAYS/NEVER) creating competing demands? |
| 20 | Autonomy erosion | Do any broad-trigger skills contain hard gates that block the user's workflow? |
| 21 | Broad trigger collision | Do multiple skills individually cast too wide a net? |

Each check gets an explicit **YES** or **NO** answer with a one-line explanation.

---

## Step 5: Report

Claude writes the final report:

- **If file**: saves to `evaluation-results/evaluate-setup-YYYY-MM-DD-HHMM.md`
- **If terminal**: prints the full report directly

Either way, Claude always prints a **short summary at the end** in the terminal — the bottom line, total counts, and numbered suggestions the user can act on by saying "do 1", "do 2", etc.

---

## What's in the report

For each item:

1. **Stars and verdict** (★★★★★ KEEP / ★★★ REVIEW / ★★ REMOVE)
2. **Layer 1 checklist** — pass/fail for each Python rule that ran on that item
3. **Rubric scores** — the 4 evaluation dimensions (Readiness, Correctness, Redundancy, Compliance) with per-dimension scores and one-sentence justifications
4. **Bullets** — what's good (+), what could improve (!), what's broken (x)

Then the cross-type analysis with all 20 checks answered, and finally the numbered suggestions.
