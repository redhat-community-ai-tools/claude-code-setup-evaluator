# How Evaluate-Skill Works

This document explains what happens when you run `/evaluate-skill` — the deep evaluation of a single skill.

---

## What it does vs /evaluate-setup

`/evaluate-setup` checks your **entire setup** shallowly — all skills, commands, CLAUDE.md, hooks, agents. Two layers.

`/evaluate-skill` checks **one skill** deeply — three layers, including an empirical A/B test that proves whether the skill actually changes Claude's behavior.

---

## Step 1: Pick a skill

If you type `/evaluate-skill python-conventions`, it uses that skill directly.

If you just type `/evaluate-skill` with no argument, Claude lists all skills in the workspace with their token counts and asks you to pick one:

```
Available skills:

  1. accessibility          (1,485 tokens)
  2. article-writing        (610 tokens)
  3. data-pipeline-patterns (663 tokens)
  ...

Type a skill name or number:
```

You pick exactly one skill per run.

---

## Step 2: Ask one question

Claude asks: **"Terminal or file?"**

If you choose file, the report is saved to `evaluation-results/evaluate-skill-<skill-name>-YYYY-MM-DD-HHMM.md`.

---

## Step 3: Layer 1 — the Python tool runs

Claude runs one command:

```bash
uv run --project "$PROJECT_DIR" evaluate-setup scan <SKILL_PATH>
```

This is the same static analysis engine used by `/evaluate-setup`. It runs 9 skill rules on the selected skill:

| Rule | What it checks |
|------|---------------|
| SKILL.md exists | The skill directory contains a SKILL.md file |
| Description required | Description field exists and is not empty |
| Description quality | Third-person POV, includes use-case context, length between 20 and 1,024 characters |
| Frontmatter valid | YAML frontmatter parses correctly, name matches directory |
| Token budget | SKILL.md is under the token limit and under 500 lines |
| Broken references | All file links and references point to files that exist |
| Duplicate detection | No other skill is >85% similar (TF-IDF cosine similarity) |
| No prompt injection | No patterns that could hijack Claude's behavior |
| No credential access | No references to ~/.ssh, ~/.aws, $API_KEY, sudo, chmod 777 |

Output is JSON with diagnostics — what passed, what failed, and why.

---

## Step 4: Layer 2 — Claude scores the skill

Claude reads the actual files:

**The target skill:**
1. The SKILL.md file
2. All files in the skill's `skills/` subdirectory (reference files that load on demand)
3. The skill's `guidelines.md` (if it exists) — behavioral rules, hard limits

**For context (not scored — just used for comparison):**
4. All OTHER skill SKILL.md files in the workspace
5. CLAUDE.md
6. Hooks in `.claude/settings.json`

### Individual rubric (5 dimensions)

Claude scores the skill on 5 weighted dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Specificity | 0.25 | Are instructions concrete and actionable? |
| Redundancy | 0.25 | Does this teach Claude something it doesn't already know? |
| Trigger quality | 0.20 | Will the description activate at the right time? |
| Token efficiency | 0.15 | Is the size justified by the value? |
| Content quality | 0.15 | Structure, examples, error handling? |

Each dimension gets a 1-5 score with a one-sentence justification. Weighted average → star rating → verdict: **KEEP** (4-5 stars), **REVIEW** (3 stars), **REMOVE** (1-2 stars).

### Contextual analysis (5 checks)

Claude also evaluates the skill in context of the whole setup:

| Check | What it answers |
|-------|----------------|
| Overlap with other skills | Does another skill cover the same domain? |
| Conflict with CLAUDE.md | Does the skill contradict CLAUDE.md? |
| Conflict with other skills | Does the skill's advice conflict with another skill? |
| Type appropriateness | Should this be a skill, a command, or a hook? |
| Structure optimization | Should a large SKILL.md be split into thin entry + reference files? |

---

## Step 5: Layer 3 — A/B testing

