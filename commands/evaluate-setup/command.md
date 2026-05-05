---
description: "Evaluate your Claude Code setup — skills, commands, CLAUDE.md. Identifies what to keep, remove, merge, and fix."
---

# /evaluate-setup

You are running **the-evaluator** — a health check for Claude Code setups. You will evaluate skills, commands, and CLAUDE.md files, then produce a report with verdicts and recommendations.

## Hard Rules

1. **Never give a verdict without running the rubric.** You MUST read the actual file content and score all rubric dimensions before assigning a star rating or verdict. Layer 1 error/warning counts are input data, not the verdict — a file with 10 false-positive warnings can still be ★★★★★.
2. **Every item must have a full rubric score block.** If a rubric score block is missing for any evaluated item, the review is incomplete. Every skill, command, CLAUDE.md, and hook MUST have all dimensions scored with one-sentence justifications before the verdict line. No exceptions, no shortcuts.
3. **Read before you judge.** Do not summarize an item based on Layer 1 output alone. You must read the actual file content to evaluate quality, clarity, and redundancy. Layer 1 catches mechanical issues. Layer 2 catches everything else.
4. **Don't manufacture problems.** If the setup is good, say so. Not every run needs to produce a list of changes. A healthy setup with minor cosmetic issues should get a clear "your setup is solid" verdict — not a long list of suggestions that creates unnecessary work. Only recommend changes that would make a real difference. "You could trim 50 tokens from this skill" is not a real recommendation. "This skill duplicates another and wastes 1,000 tokens every session" is.
5. **Always end with a short summary.** Regardless of output format, the last thing the user sees in the terminal must be a short summary (see Step 5b). The full review is either above in the terminal or saved to a file — the summary tells the user the bottom line and where to find details.

## Step 0: Ask the User Before Starting

This is a two-round question flow. Ask round 1 first, then ask round 2 based on the answers.

### Round 1: Ask these 3 questions together in a single AskUserQuestion call

1. **Scope:** "What do you want to evaluate on Layers 1+2?"
   - **Everything** — skills + commands + CLAUDE.md + hooks
   - **Skills only**
   - **A specific item** — ask which one

2. **Layers:** "Which layers do you want to run?"
   - **All (1 + 2 + 3)** — static analysis, rubric scoring, and A/B redundancy testing
   - **Layers 1 + 2** — static analysis and rubric scoring (no A/B testing)
   - **Layer 3 only** — A/B redundancy testing only (skip static analysis and rubric)

3. **Output:** "Where do you want the report?"
   - **Terminal** — print everything here
   - **File** — save to a file (recommended for full scans)

Wait for answers before proceeding to round 2.

### Round 2: Follow-up questions (based on round 1 answers)

**If the user chose "All" or "Layer 3 only" for layers:** Ask a follow-up question using AskUserQuestion to select which skills to A/B test in Layer 3. The scope from question 1 applies to Layers 1+2 only — Layer 3 always requires explicit skill selection because not all skills are good A/B candidates.

Present the skill list with recommendations. Pre-check skills that teach concrete patterns or rules. Un-check workflow orchestrators, format definitions, or skills that scored too low to justify the cost:

```
Which skills should Layer 3 (A/B testing) evaluate?

  1. [x] data-pipeline-patterns    — good candidate (teaches specific patterns)
  2. [x] python-conventions        — good candidate (teaches specific rules)
  3. [x] security-check            — good candidate (preventive, can red-team)
  4. [ ] brainstorming             — poor candidate (workflow gate, not single-turn)
  5. [ ] writing-plans             — poor candidate (document format, not testable)
  6. [ ] verification-loop         — poor candidate (orchestrates tools, not single-turn)

Select by number (e.g. 1-3, all, 1 2 5):
```

**If the user chose file output:** Check if `evaluate-setup-report.md` already exists. If it does, ask the user for a different filename — do NOT overwrite existing reports.

### Flow matrix

| Scope | Layers | What runs |
|---|---|---|
| Everything | All | L1 all → L2 all → L3 selected skills |
| Everything | 1 + 2 | L1 all → L2 all |
| Everything | 3 only | L3 selected skills only |
| Skills only | All | L1 skills → L2 skills → L3 selected skills |
| Skills only | 1 + 2 | L1 skills → L2 skills |
| Skills only | 3 only | L3 selected skills only |
| Specific item | All | L1 + L2 + L3 on that item |
| Specific item | 1 + 2 | L1 + L2 on that item |
| Specific item | 3 only | L3 on that item |

