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
  - <skill-name>: "<Gemini's reason>"
  - <skill-name>: "<Gemini's reason>"

Proceed anyway, or remove them?
```

If the user hasn't selected skills yet, present the selection using screening results to pre-check/uncheck. Always use Gemini's actual screening output — never hardcode which skills are good or poor candidates.

Confirm before proceeding.

### 6.5: Run A/B tests (3-condition design)

**Create temp directory:**
```bash
uv run .ai-workspace/scripts/mktmpdir.py deep-eval 2>/dev/null || mkdir -p .tmp/deep-eval
```

**Before starting, read ALL skill files** so you can build the "all-except" prompt for each tested skill. For each skill in the `skills/` directory, read its SKILL.md content and store it.

**For each selected skill:**

The engine auto-detects whether each skill is preventive (contains "never", "do not", "must not" patterns). Preventive skills use red-team mode (adversarial tasks testing whether the skill prevents bad behavior). Standard skills use A/B mode (tasks testing whether the skill improves output quality). No user flag needed.

**a. Generate 4 tasks** using Gemini:
```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval generate-tasks <SKILL_DIR> --repos-file .tmp/deep-eval/repos.json
```
This outputs JSON with 4 tasks:
- Task 1: Knowledge test (no repo)
- Tasks 2-4: Repo-based tasks (code review, code writing, debugging — on the user's actual repositories)

**Save the task definitions to `.tmp/deep-eval/<skill>_tasks.json`**.

**b. Spawn ALL 12 subagents in parallel** (4 tasks × 3 conditions) in a single message with multiple Agent tool calls. For each task, spawn 3 subagents:

**Agent A (bare) — no skills loaded:**
```
YOUR TASK: [task description from Gemini]

IMPORTANT RULES:
- You have READ-ONLY access to the codebase. You may use Read, Bash(grep/find/cat), and other read tools.
- Do NOT use Edit, Write, or any tool that modifies files. Do NOT run git commit, git push, or any destructive command.
- Do NOT read any files under the skills/ directory.
- Respond with your analysis, review, or code directly in your response text.
- Be specific and reference actual files, line numbers, and code patterns you find.
- Keep your response under 800 words.
[If task has a repo]: Work in the repository at: [repo path]
```

**Agent B (all-except) — all skills EXCEPT the tested one loaded:**
```
You have the following skills loaded:

<skills>
[concatenated SKILL.md content of ALL skills EXCEPT the one being tested]
</skills>

YOUR TASK: [task description from Gemini]

IMPORTANT RULES:
- You have READ-ONLY access to the codebase. You may use Read, Bash(grep/find/cat), and other read tools.
- Do NOT use Edit, Write, or any tool that modifies files. Do NOT run git commit, git push, or any destructive command.
- Do NOT read any files under the skills/ directory.
- Respond with your analysis, review, or code directly in your response text.
- Be specific and reference actual files, line numbers, and code patterns you find.
- Keep your response under 800 words.
[If task has a repo]: Work in the repository at: [repo path]
```

**Agent C (with-skill) — the tested skill loaded:**
```
You have the following skill loaded:

<skill>
[full SKILL.md content of the tested skill]
</skill>

YOUR TASK: [task description from Gemini]

IMPORTANT RULES:
- You have READ-ONLY access to the codebase. You may use Read, Bash(grep/find/cat), and other read tools.
- Do NOT use Edit, Write, or any tool that modifies files. Do NOT run git commit, git push, or any destructive command.
- Do NOT read any files under the skills/ directory.
- Respond with your analysis, review, or code directly in your response text.
- Be specific and reference actual files, line numbers, and code patterns you find.
- Keep your response under 800 words.
[If task has a repo]: Work in the repository at: [repo path]
```

After all 12 subagents complete, save each response to temp files:
- `.tmp/deep-eval/<skill>_task<N>_bare.txt` (Agent A)
- `.tmp/deep-eval/<skill>_task<N>_allexcept.txt` (Agent B)
- `.tmp/deep-eval/<skill>_task<N>_withskill.txt` (Agent C)

**CRITICAL: Save the COMPLETE agent response text using the Write tool. Do NOT summarize, abbreviate, or paraphrase — the judge must see exactly what the agent produced, word for word.**

**c. Judge 2 pairwise comparisons per task.** For each task, run 2 judge calls:

**Judgment 1 — Absolute value (A vs C):** Does the skill teach Claude something it doesn't already know?
```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval judge \
  "<TASK_DESCRIPTION>" \
  .tmp/deep-eval/<skill>_task<N>_withskill.txt \
  .tmp/deep-eval/<skill>_task<N>_bare.txt \
  \
  --skill-file <SKILL_DIR>/SKILL.md \
  --comparison-type absolute