This is what makes `/evaluate-skill` different from `/evaluate-setup`. It empirically tests whether the skill changes Claude's behavior.

### 5.1: Check prerequisites

Layer 3 uses Gemini for task generation and judging. Claude checks for `GOOGLE_API_KEY` in a `.env` file. If missing, it tells you how to set it up and stops.

### 5.2: Screen for testability

Not every skill can be A/B tested. Claude runs:

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval screen-skills <SKILL_PATH>
```

Gemini reads the skill and decides: can this be meaningfully tested in a single response? Skills that require MCP connections, define multi-step interactive workflows, or orchestrate external tools are flagged as not testable.

If the skill is flagged as not testable, Layer 3 is skipped — the Layer 1 + Layer 2 results are still valid.

### 5.3: Generate tasks

Gemini generates 3 tasks using your actual repositories:

1. **Review** — ask Claude to review specific code in a real repo
2. **Write** — ask Claude to write code or plan an implementation in a real repo
3. **Debug** — present a plausible bug scenario in a real repo

Tasks create situations where the skill's rules would naturally apply. They don't ask the agent to explain or recite the skill — that would just test reading comprehension. The engine also auto-detects whether the skill is preventive (contains "never", "do not" patterns) and switches to adversarial red-team tasks if so.

### 5.4: Validate task premises

After generating tasks, Claude runs:

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval validate-tasks .tmp/deep-eval/<skill>_tasks.json
```

This asks Gemini for a verification shell command per task (grep, find, ls only — safe commands) and runs it to check that the task premise holds against the actual repo. If a task references "the Jira integration" but the repo has no Jira code, the task fails validation and gets regenerated.

### 5.5: Prepare allexcept prompt file

Before running agents, Claude concatenates the SKILL.md content of ALL OTHER skills into one file:

```
.tmp/deep-eval/all_except_<skill>.txt
```

This is what gets loaded into Agent A's prompt — all skills except the one being tested. If the file is over 25KB, a condensed version is built (frontmatter + key rules + truncated sections).

### 5.6: Spawn 6 agents

For each of the 3 tasks, two agents are spawned:

- **Agent A (all-except):** Claude with all skills EXCEPT the tested one. Tests whether other skills already cover this skill's value.
- **Agent B (with-skill):** Claude with the tested skill loaded. Tests whether the skill makes a difference.

All 6 agents run in parallel. Each has read-only access to the repos — no files are modified. Each agent saves its output to a designated file:

```
.tmp/deep-eval/<skill>_task1_allexcept.txt
.tmp/deep-eval/<skill>_task1_withskill.txt
.tmp/deep-eval/<skill>_task2_allexcept.txt
...
```

### 5.7: Screen response quality

Before judging, Claude checks each task's response pair:

- Are any responses truncated mid-sentence?
- Are any responses under 500 bytes (likely incomplete)?
- Is there a language mismatch (Python skill but JavaScript repo)?

Tasks with clearly unusable responses are skipped — no judge call is made.

### 5.8: Gemini judges (3 calls per task)

For each valid task, Claude runs:

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval judge \
  "<TASK_DESCRIPTION>" \
  .tmp/deep-eval/<skill>_task<N>_withskill.txt \
  .tmp/deep-eval/<skill>_task<N>_allexcept.txt \
  --comparison-type marginal