## Arguments

`$ARGUMENTS` may include:
- A path (e.g., `~/.claude/skills/`, `skills/python-conventions/`)
- `--preset strict` or `--preset security` (default: recommended)
- `--red-team` (adversarial testing for preventive skills in Layer 3)
- Natural language like "evaluate my setup", "is my python skill any good?"

If no path is given and the user didn't answer Step 0 (e.g., they passed arguments directly), default to scanning skills in the current directory with terminal output, Layers 1+2 only.

## Step 1: Run Layer 1 (Static Analysis)

*Skip this step if the user chose "Layer 3 only".*

Find the evaluator project directory:

```bash
PROJECT_DIR="$(find . -path '*/evaluate-setup/src/the_evaluator/cli.py' -not -path '*/.git/*' 2>/dev/null | head -1 | sed 's|/src/the_evaluator/cli.py||')"
```

If that returns empty, fall back to `scripts/evaluate-setup`.

Run the analysis:

```bash
uv run --project "$PROJECT_DIR" evaluate-setup scan <PATH> [--preset <PRESET>]
```

Read the JSON output. This gives you per-skill diagnostics with rule IDs, severities, and token counts.

Layer 1 checks include: frontmatter validation, trigger quality, token budget, broken file references, TF-IDF cosine similarity for near-duplicate detection (threshold 0.85), prompt injection patterns, and credential access references.

## Step 2: Read Actual Files (Layer 2 Preparation)

*Skip this step if the user chose "Layer 3 only".*

Read the actual content of:
1. Every skill file (SKILL.md) in the scan path
2. Every command file (command.md) found nearby
3. The user's CLAUDE.md files (project and user level)

You need the actual content — not just the Layer 1 JSON — to evaluate quality, redundancy, and content.

## Step 3: Evaluate Each Skill (Layer 2)

*Skip this step if the user chose "Layer 3 only".*

For each skill, produce a **structured rubric score** on 5 dimensions:

### Rubric Dimensions

**Specificity (weight 0.25)**
- 1: Entirely vague platitudes, no actionable instructions
- 2: Mostly generic advice with one or two specific rules
- 3: Mix of specific and generic; some rules change Claude's behavior
- 4: Mostly specific, actionable instructions with concrete patterns
- 5: Every instruction is specific, actionable, includes concrete patterns or examples

**Redundancy (weight 0.25)**
- 1: Every instruction duplicates Claude's default behavior
- 2: 75%+ is default behavior, very little unique value
- 3: Some unique value, but 50%+ is default behavior
- 4: Mostly unique, with minor overlap with Claude's defaults
- 5: Entirely unique — teaches Claude something it genuinely doesn't know

Things Claude already does by default (always redundant):
- "Write clean, readable code"
- "Be helpful and thorough"
- "Handle errors properly" (too vague to add value)
- "Follow best practices"
- "Use proper formatting"
- "Think step by step"
- "Consider edge cases"

A skill is NOT redundant if it provides specific, actionable rules. "Always use `raise from` for exception chaining in Python" is specific enough to change behavior.

**Also check for overlap with Claude's built-in behavior.** Claude already does many things by default (plan mode, code review, commit messages, code explanation). A skill that just wraps a Claude default without adding specific rules or constraints is redundant. Ask: "if I deleted this skill, would Claude behave differently?" If not → redundant.

**Trigger quality (weight 0.20)**
- 1: No description, or description triggers on everything
- 2: Description exists but is too broad or too narrow
- 3: Description is reasonable but could be more precise
- 4: Good description that targets the right tasks most of the time
- 5: Description precisely targets the right tasks; starts with "Use when"; doesn't overlap with other skills

**Token efficiency (weight 0.15)**
- 1: >3,000 tokens with low value density
- 2: 2,000-3,000 tokens, or under 1,500 with very low value
- 3: Under 1,500 tokens, some padding that could be trimmed
- 4: Well-sized, minor optimization possible
- 5: Every token earns its place; high value-to-token ratio

**Content quality (weight 0.15)**
- 1: No structure, no examples, broken references
- 2: Minimal structure, vague instructions
- 3: Decent structure, some examples, no broken references
- 4: Well-organized with examples and clear sections
- 5: Well-organized, includes examples, references valid files, covers edge cases

### Scoring

