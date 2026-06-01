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

If no repositories are found, Layer 3 cannot run — all tasks require a real repository. Warn the user: "No repositories found in repositories/ — Layer 3 requires at least one cloned repository for A/B testing."

### 6.3: Screen skills for testability

Before asking the user to select skills, run the screening step to let Gemini decide which skills can actually be A/B tested:

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval screen-skills skills/
```

This outputs JSON with `testable` and `not_testable` lists, each with reasons. **Save the screening output to `.tmp/deep-eval/skill-screening.json`** so the user can inspect why each skill was or wasn't considered testable.

Use this to inform the skill selection — show the user which skills Gemini flagged as not testable and why (e.g., "requires MCP connection", "orchestrates tools rather than teaching patterns").

### 6.4: Confirm skill selection and snapshot repos

If the user already selected skills in Step 0 (round 2), cross-reference with the screening results. If any of their selections were flagged as not testable, warn them:

```
Gemini flagged these skills as poor A/B candidates:
  - <skill-name>: "<Gemini's reason>"
  - <skill-name>: "<Gemini's reason>"

Proceed anyway, or remove them?
```

If the user hasn't selected skills yet, present the selection using screening results to pre-check/uncheck. Always use Gemini's actual screening output — never hardcode which skills are good or poor candidates.

Confirm before proceeding.

**Snapshot repo state** before any agents run:
```bash
for dir in repositories/*/; do
  if [ -d "$dir/.git" ]; then
    name=$(basename "$dir")
    git -C "$dir" status --porcelain 2>/dev/null | wc -l > .tmp/deep-eval/repo_snapshot_${name}.txt
  fi
done
```

**Important:** Identify the skill's target language from its content (e.g., Python, JavaScript, general). When building the repos.json, include a `language` field for each repo (detect from file extensions or README). Pass the skill's language so Gemini picks repos that match — a Python skill should not get tasks on JavaScript repos.

### 6.5: Prepare allexcept prompt files

**Do this ONCE, before processing any skill.** This is a mechanical step — build it early when context is fresh.

For each selected skill, concatenate the SKILL.md content of ALL OTHER skills and save to a file:

```bash
# For each selected skill, build the allexcept content
for skill_name in <selected_skills>; do
  allexcept=""
  for other_dir in skills/*/; do
    other_name=$(basename "$other_dir")
    if [ "$other_name" != "$skill_name" ] && [ -f "$other_dir/SKILL.md" ]; then
      allexcept+="--- $other_name ---"$'\n'
      allexcept+=$(cat "$other_dir/SKILL.md")
      allexcept+=$'\n\n'
    fi
  done
  echo "$allexcept" > ".tmp/deep-eval/all_except_${skill_name}.txt"
done
```

**Verify all files were created** before proceeding:
```bash
for skill_name in <selected_skills>; do
  if [ ! -s ".tmp/deep-eval/all_except_${skill_name}.txt" ]; then
    echo "ERROR: Missing allexcept file for $skill_name"
  fi
