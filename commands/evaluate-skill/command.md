---
description: "Deep-evaluate a single skill — static analysis, contextual rubric scoring, and A/B redundancy testing. Runs all 3 layers on one skill to determine if it earns its place."
argument-hint: "[skill-name or path]"
---

# Evaluate Skill — Deep Single-Skill Evaluation

Run all 3 evaluation layers on a single skill to determine whether it earns its place in your setup.

- **Layer 1 (Rules):** Static analysis — frontmatter, tokens, references, injection patterns, description quality
- **Layer 2 (Prompt):** Contextual rubric scoring — evaluate this skill individually AND in context of all other skills, commands, and CLAUDE.md
- **Layer 3 (A/B Testing):** Empirical test — does this skill actually change Claude's behavior?

## Hard Rules

1. **Never give a verdict without running the rubric.** You MUST read the actual file content and score all rubric dimensions before assigning a star rating or verdict. Layer 1 diagnostics are input data, not the verdict.
2. **Every dimension must have a score and justification.** No shortcuts. Both the individual rubric AND the contextual analysis must be fully scored before the verdict line.
3. **Read before you judge.** Do not summarize based on Layer 1 output alone. You must read the actual SKILL.md content (and reference files if they exist) to evaluate quality.
4. **Don't manufacture problems.** If the skill is good, say so. Only recommend changes that would make a real difference.
5. **Always end with a short summary.** Regardless of output format, the last thing the user sees is the terminal summary.

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

If file: save to `evaluation-results/evaluate-skill-<skill-name>-YYYY-MM-DD.md`. Create the `evaluation-results/` directory if it doesn't exist. If the file already exists (second run same day), append a counter: `-2`, `-3`, etc.

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

### 4.1: Read the files

Read the skill's actual content:
1. The SKILL.md file
2. All files in the skill's `skills/` subdirectory (reference files). Score the COMBINED content (SKILL.md + reference files), not just the entry point.
3. The skill's `guidelines.md` (if it exists) — behavioral rules, hard limits, safety constraints

Also read for context (but don't score these — they're context for evaluating the target skill):
4. All OTHER skill SKILL.md files in the workspace — to check for overlap and redundancy
5. CLAUDE.md — to check for conflicts and duplication
6. Hooks in `.claude/settings.json` — to check if the skill should be a hook instead

### 4.2: Individual Rubric (5 dimensions)

Score the skill on 5 dimensions. Each dimension gets a 1-5 score with a one-sentence justification citing specific evidence from the skill content.

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

Also check for overlap with Claude's built-in behavior. Claude already does many things by default (plan mode, code review, commit messages, code explanation). A skill that just wraps a Claude default without adding specific rules is redundant. Ask: "if I deleted this skill, would Claude behave differently?" If not → redundant.

Check redundancy against three sources:
- Claude's default behavior (generic advice = redundant)
- Other skills in the workspace (overlap = partially redundant)
- CLAUDE.md content (duplication = wasted tokens)

**Trigger quality (weight 0.20)**
- 1: No description, or description triggers on everything, or uses coercive language with broad scope
- 2: Description exists but is too broad, too narrow, or uses coercive language with narrow scope
- 3: Description is reasonable but could be more precise
- 4: Good description that targets the right tasks most of the time
- 5: Description precisely targets the right tasks; starts with "Use when"; doesn't overlap with other skills

**Autonomy impact (scored within Trigger quality):** Skills should guide, not mandate.
- **Coercive language in description:** "MUST use this", "ALWAYS use this before", "NEVER skip" — cap trigger quality at 2/5 if the description mandates activation.
- **Hard gates in skill body:** "Do NOT proceed until", "STOP and do X first" — appropriate for narrow safety concerns, not broad workflows.
- **Broad category intercept:** "any creative work", "all code changes" — skills that claim authority over entire categories will over-trigger.
- **The test:** Ask "could a reasonable user want to skip this skill and go straight to coding?" If yes, the trigger language shouldn't prevent that.

**Token efficiency (weight 0.15)**
- 1: >3,000 tokens with low value density
- 2: 2,000-3,000 tokens, or under 1,500 with very low value
- 3: Under 1,500 tokens, some padding that could be trimmed
- 4: Well-sized, minor optimization possible
- 5: Every token earns its place; high value-to-token ratio

Note: Token budget applies to SKILL.md only (the always-loaded cost). Reference files in a `skills/` subdirectory load on demand and cost zero tokens until read. A 200-token SKILL.md with 2,000 tokens of reference files is more efficient than a 2,200-token monolithic SKILL.md. If SKILL.md is over ~800 tokens and contains detailed procedures or tables, recommend splitting into thin SKILL.md + reference files (progressive disclosure).

**Content quality (weight 0.15)**
- 1: No structure, no examples, broken references
- 2: Minimal structure, vague instructions
- 3: Decent structure, some examples, no broken references
- 4: Well-organized with examples and clear sections
- 5: Well-organized, includes examples, references valid files, covers edge cases

Additional quality checks (score within Content quality):
- **Cognitive load:** For workflow-type skills — are steps digestible? Does any phase require synthesizing more than 3 inputs? Score N/A for pure knowledge skills.
- **Error handling:** For skills that execute commands or call APIs — does the skill define what happens when something fails? Score N/A for pure knowledge skills.
- **Guidelines separation:** If the skill contains hard limits inline (MUST/NEVER/ALWAYS) but has no `guidelines.md`, recommend extracting. Not a negative score — a recommendation for complex skills.

**Scoring:**
- Calculate overall: `round(specificity*0.25 + redundancy*0.25 + trigger*0.20 + efficiency*0.15 + quality*0.15)`
- Assign verdict: **KEEP** (4-5 stars), **REVIEW** (3 stars), **REMOVE** (1-2 stars)

### 4.3: Contextual Analysis (5 dimensions)

Evaluate the skill in context of the whole setup. Each dimension gets a severity rating.

**Overlap with other skills** — NONE / MINOR / SIGNIFICANT
  Does any other skill cover the same domain? How much content is shared? Name the overlapping skills and the specific shared content. Could they be merged?

**Conflict with CLAUDE.md** — NONE / MINOR / SIGNIFICANT
  Does the skill contradict anything in CLAUDE.md? Cite the specific conflicting instructions.

**Conflict with other skills** — NONE / MINOR / SIGNIFICANT
  Does this skill's advice conflict with another skill's? Name the skills and the contradiction.

**Type appropriateness** — CORRECT / WRONG TYPE
  Should this be a skill (auto-triggered), a command (user-triggered), or a hook (deterministic)?
  - If the skill describes a user-triggered workflow → should be a command
  - If the skill contains rules that MUST happen every time → should be a hook
  - If the skill teaches passive behavior → correct as a skill

**Structure optimization** — OPTIMAL / COULD IMPROVE
  If SKILL.md is >800 tokens and monolithic: recommend splitting into thin SKILL.md + reference files.
  If the skill has inline hard limits but no `guidelines.md`: recommend extracting.

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

  Overlap with other skills:   [NONE/MINOR/SIGNIFICANT] — [findings]
  Conflict with CLAUDE.md:     [NONE/MINOR/SIGNIFICANT] — [findings]
  Conflict with other skills:  [NONE/MINOR/SIGNIFICANT] — [findings]
  Type appropriateness:        [CORRECT/WRONG TYPE] — [assessment]
  Structure optimization:      [OPTIMAL/COULD IMPROVE] — [findings]

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
