---
description: "Deep-evaluate a single skill — static analysis, contextual rubric scoring, and A/B redundancy testing. Runs all 3 layers on one skill to determine if it earns its place."
argument-hint: "[skill-name or path]"
---

# Evaluate Skill — Deep Single-Skill Evaluation

Run all 3 evaluation layers on a single skill to determine whether it earns its place in your setup.

- **Layer 1 (Rules):** Static analysis — frontmatter, tokens, references, injection patterns, description quality
- **Layer 2 (Prompt):** Contextual rubric scoring — evaluate this skill individually AND in context of all other skills, commands, and CLAUDE.md
- **Layer 3 (A/B Testing):** Empirical test — does this skill actually change Claude's behavior?

## Step 1: Select the Skill

Discover all skills in the workspace (search for directories containing SKILL.md files).

**If `$ARGUMENTS` contains a skill name or path:** Verify it exists in the discovered list. If it does, use it directly — skip the selection prompt.

**If no valid skill in arguments:** Print the full skill list as numbered text and ask the user to type a name or number:

```
Available skills:

  1. accessibility          (1,485 tokens)
  2. article-writing        (610 tokens)
  3. data-pipeline-patterns (663 tokens)
  ...

Type a skill name or number:
```

Wait for the user's response. The user picks exactly one skill per invocation.

## Step 2: Ask Output Preference

Ask using AskUserQuestion:
- **Terminal** — print results here
- **File** — save to a file

If file: check if `evaluate-skill-<skill-name>.md` exists and ask for a different name if so.

## Step 3: Run Layer 1 (Rules)

Find the evaluator project directory:
```bash
PROJECT_DIR="$(find . -path '*/evaluate-setup/src/the_evaluator/cli.py' -not -path '*/.git/*' 2>/dev/null | head -1 | sed 's|/src/the_evaluator/cli.py||')"
```
If empty, fall back to `scripts/evaluate-setup`.

Run static analysis on the selected skill:
```bash
uv run --project "$PROJECT_DIR" evaluate-setup scan <SKILL_PATH> [--preset <PRESET>]
```

Read the JSON output. This gives you diagnostics with rule IDs, severities, and token counts for this skill.

## Step 4: Run Layer 2 (Prompt)

Read the skill's actual content:
1. The SKILL.md file
2. All files in the skill's `skills/` subdirectory (reference files)
3. The skill's `guidelines.md` (if it exists)

Also read for context (but don't score these — they're context for evaluating the target skill):
4. All OTHER skill SKILL.md files in the workspace — to check for overlap and redundancy
5. CLAUDE.md — to check for conflicts and duplication
6. Hooks in `.claude/settings.json` — to check if the skill should be a hook instead

### Rubric: Individual Assessment

Score the skill on 5 dimensions (same rubric as evaluate-setup):

**Specificity (0.25)** — Are instructions specific and actionable, or vague platitudes?
**Redundancy (0.25)** — Does this skill teach Claude something it doesn't already know? Check against:
  - Claude's default behavior (generic advice = redundant)
  - Other skills in the workspace (overlap = partially redundant)
  - CLAUDE.md content (duplication = wasted tokens)
**Trigger quality (0.20)** — Will the description activate on the right tasks?
**Token efficiency (0.15)** — Is it well-sized? Could it use progressive disclosure?
**Content quality (0.15)** — Structure, examples, references, error handling?

Score each 1-5 with one-sentence justification. Calculate overall star rating.

### Contextual Analysis

Beyond the individual rubric, evaluate the skill in context of the whole setup:

- **Overlap with other skills:** Does any other skill cover the same domain? How much content is shared? Could they be merged?
- **Conflict with CLAUDE.md:** Does the skill contradict anything in CLAUDE.md?
- **Conflict with other skills:** Does this skill's advice conflict with another skill's?
- **Type appropriateness:** Should this be a skill (auto-triggered), a command (user-triggered), or a hook (deterministic)?
- **Progressive disclosure:** If monolithic (>800 tokens), should it split into thin SKILL.md + reference files?

## Step 5: Run Layer 3 (A/B Testing)

### 5.1: Check prerequisites

Read `commands/evaluate-skill/layer3-protocol.md` step 6.1 for prerequisite checks (`GOOGLE_API_KEY`).