done
```

Do NOT skip this step. Do NOT build allexcept prompts on the fly during agent dispatch — use these pre-built files.

**Size check and condensation:** After building each allexcept file, check its size:
```bash
size=$(wc -c < ".tmp/deep-eval/all_except_${skill_name}.txt")
echo "$skill_name allexcept: $size bytes"
```

If the file exceeds 25,000 bytes, build a condensed companion:
1. For each skill in the allexcept file, keep: full YAML frontmatter, any "When to Activate" / "When to Use" section, any lines containing MUST/NEVER/ALWAYS rules, and the first 200 characters of each remaining section followed by `[... truncated]`
2. Save to `.tmp/deep-eval/all_except_${skill_name}_condensed.txt`
3. Use the condensed version in the agent prompt instead of the full version
4. Log: `"Using condensed allexcept for $skill_name ($size bytes → condensed)"`

When inlining allexcept content into the agent prompt:
- Read the allexcept file completely — do not skip or summarize
- If using condensed version, change the agent prompt preamble to: "You have the following skills loaded (condensed — frontmatter and key rules preserved):"
- NEVER silently truncate — either use the full version or explicitly use the condensed version

### 6.6: Run A/B tests — one skill at a time

**Process each selected skill sequentially.** Complete ALL steps (agents → verify files → judge → verdict) for one skill before starting the next. Do NOT start the next skill until the current one is fully judged.

The engine auto-detects whether each skill is preventive (contains "never", "do not", "must not" patterns). Preventive skills use red-team mode (adversarial tasks testing whether the skill prevents bad behavior). Standard skills use A/B mode (tasks testing whether the skill improves output quality). No user flag needed.

**For each selected skill, do steps a–f in order:**

**a. Generate 3 tasks** using Gemini:

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval generate-tasks <SKILL_DIR> --repos-file .tmp/deep-eval/repos.json
```
This outputs JSON with 3 repo-based tasks: code review, code writing, and debugging. All 3 tasks create situations where the skill's rules would naturally apply.

**Important:** If the skill is language-specific and no matching-language repos exist, warn the user and use the closest available repos. Note the mismatch in the report.

**Save the task definitions to `.tmp/deep-eval/<skill>_tasks.json`**.

**a2. Validate task premises:**

After generating tasks, verify each task's premise holds for its target repository:

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval validate-tasks .tmp/deep-eval/<skill>_tasks.json
```

Read the validation output. If any task fails validation:
1. Log the failure reason
2. Regenerate tasks with the additional constraint: "Do NOT reference [failed premise] in [repo]."
3. Re-validate. If still failing after 1 retry, use the task anyway but flag it in the report.

Save validation results to `.tmp/deep-eval/<skill>_validation.json`.

**b. Spawn 6 subagents in parallel** (3 tasks × 2 conditions) in a single message with multiple Agent tool calls. All 6 agents are for THIS skill only.

Each agent saves its own output to a designated file. The orchestrator does NOT relay or save agent responses — the agents write directly to disk.

Two conditions per task:
- **Agent A (all-except):** All skills EXCEPT the tested one — tests marginal value
- **Agent B (with-skill):** Only the tested skill loaded — tests with the skill active

No bare condition — the marginal comparison (all-except vs with-skill) is the primary verdict and determines whether the skill earns its place. The absolute comparison (bare vs with-skill) was dropped because it doesn't answer the key question: "does this skill add value beyond what other skills already provide?"

**Agent A (all-except) — all skills EXCEPT the tested one loaded:**

Read the file `.tmp/deep-eval/all_except_<skill>.txt` and INLINE its full content directly into the agent prompt below. Do NOT tell the agent to read the file — paste the content so the agent has it in its prompt from the start.

```
You have the following skills loaded:

<skills>
[INLINE the full content of .tmp/deep-eval/all_except_<skill>.txt here — do NOT use a file pointer]
</skills>

YOUR TASK: [task description from Gemini]

IMPORTANT RULES:
- You have READ-ONLY access to the repository. You may use Read, Bash(grep/find/cat), and other read tools.
- Do NOT modify any files in the repository. Do NOT run git commit, git push, or any destructive command.
- Do NOT read any files under the skills/ directory.
- Be specific and reference actual files, line numbers, and code patterns you find.
- Keep your analysis under 800 words.

OUTPUT: Write your COMPLETE analysis to .tmp/deep-eval/<skill>_task<N>_allexcept.txt using the Write tool. This is your primary deliverable — the file content is what gets judged.
After writing the file, end your response with a 1-2 sentence summary of what you found.

[If task has a repo]: Work in the repository at: [repo path]
```

**Agent B (with-skill) — the tested skill loaded:**
```
You have the following skill loaded:

<skill>
[full SKILL.md content of the tested skill]
</skill>

YOUR TASK: [task description from Gemini]