- Score each dimension 1-5
- Include a **one-sentence justification** for each score citing specific evidence
- Calculate overall: `round(specificity*0.25 + redundancy*0.25 + trigger*0.20 + efficiency*0.15 + quality*0.15)`
- Assign verdict: **KEEP** (4-5 stars), **REVIEW** (3 stars), **REMOVE** (1-2 stars)

### Per-Skill Output Format

```
### skill-name                               ★★★★    KEEP
  Tokens: 663

  Rubric:
    Specificity:      5/5  Concrete rules: raise from, exception hierarchies
    Redundancy:       4/5  One rule overlaps Claude's default
    Trigger quality:  5/5  Targets Python error handling precisely
    Token efficiency: 5/5  663 tokens, high value density
    Content quality:  4/5  Well-structured but could add examples

  + What's good (bullet points)
  ! What could improve (bullet points)
  x What's broken (from Layer 1 diagnostics)
```

## Step 3b: Evaluate CLAUDE.md (if --claude-md or --all)

Score CLAUDE.md on 5 dimensions:

| Dimension | Weight | What to check |
|---|---|---|
| **Conciseness** | 0.25 | Under ~300 lines? Can each line pass "would removing this cause mistakes?" |
| **Signal-to-noise** | 0.25 | Only contains things Claude can't figure out from code? No generic advice? |
| **Skill separation** | 0.20 | Domain-specific rules are in skills (on-demand), not CLAUDE.md (every session)? |
| **Structure** | 0.15 | Clear sections? Critical rules marked? Scannable? |
| **Conflict-free** | 0.15 | No contradictions with any skill? |

## Step 3c: Evaluate Commands (if --commands or --all)

Score each command on 7 dimensions:

| Dimension | Weight | What to check |
|---|---|---|
| **Description quality** | 0.20 | Clear, concise description for the UI menu? |
| **Instruction clarity** | 0.20 | Claude knows exactly what to do, in what order? |
| **Script integrity** | 0.15 | Referenced scripts exist? Discovery pattern works? |
| **Scope appropriateness** | 0.10 | Should this be a command (user-triggered) or a skill (auto-triggered)? |
| **Token efficiency** | 0.10 | Concise or bloated? |
| **Redundancy with defaults** | 0.15 | Does Claude already do this without the command? Claude has built-in plan mode, generates commit messages, explains code, and reviews code by default. A command is only justified if it adds specific rules, constraints, or structure that Claude wouldn't follow unprompted. Ask: "if I deleted this command, could I get the same result by just asking Claude?" If yes → redundant. |
| **Robustness** | 0.10 | Does the command handle edge cases? Does it hardcode assumptions (specific tools, languages, thresholds) that should be detected from the project? Does it depend on skills loading reliably? Does it gracefully handle missing dependencies? |

## Step 3d: Evaluate Hooks (if --hooks or --all)

For each hook, check:
- Does the hook have a clear purpose?
- Does the referenced script/command exist?
- Are there dangerous patterns (rm -rf, force push)?
- Is this the right mechanism? (hooks are deterministic — 100% execution. If the behavior is advisory, it should be in CLAUDE.md or a skill instead.)

## Step 4: Cross-Type Optimization (the full picture)

*Skip this step if the user chose "Layer 3 only".*

This is where you look at the **whole setup** and suggest transformations between types. Only suggest transformations when you genuinely believe they would improve the setup — don't suggest changes for the sake of it.

### Transformation types to consider:

**Skill → Hook** — If a skill contains rules that MUST happen every time without exception (e.g., "always run linting after editing"), that's a hook, not a skill. Skills are advisory (~80% adherence). Hooks are deterministic (100%). Ask: "If Claude ignores this instruction, would something break?" If yes → hook.

**Skill → Command** — If a skill describes a specific workflow the user triggers explicitly (e.g., "audit my code", "generate a migration", "deploy to staging"), it should be a command. Skills are for passive behavior ("whenever you write Python, do X"). Commands are for active actions the user invokes with `/command-name`.

**Command → Skill** — If a command describes general behavior that should always be active (e.g., a `/python-style` command that the user runs every time), it should be a skill that auto-triggers.

**Skill content → CLAUDE.md** — If a skill contains rules that apply to EVERY conversation regardless of task (e.g., "always use uv for Python", "never commit .env files"), those belong in CLAUDE.md. Skills load on-demand; CLAUDE.md loads every session. Universal rules should be in CLAUDE.md.