```

The judge uses **blind dimension scoring** — it does NOT see the skill content. It scores each response independently on 5 dimensions (1-5 scale):

| Dimension | What it measures |
|-----------|-----------------|
| Accuracy | Are claims correct? Are code patterns valid? |
| Specificity | Does it reference concrete files, functions, line numbers? |
| Actionability | Could a developer act on this immediately? |
| Completeness | Does it cover the full scope of the task? |
| Response posture | Does it verify claims before acting? Push back on questionable suggestions? |

The winner is computed from total score difference:
- Difference >= 3: clear winner
- Difference of 1-2: marginal winner
- Difference = 0: tie

Each task gets 3 judge calls (repeat-and-vote). Majority verdict wins. Confidence: HIGH if unanimous (3-0), LOW if 2-1 split.

### 5.9: Aggregate results

Only good-quality tasks count toward the verdict. Tasks where the judge reported poor test quality are excluded.

**Dimension deltas:** For each good-quality task, the per-dimension deltas (with_skill score - without_skill score) are averaged. The report shows the strongest dimension (highest positive delta) and weakest dimension (lowest/most negative delta).

**Verdicts:**
- If 0 good-quality tasks remain → **INCONCLUSIVE**
- **KEEP** (wins > losses and wins > ties)
- **HURTS** (losses > wins)
- **NO IMPACT** (otherwise — the skill doesn't make a measurable difference)

For preventive skills (red-team mode):
- **STRONG** (score >= 0.80)
- **WEAK** (score >= 0.50)
- **FRAGILE** (score < 0.50)

### 5.10: Verify no repo changes

After testing, Claude compares repo state with a snapshot taken before agents ran. If new changes are detected, it warns — but NEVER runs destructive commands to clean up (the user may have uncommitted work).

---

## Step 6: Report

Claude combines all 3 layers into a single report:

```
# Skill Evaluation: <skill-name>

## Layer 1: Rules (Static Analysis)

  SKILL.md exists                          PASS
  Description has use-case context          FAIL — lacks "use when" phrasing
  Token budget (under limit)               PASS — 235 tokens
  ...

## Layer 2: Rubric Scoring

### Individual Assessment                        ★★★★    KEEP

  Specificity:      5/5  Concrete rules with code patterns
  Redundancy:       4/5  One rule overlaps Claude's default
  ...

### Contextual Analysis

  Overlap with other skills:   MINOR — shares 2 rules with data-pipeline-patterns
  Conflict with CLAUDE.md:     NONE
  ...

## Layer 3: A/B Testing                          KEEP

| Task | Repo | Description | Winner | Acc | Spec | Action | Comp | Posture |
|------|------|-------------|--------|-----|------|--------|------|---------|
| 1 | site-analysis | Review server.py | with_skill (HIGH) | +1.0 | +1.7 | +0.3 | +0.7 | +1.0 |
| ...

## Final Verdict

KEEP — skill adds measurable value across review and debug tasks.
```

**Terminal summary (always printed):**

```
Evaluation complete for "python-conventions":
  Layer 1: 0 errors, 1 warning
  Layer 2: ★★★★ KEEP — specific team conventions Claude doesn't know
  Layer 3: KEEP (2W/0L/1T) — strongest: specificity (+1.7), weakest: posture (+0.3)
  Final:   KEEP

Full report: saved to evaluation-results/evaluate-skill-python-conventions-2026-05-13-1430.md
```

---

## Step 7: Save detailed log

If Layer 3 ran, a detailed A/B log is saved separately. This includes the full task descriptions, response summaries, judge reasoning, and per-vote scores. It's too long for the terminal — always saved to a file.

---

## What's in the report

For the evaluated skill:

1. **Layer 1 checklist** — pass/fail for each of the 9 Python rules
2. **Layer 2 individual rubric** — 5 dimensions, 1-5 scores with justifications
3. **Layer 2 contextual analysis** — overlap, conflicts, type appropriateness
4. **Layer 3 A/B results** (if tested) — per-task winners, dimension deltas, overall verdict
5. **Final verdict** — combining all 3 layers
6. **Suggestions** — numbered actionable items

---

## What Layer 3 does NOT test

Layer 3 tests: "Does having this skill's text in Claude's context make the output better?"

Layer 3 does NOT test: "Does Claude Code correctly decide when to load this skill?" That would require running real Claude Code in subprocess mode. Layer 2 partially compensates by evaluating the skill's description for trigger quality.