IMPORTANT RULES:
- You have READ-ONLY access to the repository. You may use Read, Bash(grep/find/cat), and other read tools.
- Do NOT modify any files in the repository. Do NOT run git commit, git push, or any destructive command.
- Do NOT read any files under the skills/ directory.
- Be specific and reference actual files, line numbers, and code patterns you find.
- Keep your analysis under 800 words.

OUTPUT: Write your COMPLETE analysis to .tmp/deep-eval/<skill>_task<N>_withskill.txt using the Write tool. This is your primary deliverable — the file content is what gets judged.
After writing the file, end your response with a 1-2 sentence summary of what you found.

[If task has a repo]: Work in the repository at: [repo path]
```

**c. Wait for all 6 agents to complete, then verify output files exist.**

After all 6 agents for this skill finish, verify every expected file was written:

```bash
missing=0
for n in 1 2 3; do
  for condition in allexcept withskill; do
    file=".tmp/deep-eval/<skill>_task${n}_${condition}.txt"
    if [ ! -s "$file" ]; then
      echo "MISSING: $file"
      missing=$((missing + 1))
    fi
  done
done

if [ "$missing" -gt 0 ]; then
  echo "WARNING: $missing output files missing — some agents may not have written their results"
fi
```

If any files are missing, check what happened. The agent may have returned its analysis in the response text instead of writing to the file. In that case, use the Write tool to save the agent's response from the task notification `result` field to the correct file. **Save the complete text — do NOT summarize.**

**d. Screen response quality before judging.**

For each of the 3 tasks, check whether the agent responses are complete enough to compare. Read both output files (allexcept, withskill) for the task and check:

- Are any responses truncated mid-sentence or mid-code-block?
- Are any responses under 500 bytes (likely incomplete)?
- Did the task produce a language mismatch (e.g., Python skill but JavaScript repo)?

If a task has clearly unusable responses (both truncated, language mismatch making comparison meaningless), mark it as `skipped_poor_quality` with a reason and do NOT run judge calls for it. This saves API calls on tests that can't produce meaningful signal.

If responses look reasonable (even if imperfect), proceed to judging — the judge also reports `test_quality` as a second filter.

**e. Run 3 judge calls** (1 per non-skipped task):

**Marginal value (A vs B):** Does the skill add value beyond what OTHER skills already provide?
```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval judge \
  "<TASK_DESCRIPTION>" \
  .tmp/deep-eval/<skill>_task<N>_withskill.txt \
  .tmp/deep-eval/<skill>_task<N>_allexcept.txt \
  --comparison-type marginal
```

The judge uses blind dimension scoring — it does NOT see the skill content. It scores both responses on accuracy, specificity, actionability, and completeness (1-5 each), then determines the winner by total score difference.

This is the only comparison that matters — it answers "does this skill earn its place in the full setup?"

**f. Aggregate this skill's results** and determine its verdict (see 6.8 for verdict rules).

**g. Tell the user** the result for this skill before moving on:
```
Skill "<skill-name>" complete:
  Marginal: <verdict> (<wins>W/<losses>L/<ties>T)
  Strongest dimension: <dim> (+X.X), weakest: <dim> (+X.X)
  Moving to next skill...