**CLAUDE.md content → Skill** — The reverse. If CLAUDE.md contains domain-specific rules that only matter sometimes (e.g., "when writing data pipelines, use this stage structure"), those waste context in every session. Move them to a skill that loads only when relevant.

**CLAUDE.md content → Hook** — If CLAUDE.md says "always run tests before committing" but Claude sometimes forgets — make it a hook. The hook guarantees it happens.

### Setup-wide checks:

- **Merge candidates**: Skills covering related topics that would be stronger combined
- **Overlapping triggers**: Skills whose descriptions might cause multiple to load unnecessarily
- **Coverage gaps**: Obvious missing areas based on what's present
- **Total context budget**: Sum all skills + CLAUDE.md + commands tokens, warn if >20% of context window
- **Redundancy across types**: Same instruction appearing in CLAUDE.md AND a skill (double token cost)
- **Conflicts across types**: CLAUDE.md says one thing, a skill says the opposite

### Example transformation suggestions:

```
## Cross-Type Optimization

  ⟳ Skill → Hook: security-check says "always run pre-commit before pushing" —
    this should be a hook to guarantee it runs every time, not a skill that
    Claude might skip.

  ⟳ Skill → Command: brainstorming says "you MUST use this before any creative work" —
    the hard gate makes it behave like a command. Consider making it a /brainstorm
    command instead.

  ⟳ CLAUDE.md → Skill: The "Testing" section in CLAUDE.md (lines 45-60) contains
    pytest-specific rules that only matter when writing tests. Move to a
    testing-conventions skill that loads on demand.

  ✓ No conflicts detected between CLAUDE.md and skills.
  ✓ No redundant content detected across types.
```

## Step 5: Produce the Report

*Skip this step if the user chose "Layer 3 only".*

### Step 5a: Full Review

If the user chose **terminal output**, print the full review directly. If they chose **file output**, write it to the chosen filename and tell the user where to find it.

Full review format:

```
## How This Evaluation Works

This report was generated by the evaluate-setup tool. Here's what each layer did:

**Layer 1 (Static Analysis)** — A Python script automatically scanned every
skill, command, and CLAUDE.md file. It checked: does each SKILL.md have valid
frontmatter? Does the description start with "Use when"? Is the skill under
1,500 tokens? Do referenced files exist? Are any two skills near-duplicates
(using TF-IDF text similarity)? Are there prompt injection patterns or
hardcoded credentials? This layer catches mechanical issues — broken files,
missing fields, structural problems.

**Layer 2 (Rubric Scoring)** — Claude read every file and scored it on a
weighted rubric. For skills: Specificity (are instructions actionable?),
Redundancy (does Claude already do this by default?), Trigger Quality (will it
activate at the right time?), Token Efficiency (value per token), and Content
Quality (structure, examples, references). For commands: 7 dimensions including
whether Claude already does this without the command. For CLAUDE.md: conciseness,
signal-to-noise, and whether domain rules belong in skills instead. Then Claude
looked across all items for conflicts, overlaps, and type mismatches (e.g., a
skill that should be a hook).

[If Layer 3 ran:]
**Layer 3 (A/B Testing)** — This layer answers the question: "does this skill
actually change Claude's behavior, or does Claude already do the same thing
without it?" For selected skills, Gemini generated 4 test tasks (1 knowledge
question + 3 tasks on your actual repositories). Claude ran each task twice:
once with the skill loaded, once without. Gemini then judged the pair with a
**redundancy-first** approach: the primary question (~70%) is "did one response
apply specific conventions from the skill that the other missed?" — not just
"which response is better." If both responses follow the same conventions
equally well, that means Claude already knows the content and the skill is
redundant — the verdict is TIE regardless of minor quality differences. Quality
is only a tiebreaker (~30%) when the redundancy check is inconclusive. Each
task gets 3 blind votes (the judge doesn't know which response had the skill),
majority wins. If both responses were equally vague or unhelpful, the test is
marked inconclusive rather than forcing a verdict. Subagents have READ-ONLY
access to your repositories — they can read and search code but never modify
files, commit, or push.

---

## Static Analysis (Layer 1)
  Preset: <preset> | <N> skills, <M> commands, <K> other items
  <tokens> tokens total (<pct>% of context budget)
  <errors> errors | <warnings> warnings | <info> info
  <fixable> auto-fixable issues found

## Per-Item Review (Layer 2)

### Skills
  [Per-skill rubric output, one per skill]

### CLAUDE.md (if evaluated)
  [CLAUDE.md rubric output]

### Commands (if evaluated)
  [Per-command rubric output]

### Hooks (if evaluated)
  [Per-hook review]

## Cross-Type Optimization
  [Transformation suggestions — only when genuinely beneficial]

## Setup-Wide Recommendations
  [Merge candidates, overlapping triggers, coverage gaps, context budget]
```