### 5.2: Screen for testability

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval screen-skills <SKILL_PATH>
```

If the skill is flagged as not testable, explain why and skip Layer 3:
```
Layer 3 skipped — Gemini flagged this skill as not testable:
  Reason: "<Gemini's reason>"

This skill can't be meaningfully A/B tested in a single response.
The Layer 1 + Layer 2 results above are still valid.
```

### 5.3: Run the A/B test

Read `commands/evaluate-skill/layer3-protocol.md` steps 6.5–6.8 for the full protocol:
- Pre-build the allexcept file for this skill
- Discover repos and snapshot state
- Generate 3 tasks (Gemini)
- Spawn 6 agents (3 tasks × 2 conditions: allexcept + withskill)
- Verify all 6 output files exist
- Screen response quality, then run 3 marginal judge calls
- Aggregate results (good-quality tasks only)

## Step 6: Produce the Report

Combine all 3 layers into a single report.

**Format:**

```markdown
# Skill Evaluation: <skill-name>

**Date:** [today]
**Tokens:** [SKILL.md tokens] (+[reference file tokens] in reference files)
**Reference files:** [list or "none"]
**Guidelines:** [yes/no]

---

## Layer 1: Rules (Static Analysis)

Present each check as a human-readable description with PASS or FAIL:

  SKILL.md exists                          PASS
  Frontmatter has description              PASS
  Description has use-case context          FAIL — lacks "use when" / "applies to" phrasing
  Frontmatter format valid                 PASS
  Token budget (under 1,500)               PASS — 235 tokens
  No broken file references                PASS
  No near-duplicates (>0.85 similarity)    PASS
  No prompt injection patterns             PASS
  No credential references                 PASS

Map each Layer 1 diagnostic to its corresponding check. Checks with no diagnostic = PASS. Checks with a diagnostic = FAIL with the message.

---

## Layer 2: Rubric Scoring

### Individual Assessment                        ★★★★    KEEP

  Specificity:      [score]/5  [justification]
  Redundancy:       [score]/5  [justification]
  Trigger quality:  [score]/5  [justification]
  Token efficiency: [score]/5  [justification]
  Content quality:  [score]/5  [justification]

### Contextual Analysis

  Overlap with other skills: [findings]
  Conflicts with CLAUDE.md: [findings]
  Type appropriateness: [skill/command/hook assessment]

  + What's good
  ! What could improve
  x What's broken

---

## Layer 3: A/B Testing                          KEEP

Only include tasks where the judge rated test quality as "good." Tasks rated "poor" are excluded from the table and verdict — note them below with the reason.

[If tested:]
| Task | Repo | Description | Marginal |
|------|------|-------------|----------|
| 1 | site-analysis | Review server.py for refactoring opportunities | tie (HIGH) |
| 2 | qe-ds-il-agent | Debug search result processing failures | with_skill (HIGH) |
| 3 | eval-playground | Implement SimilarityScorer utility | tie (LOW) |
| **Overall** | | | **NO IMPACT (1W/0L/2T)** |

[Tasks excluded due to poor test quality:]
  Task 3 (evaluation-playground): Both responses truncated mid-implementation — judge couldn't compare.

[If skipped:]
Skipped — skill is not testable ([reason]).

---

## Final Verdict

**[KEEP / REVIEW / REMOVE]** — [one-sentence summary combining all 3 layers]

[If actionable suggestions exist:]
Suggestions:
  1. [suggestion]
  2. [suggestion]
```

**Terminal summary (always printed):**

```
Evaluation complete for "<skill-name>":
  Layer 1: [N errors, N warnings]
  Layer 2: ★★★★ [verdict] — [one-line summary]
  Layer 3: [verdict] ([W]W/[L]L/[T]T) or "skipped (not testable)"
  Final:   [KEEP / REVIEW / REMOVE]

[Full report: saved to <filename> | printed above]
```

## Step 7: Save Detailed Log

If Layer 3 ran, always save the detailed log to `evaluate-skill-<skill-name>-log.md` (append number if exists). This includes full task descriptions, response summaries, and judge reasoning. See `layer3-protocol.md` step 6.9 for the log format.

Tell the user: "Detailed A/B log saved to `<filename>`."