```

**Then move to the next selected skill and repeat steps a–f.**

### 6.7: Verify no changes were made

After ALL skills are tested, compare repo state with the snapshot taken in step 6.4:

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

### 6.8: Aggregate results

For each skill, aggregate the marginal verdict across all tasks. **Only count tasks with good test quality.** Exclude:
- Tasks skipped in the pre-judge screening (step 6.6d)
- Tasks where the judge reported `test_quality: "poor"` — these are noted in the report but don't count toward the verdict

**Marginal value** (all-except vs with-skill): Does the skill add value beyond what OTHER skills provide?
- Count wins, losses, ties from good-quality judge results only

**Dimension deltas:** For each good-quality task, read the `dimension_deltas` from the judge output. Average the deltas across all good-quality tasks to produce overall dimension scores. Report the strongest dimension (highest positive delta) and weakest dimension (lowest or most negative delta). The 5 dimensions are: accuracy, specificity, actionability, completeness, response_posture.

If all dimension deltas are within [-0.5, +0.5], the skill has NO IMPACT regardless of win/loss count — the differences are noise.

Verdicts (based on good-quality tasks only):
- If 0 good-quality tasks remain → **INCONCLUSIVE** (all tests were poor quality)
- **KEEP** (wins > losses and wins > ties), **HURTS** (losses > wins), **NO IMPACT** (otherwise)
- Red-team mode verdict: **STRONG** (score ≥ 0.80), **WEAK** (score ≥ 0.50), **FRAGILE** (score < 0.50)

### 6.9: Save the detailed Layer 3 log

Write to `evaluate-setup-deep-log.md` (if that file exists, append a number: `evaluate-setup-deep-log-2.md`, etc.). This log is always saved to a file, never printed to terminal — it's too long.

```markdown
# Layer 3 Deep Evaluation Log

**Date:** [today]
**Skills tested:** [list]
**Repositories used:** [list]
**Mode:** [standard or red-team — auto-detected per skill]

## How This Evaluation Works

For each skill below, we ran 3 tasks on your actual repositories (review, write, debug).
Each task was run TWICE:
- **Agent A (all-except):** Claude with all skills EXCEPT the tested one
- **Agent B (with-skill):** Claude with the tested skill loaded

One judgment per task:
- **Marginal (A vs B):** Does the skill add value beyond what OTHER skills provide?

Gemini judges each pair with 3 blind votes using dimension scoring (accuracy, specificity, actionability, completeness, response_posture). The judge does NOT see the skill content — it evaluates purely on output quality.
Tasks with poor test quality are excluded from the verdict.

No files were modified during testing — all repository access was read-only.

---

## skill-name                                    KEEP

> Task definitions: `.tmp/deep-eval/<skill>_tasks.json`

### Task 1 (review on repo-name): [task description]

**Response A (all-except):** [summary]
**Response B (with-skill):** [summary]

**Marginal:** with_skill (HIGH)
**Dimensions:** accuracy +1.0, specificity +1.7, actionability +0.3, completeness +0.7, response_posture +0.3

---

[Tasks 2-3 follow same format]

### Skill Verdict
  Marginal:  KEEP (2 wins, 0 losses, 1 tie) — skill adds value beyond other skills
  Dimensions: strongest specificity (+1.7), weakest response_posture (+0.3)
```

Tell the user: "Layer 3 detailed log saved to `<filename>`."

### 6.10: Add Layer 3 results to the main report's Redundancy dimension

Layer 3 results go in the main report. For each tested skill, add:

```
### Layer 3 A/B Results: skill-name

| Task | Repo | Description | Winner | Acc | Spec | Action | Comp | Posture |
|---|---|---|---|---|---|---|---|---|
| 1 | site-analysis | Review server.py for refactoring | with_skill (HIGH) | +1.0 | +1.7 | +0.3 | +0.7 | +1.0 |
| 2 | eval-playground | Implement SimilarityScorer | tie (LOW) | 0.0 | +0.3 | -0.3 | 0.0 | 0.0 |
| 3 | qe-ds-il-agent | Debug search result failures | with_skill (HIGH) | +0.7 | +1.3 | +0.7 | +1.0 | +0.3 |
| **Overall** | | | **KEEP (2W/0L/1T)** | **+0.6** | **+1.1** | **+0.2** | **+0.6** | **+0.4** |

Dimension deltas are (with_skill score - without_skill score) averaged across 3 judge votes.
Positive = skill helps on that dimension. Negative = skill hurts.
```

Only include tasks with good test quality in the main table. Note excluded tasks below:
```
Tasks excluded due to poor test quality:
  Task 2: Both responses truncated mid-implementation.
```