### Step 5b: Terminal Summary (ALWAYS printed, regardless of output format)

This is the last thing the user sees. Keep it short — 10-15 lines max. It tells the user the bottom line.

```
## Evaluation Summary

<Overall verdict — one sentence. E.g., "Your setup is solid" or "Found 2 issues that need attention.">
Reviewed <N> skills, <M> commands, CLAUDE.md. Total: <tokens> tokens (<pct>%).

Suggestions (say "do 1", "do 2", "skip 3" to act on them):
  1. <one-line suggestion>
  2. <one-line suggestion>
  3. <one-line suggestion>

Full review: <"printed above" or "saved to <filename>">
```

**Numbering rules:**
- Every suggestion gets a number, starting from 1
- Each number is one actionable item Claude can execute if the user says "do N"
- Keep each suggestion to one line — the full explanation is in the detailed review
- If the setup is healthy, it's fine to have just 1-2 suggestions or even zero. Don't pad.

**Key principle:** If nothing significant needs to change, say "your setup is solid" and list only the minor items. Don't pad the summary with nice-to-have suggestions. The user should be able to read the summary in 10 seconds and know: do I need to act or not?

## Step 6: Deep Evaluation (Layer 3)

*Run this step if the user chose "All" or "Layer 3 only" for layers.*

### 6.1: Check prerequisites

**Check `GOOGLE_API_KEY`:**
```bash
grep -q "GOOGLE_API_KEY" .env 2>/dev/null && echo "found" || echo "missing"
```

If missing, tell the user:
```
Layer 3 requires a Google API key for Gemini (task generation + judging).
Claude runs the tasks itself — no Anthropic API key needed.

Create a .env file in your project root with:

  GOOGLE_API_KEY=your-key-here
  GEMINI_MODEL=gemini-2.0-flash  # optional, this is the default

Make sure .env is in your .gitignore.
```
Stop here if the key is missing.

### 6.2: Discover available repositories

Scan for repositories the user has cloned:
```bash
for dir in repositories/*/; do
  if [ -d "$dir/.git" ]; then
    name=$(basename "$dir")
    # Read first line of README for description
    desc=$(head -5 "$dir/README.md" 2>/dev/null | grep -v '^#' | grep -v '^$' | head -1)
    echo "$name|$dir|$desc"
  fi
done
```

Write the repo info to a JSON file for the task generator:
```json
[
  {"name": "repo-name", "path": "repositories/repo-name", "description": "brief description from README"}
]
```
Save to `.tmp/deep-eval/repos.json`.

If no repositories are found, Layer 3 falls back to knowledge-only tasks (task 1 only, no repo-based tasks 2-4). Warn the user: "No repositories found in repositories/ — Layer 3 will only run knowledge tests, not repo-based A/B tests."

### 6.3: Screen skills for testability

Before asking the user to select skills, run the screening step to let Gemini decide which skills can actually be A/B tested:

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval screen-skills skills/
```

This outputs JSON with `testable` and `not_testable` lists, each with reasons. **Save the screening output to `.tmp/deep-eval/skill-screening.json`** so the user can inspect why each skill was or wasn't considered testable.

Use this to inform the skill selection — show the user which skills Gemini flagged as not testable and why (e.g., "requires MCP connection", "orchestrates tools rather than teaching patterns").

### 6.4: Confirm skill selection

If the user already selected skills in Step 0 (round 2), cross-reference with the screening results. If any of their selections were flagged as not testable, warn them:

```
Gemini flagged these skills as poor A/B candidates:
  - brainstorming: "Multi-step interactive workflow with user approval gates"
  - verification-loop: "Orchestrates tools (mypy, ruff, pytest) rather than teaching patterns"