```

**Judgment 2 — Marginal value (B vs C):** Does the skill add value beyond what OTHER skills already provide?
```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval judge \
  "<TASK_DESCRIPTION>" \
  .tmp/deep-eval/<skill>_task<N>_withskill.txt \
  .tmp/deep-eval/<skill>_task<N>_allexcept.txt \
  \
  --skill-file <SKILL_DIR>/SKILL.md \
  --comparison-type marginal
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

For each skill, aggregate TWO separate verdict tracks across all 4 tasks:

**Absolute value** (bare vs with-skill): Does the skill teach Claude something it doesn't already know?
- Count wins, losses, ties, inconclusive from Judgment 1 results

**Marginal value** (all-except vs with-skill): Does the skill add value beyond what OTHER skills provide?
- Count wins, losses, ties, inconclusive from Judgment 2 results

**The marginal value is the primary verdict** — it determines if the skill earns its place in the full setup.

Per-track verdicts:
- If 2+ tasks are inconclusive → **INCONCLUSIVE**
- **KEEP** (wins > losses and wins > ties), **HURTS** (losses > wins), **NO IMPACT** (otherwise)
- Red-team mode verdict: **STRONG** (score ≥ 0.80), **WEAK** (score ≥ 0.50), **FRAGILE** (score < 0.50)

### 6.7: Save the detailed Layer 3 log

Write to `evaluate-setup-deep-log.md` (if that file exists, append a number: `evaluate-setup-deep-log-2.md`, etc.). This log is always saved to a file, never printed to terminal — it's too long.

```markdown
# Layer 3 Deep Evaluation Log

**Date:** [today]
**Skills tested:** [list]
**Repositories used:** [list]
**Mode:** [standard or red-team — auto-detected per skill]

## How This Evaluation Works

For each skill below, we ran 4 tasks: 1 knowledge question + 3 tasks on
your actual repositories. Each task was run THREE times:
- **Agent A (bare):** Claude with no skills loaded
- **Agent B (all-except):** Claude with all skills EXCEPT the tested one
- **Agent C (with-skill):** Claude with the tested skill loaded

Two pairwise judgments per task:
- **Absolute (A vs C):** Does the skill teach Claude something it doesn't know?
- **Marginal (B vs C):** Does the skill add value beyond what OTHER skills provide?

Gemini judges each pair with 3 blind votes (majority wins). The marginal
verdict is what determines if the skill earns its place in the full setup.

No files were modified during testing — all repository access was read-only.

---

## skill-name                                    KEEP

> Task definitions: `.tmp/deep-eval/<skill>_tasks.json`

### Task 1 (knowledge): [task description]

**Response A (bare):** [summary]
**Response B (all-except):** [summary]
**Response C (with-skill):** [summary]

**Absolute (A vs C):** with_skill (HIGH) — unique
**Marginal (B vs C):** with_skill (LOW) — unique

---

### Task 2 (review on repo-name): [task description]

**Response A (bare):** [summary]
**Response B (all-except):** [summary]
**Response C (with-skill):** [summary]

**Absolute (A vs C):** with_skill (HIGH) — unique
**Marginal (B vs C):** with_skill (HIGH) — unique

---

[Tasks 3-4 follow same format]

---

### Skill Verdict
  Absolute:  KEEP (3 wins, 0 losses, 1 tie) — skill teaches Claude new things
  Marginal:  KEEP (2 wins, 0 losses, 2 ties) — skill adds value beyond other skills
  Final:     KEEP (marginal is the primary verdict)
```

Tell the user: "Layer 3 detailed log saved to `<filename>`."

### 6.8: Add Layer 3 results to the main report's Redundancy dimension

Layer 3 results go in **Dimension 3: Redundancy** of the main report. For each tested skill, add:

```
### Layer 3 A/B Results: skill-name

| Task | Absolute (bare vs skill) | Marginal (all-except vs skill) |
|---|---|---|
| Task 1 (knowledge) | with_skill (HIGH) | tie (LOW) |
| Task 2 (review) | with_skill (HIGH) | with_skill (HIGH) |
| Task 3 (write) | with_skill (LOW) | with_skill (LOW) |
| Task 4 (debug) | tie (LOW) | tie (LOW) |
| **Verdict** | **KEEP (2W/0L/2T)** | **KEEP (2W/0L/2T)** |

Absolute: skill teaches Claude things it doesn't already know
Marginal: skill adds value beyond what other skills provide
```

When the marginal verdict is different from absolute, highlight it:
```
Layer 3 (A/B): NO IMPACT — 1 win, 1 loss, 2 ties (LOW confidence)
  Redundancy signal: redundant — both agents applied the same conventions,
  meaning Claude already knows this content without the skill
  See evaluate-setup-deep-log.md for full details.
```

If Layer 3 was NOT selected but some skills scored 2 stars or below in L2:
- Suggest: "N skills scored poorly. Consider running Layer 3 to verify with A/B testing. Requires GOOGLE_API_KEY in your .env."