Proceed anyway, or remove them?
```

If the user hasn't selected skills yet, present the selection using screening results to pre-check/uncheck.

Show estimated cost: ~13 Gemini API calls per skill (4 tasks × 3 judge votes + 1 task generation). Confirm before proceeding.

### 6.5: Run A/B tests

**Create temp directory:**
```bash
uv run .ai-workspace/scripts/mktmpdir.py deep-eval 2>/dev/null || mkdir -p .tmp/deep-eval
```

**For each selected skill:**

**a. Generate 4 tasks** using Gemini:
```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval generate-tasks <SKILL_DIR> [--red-team] --repos-file .tmp/deep-eval/repos.json
```
This outputs JSON with 4 tasks:
- Task 1: Knowledge test (no repo)
- Tasks 2-4: Repo-based tasks (code review, code writing, debugging — on the user's actual repositories)

**Save the task definitions to `.tmp/deep-eval/<skill>_tasks.json`** so the user can inspect exactly what tasks were used for A/B testing.

**b. Spawn ALL 8 subagents in parallel** (4 with-skill + 4 without-skill) in a single message with multiple Agent tool calls. This is the key speed optimization — don't run tasks sequentially.

For each task, spawn 2 subagents:

**With-skill agent prompt:**
```
You have the following skill loaded:

<skill>
[full SKILL.md content]
</skill>

YOUR TASK: [task description from Gemini]

IMPORTANT RULES:
- You have READ-ONLY access to the codebase. You may use Read, Bash(grep/find/cat), and other read tools.
- Do NOT use Edit, Write, or any tool that modifies files. Do NOT run git commit, git push, or any destructive command.
- Respond with your analysis, review, or code directly in your response text.
- Be specific and reference actual files, line numbers, and code patterns you find.
- Keep your response under 800 words.
[If task has a repo]: Work in the repository at: [repo path]
```

**Without-skill agent prompt:**
```
YOUR TASK: [same task description]

IMPORTANT RULES:
- You have READ-ONLY access to the codebase. You may use Read, Bash(grep/find/cat), and other read tools.
- Do NOT use Edit, Write, or any tool that modifies files. Do NOT run git commit, git push, or any destructive command.
- Respond with your analysis, review, or code directly in your response text.
- Be specific and reference actual files, line numbers, and code patterns you find.
- Keep your response under 800 words.
[If task has a repo]: Work in the repository at: [repo path]
```

After all 8 subagents complete, save each response to temp files:
- `.tmp/deep-eval/<skill>_task<N>_with.txt`
- `.tmp/deep-eval/<skill>_task<N>_without.txt`

**CRITICAL: Save the COMPLETE agent response text using the Write tool. Do NOT summarize, abbreviate, or paraphrase — the judge must see exactly what the agent produced, word for word. If an agent response is very long, save it in full anyway. The judge script truncates to 3000 chars internally, so you don't need to worry about length — but the full text must be on disk for reproducibility.**

**c. Judge all 4 pairs.** For each task, run the judge with the skill file for context-aware judging:
```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval judge \
  "<TASK_DESCRIPTION>" \
  .tmp/deep-eval/<skill>_task<N>_with.txt \
  .tmp/deep-eval/<skill>_task<N>_without.txt \
  [--red-team] \
  --skill-file <SKILL_DIR>/SKILL.md
```

**d. Verify no changes were made** to any repo.

Before running any subagents (at the start of step 6.4), record each repo's current state:
```bash
for dir in repositories/*/; do
  if [ -d "$dir/.git" ]; then
    name=$(basename "$dir")
    git -C "$dir" status --porcelain 2>/dev/null | wc -l > .tmp/deep-eval/repo_snapshot_${name}.txt
  fi
done
```

After all subagents complete, compare with the snapshot:
```bash
for dir in repositories/*/; do
  if [ -d "$dir/.git" ]; then
    name=$(basename "$dir")
    before=$(cat .tmp/deep-eval/repo_snapshot_${name}.txt 2>/dev/null || echo "0")
    after=$(git -C "$dir" status --porcelain 2>/dev/null | wc -l)
    if [ "$after" -gt "$before" ]; then
      echo "WARNING: $dir has new changes that weren't there before testing"
    fi
  fi
done
```

**NEVER run `git checkout .`, `git stash`, `git restore`, or any command that modifies repository state.** The user may have uncommitted work in these repos. If new changes are detected, only WARN — let the user decide what to do.

### 6.6: Aggregate results

For each skill, across all 4 tasks:
- Count wins (with_skill), losses (without_skill), ties, and **inconclusive** results
- If 2+ tasks are inconclusive, the skill verdict is **INCONCLUSIVE** — the test didn't work, not that the skill is bad. Report this clearly: "A/B test was inconclusive — responses didn't produce measurable differences. This doesn't mean the skill is useless, just that it couldn't be tested this way."
- Standard mode verdict (if enough conclusive results): **KEEP** (wins > losses and wins > ties), **HURTS** (losses > wins), **NO IMPACT** (otherwise)
- Red-team mode verdict: **STRONG** (score ≥ 0.80), **WEAK** (score ≥ 0.50), **FRAGILE** (score < 0.50)

### 6.7: Save the detailed Layer 3 log

Write to `evaluate-setup-deep-log.md` (if that file exists, append a number: `evaluate-setup-deep-log-2.md`, etc.). This log is always saved to a file, never printed to terminal — it's too long.

```markdown
# Layer 3 Deep Evaluation Log

**Date:** [today]
**Skills tested:** [list]
**Repositories used:** [list]
**Mode:** standard / red-team

## How This Evaluation Works

For each skill below, we ran 4 tasks: 1 knowledge question (can Claude recall
the skill's rules?) and 3 tasks on your actual repositories (does the skill
change how Claude reviews, writes, or debugs real code?).

Each task was run twice — once with the skill loaded, once without. The
responses were sent to Gemini as a blind judge (it doesn't know which is which).
Gemini voted 3 times per task; majority wins. If both responses were equally
unhelpful or off-topic, the judge marked the test as inconclusive instead of
picking a winner.

No files were modified during testing — all repository access was read-only.

## Skill Screening Results

Gemini evaluated each skill for A/B testability before testing began.
Full screening output: `.tmp/deep-eval/skill-screening.json`

**Testable:**
- [skill-name] — "[reason from screening]"
- ...

**Not testable:**
- [skill-name] — "[reason from screening]"
- ...

---

## skill-name                                    KEEP

> Task definitions: `.tmp/deep-eval/<skill>_tasks.json`

### Task 1 (knowledge): [task description]

**Response WITH skill:**
> [full response text]

**Response WITHOUT skill:**
> [full response text]

**Gemini Judgment:**
- Vote 1: with_skill (good test, unique) — "[reasoning excerpt]"
- Vote 2: with_skill (good test, unique) — "[reasoning excerpt]"
- Vote 3: tie (good test, redundant) — "[reasoning excerpt]"
- **Verdict: with_skill (HIGH confidence) | Redundancy: unique**

---

### Task 2 (review on repo-name): [task description]

**Response WITH skill:**
> [full response text]

**Response WITHOUT skill:**
> [full response text]

**Gemini Judgment:**
- Vote 1: with_skill (good test) — "[reasoning]"
- Vote 2: without_skill (good test) — "[reasoning]"
- Vote 3: with_skill (good test) — "[reasoning]"
- **Verdict: with_skill (LOW confidence)**

---

### Task 3 (write on repo-name): [task description]

**Response WITH skill:**
> [full response text]

**Response WITHOUT skill:**
> [full response text]

**Gemini Judgment:**
- Vote 1: inconclusive (poor test — "both responses asked for clarification instead of answering") — "[reasoning]"
- Vote 2: inconclusive (poor test — "neither response addressed the task") — "[reasoning]"
- Vote 3: tie (poor test) — "[reasoning]"
- **Verdict: INCONCLUSIVE (test quality: poor)**

---

### Task 4 (debug on repo-name): [task description]
...

---

### Skill Verdict: KEEP (3 wins, 0 losses, 1 tie) | Redundancy: unique
```

Tell the user: "Layer 3 detailed log saved to `<filename>`."

### 6.8: Add Layer 3 summary to the main report

If L1+L2 also ran, add a short block after each tested skill's L2 rubric:

```
Layer 3 (A/B): KEEP — 3 wins, 0 losses, 1 tie (HIGH confidence)
  Redundancy signal: unique — skill taught conventions Claude didn't know
  See evaluate-setup-deep-log.md for full details.
```

When the redundancy signal is "redundant" across most tasks, include that in the verdict explanation:
```
Layer 3 (A/B): NO IMPACT — 1 win, 1 loss, 2 ties (LOW confidence)
  Redundancy signal: redundant — both agents applied the same conventions,
  meaning Claude already knows this content without the skill
  See evaluate-setup-deep-log.md for full details.
```

If Layer 3 was NOT selected but some skills scored 2 stars or below in L2:
- Suggest: "N skills scored poorly. Consider running Layer 3 to verify with A/B testing. Requires GOOGLE_API_KEY in your .env."
