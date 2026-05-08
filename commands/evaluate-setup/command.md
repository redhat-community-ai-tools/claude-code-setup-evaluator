---
description: "Evaluate your Claude Code setup — skills, commands, agents, CLAUDE.md. Identifies what to keep, remove, merge, and fix."
---

# /evaluate-setup

You are running **the-evaluator** — a health check for Claude Code setups. You will evaluate skills, commands, agents, CLAUDE.md files, and hooks, then produce a report with verdicts and recommendations.

## Hard Rules

1. **Never give a verdict without running the rubric.** You MUST read the actual file content and score all rubric dimensions before assigning a star rating or verdict. Layer 1 error/warning counts are input data, not the verdict — a file with 10 false-positive warnings can still be ★★★★★.
2. **Every item must have a full rubric score block.** If a rubric score block is missing for any evaluated item, the review is incomplete. Every skill, command, agent, CLAUDE.md, and hook MUST have all dimensions scored with one-sentence justifications before the verdict line. No exceptions, no shortcuts.
3. **Read before you judge.** Do not summarize an item based on Layer 1 output alone. You must read the actual file content to evaluate quality, clarity, and redundancy. Layer 1 catches mechanical issues. Layer 2 catches everything else.
4. **Don't manufacture problems.** If the setup is good, say so. Not every run needs to produce a list of changes. A healthy setup with minor cosmetic issues should get a clear "your setup is solid" verdict — not a long list of suggestions that creates unnecessary work. Only recommend changes that would make a real difference. "You could trim 50 tokens from this skill" is not a real recommendation. "This skill duplicates another and wastes 1,000 tokens every session" is.
5. **Always end with a short summary.** Regardless of output format, the last thing the user sees in the terminal must be a short summary (see Step 5b). The full review is either above in the terminal or saved to a file — the summary tells the user the bottom line and where to find details.

## Step 0: Ask the User Before Starting

This is a two-round question flow. Ask round 1 first, then ask round 2 based on the answers.

### Round 1: Ask these 3 questions together in a single AskUserQuestion call

1. **Scope:** "What do you want to evaluate on Layers 1+2?"
   - **Everything** — skills + commands + agents + CLAUDE.md + hooks
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

Present the skill list dynamically. Run `screen-skills` first (Step 6.3) to let Gemini classify each skill as testable or not. Then present the results to the user with pre-checked/unchecked based on Gemini's assessment:

```
Which skills should Layer 3 (A/B testing) evaluate?

  [For each skill found in the workspace, show Gemini's assessment:]
  N. [x] <skill-name>    — <Gemini's reason: e.g., "teaches specific patterns">
  N. [ ] <skill-name>    — <Gemini's reason: e.g., "workflow orchestrator, not single-turn">

Select by number (e.g. 1-3, all, 1 2 5):
```

If `screen-skills` hasn't run yet (e.g., user jumped straight to Round 2), run it now before presenting the list. Never hardcode skill names — always discover from the workspace.

**If the user chose file output:** Check if `evaluate-setup-report.md` already exists. If it does, ask the user for a different filename — do NOT overwrite existing reports.

### Flow matrix

| Scope | Layers | What runs |
|---|---|---|
| Everything | All | L1 all → L2 all → L3 selected skills/agents |
| Everything | 1 + 2 | L1 all → L2 all |
| Everything | 3 only | L3 selected skills/agents only |
| Skills only | All | L1 skills → L2 skills → L3 selected skills |
| Skills only | 1 + 2 | L1 skills → L2 skills |
| Skills only | 3 only | L3 selected skills only |
| Specific item | All | L1 + L2 + L3 on that item |
| Specific item | 1 + 2 | L1 + L2 on that item |
| Specific item | 3 only | L3 on that item |

## Arguments

`$ARGUMENTS` may include:
- A path (e.g., `~/.claude/skills/`, `skills/<skill-name>/`)
- `--preset strict` or `--preset security` (default: recommended)
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

Layer 1 checks include: frontmatter validation, description quality (third-person POV, use-case context, length), adaptive token budget and 500-line limit, broken file references, TF-IDF cosine similarity for near-duplicate detection (threshold 0.85), prompt injection patterns (17 patterns), credential access references, and dangerous commands. For commands: prompt injection and credential access checks. For agents: description required, referenced skills exist, disallowedTools format, constraint-body enforcement match, prompt injection, credential access.

## Step 2: Read Actual Files (Layer 2 Preparation)

*Skip this step if the user chose "Layer 3 only".*

Read the actual content of:
1. Every skill file (SKILL.md) in the scan path
2. **All files in each skill's `skills/` subdirectory** (if it exists) — these are reference files with detailed content. Score the COMBINED content (SKILL.md + reference files), not just the entry point.
3. **Each skill's `guidelines.md`** (if it exists) — behavioral rules, hard limits, safety constraints
4. Every command file (command.md) found nearby
5. Every agent file (.md files in `agents/` directories)
6. The user's CLAUDE.md files (project and user level)

You need the actual content — not just the Layer 1 JSON — to evaluate quality, redundancy, and content. For skills with reference files, the SKILL.md is just the entry point — the real content is in the reference files.

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
- 1: No description, or description triggers on everything, or uses coercive language with broad scope
- 2: Description exists but is too broad, too narrow, or uses coercive language with narrow scope
- 3: Description is reasonable but could be more precise
- 4: Good description that targets the right tasks most of the time
- 5: Description precisely targets the right tasks; starts with "Use when"; doesn't overlap with other skills

**Autonomy impact (scored within Trigger quality):** Skills should guide, not mandate. Check for these patterns:
- **Coercive language in description:** "MUST use this", "ALWAYS use this before", "NEVER skip" — these override the user's choice of when to activate the skill. A skill description should describe *when it's relevant*, not *demand* it runs. Cap trigger quality at 2/5 if the description mandates activation.
- **Hard gates in skill body:** `<HARD-GATE>`, "Do NOT proceed until", "STOP and do X first" — these block the user's workflow unless the skill's precondition is met. Hard gates are appropriate for narrow safety concerns (e.g., "don't commit secrets") but not for broad creative workflows.
- **Broad category intercept:** "any creative work", "all code changes", "every project", "whenever you write code" — skills that claim authority over entire categories of work will trigger too often and erode user trust. A good skill targets a specific task type, not a category of all human activity.
- **The test:** Ask "could a reasonable user want to skip this skill and go straight to coding?" If yes, the trigger language shouldn't prevent that.

**Token efficiency (weight 0.15)**
- 1: >3,000 tokens with low value density
- 2: 2,000-3,000 tokens, or under 1,500 with very low value
- 3: Under 1,500 tokens, some padding that could be trimmed
- 4: Well-sized, minor optimization possible
- 5: Every token earns its place; high value-to-token ratio

Note: Token budget applies to the SKILL.md file only (the always-loaded cost). Reference files in a `skills/` subdirectory load on demand and cost zero tokens until Claude reads them. A 200-token SKILL.md with 2,000 tokens of reference files is more efficient than a 2,200-token monolithic SKILL.md. If a skill's SKILL.md is over ~800 tokens and contains detailed procedures, tables, or multi-step processes, recommend splitting into a thin SKILL.md + reference files (progressive disclosure — Anthropic-recommended pattern). This is not an error — just a recommendation.

**Content quality (weight 0.15)**
- 1: No structure, no examples, broken references
- 2: Minimal structure, vague instructions
- 3: Decent structure, some examples, no broken references
- 4: Well-organized with examples and clear sections
- 5: Well-organized, includes examples, references valid files, covers edge cases

**Additional quality checks (score within Content quality):**
- **Cognitive load:** For workflow-type skills with sequential steps — are steps digestible? Does any single phase require synthesizing more than 3 inputs? Are there checkpoints for long processes? Score N/A for pure knowledge skills.
- **Error handling:** For skills that execute commands, call APIs, or reference external tools — does the skill define what happens when something fails? Are escalation paths clear? Score N/A for pure knowledge skills that only teach conventions.
- **Guidelines separation:** If the skill has a `guidelines.md`, evaluate it: are behavioral rules specific and enforceable? Do they conflict with CLAUDE.md? If the skill does NOT have `guidelines.md` but contains hard limits or safety constraints inline (MUST/NEVER/ALWAYS), recommend extracting to `guidelines.md` for better separation of concerns. This is not a requirement — not having guidelines.md is not a negative score. It's a recommendation for complex skills.

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
| **Conciseness** | 0.25 | Can each line pass "would removing this cause Claude to make mistakes?" Ruthlessly prune — Anthropic's guidance. |
| **Signal-to-noise** | 0.25 | Only contains things Claude can't figure out from code? No generic advice like "write clean code", "be helpful", "follow best practices", "think step by step"? These waste tokens — Claude already does them by default. Also check: no standard language conventions (use linters instead), no detailed API docs (link instead), no file-by-file descriptions. |
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
| **Token efficiency** | 0.10 | Concise or bloated? See command size thresholds below. |
| **Redundancy with defaults** | 0.15 | Does Claude already do this without the command? Claude has built-in plan mode, generates commit messages, explains code, and reviews code by default. A command is only justified if it adds specific rules, constraints, or structure that Claude wouldn't follow unprompted. Ask: "if I deleted this command, could I get the same result by just asking Claude?" If yes → redundant. |
| **Robustness** | 0.10 | Does the command handle edge cases? Does it hardcode assumptions (specific tools, languages, thresholds) that should be detected from the project? Does it depend on skills loading reliably? Does it gracefully handle missing dependencies? |

**Command size thresholds (scored within Token efficiency):** Commands use the same progressive disclosure principle as skills. A monolithic command.md loads its entire content when invoked — the larger it is, the more context it burns.
- Under 15KB: Fine. Most commands are 1-5KB.
- 15-30KB: Recommend splitting into a thin command.md (execution steps, rubric) + reference files that Claude reads on demand. Score token efficiency at most 2/5.
- Over 30KB: Strong recommendation to split. The command is doing too much in one file. Score token efficiency at most 1/5.
- A command.md that references separate files for optional/conditional sections (e.g., Layer 3 protocol loaded only when the user selects it) is more efficient than one that inlines everything.

## Step 3d: Evaluate Hooks (if --hooks or --all)

For each hook, check:
- Does the hook have a clear purpose?
- Does the referenced script/command exist?
- Are there dangerous patterns (rm -rf, force push)?
- Is this the right mechanism? (hooks are deterministic — 100% execution. If the behavior is advisory, it should be in CLAUDE.md or a skill instead.)

## Step 3e: Evaluate Agents (if agents were found during scan)

*Skip this step if the user chose "Layer 3 only" or no agents were found.*

Score each agent on 5 dimensions:

**Specificity (weight 0.25)**
- 1: Entirely vague: "implement the fix", "review the code", no concrete procedure
- 3: Mix of specific phases and vague steps
- 5: Every phase has specific steps, concrete rules, defined output format

**Constraint clarity (weight 0.25)** — replaces Redundancy (agents define new roles, not knowledge Claude already has)
- 1: No constraints stated — agent can do anything
- 3: Constraints exist in body and `disallowedTools` but with gaps
- 5: Body constraints and `disallowedTools` form a coherent, complete security boundary; every "cannot" in the body is backed by enforcement; scope is explicitly bounded ("you do X — you do not do Y, Z, or W")

**Zero-trust integrity (weight 0.20)** — replaces Trigger quality (agents are dispatched by harness, not description-matched)
- 1: No mention of input trust; agent blindly follows issue text or PR descriptions
- 3: States zero-trust principle but verification steps are inconsistent
- 5: Explicit zero-trust section; all external inputs treated as untrusted; concrete verification steps; injection-like patterns in input are flagged rather than followed

**Token efficiency (weight 0.15)**
- 1: >5,000 tokens with low value density
- 3: Under 3,000 tokens, some padding
- 5: Every token earns its place; procedures are in skills (not inlined), no repeated boilerplate across agents

**Content quality (weight 0.15)**
- 1: No structure, no output format, no failure handling
- 3: Decent structure; output format defined but incomplete; failure handling vague
- 5: Clear sections (identity, inputs, constraints, procedure, output, failure); output format with schema; exit codes documented; handoff contract with pre/post scripts explicit

### Scoring

Same as skills: `round(specificity*0.25 + constraint_clarity*0.25 + zero_trust*0.20 + efficiency*0.15 + quality*0.15)`

Verdicts: **KEEP** (4-5 stars), **REVIEW** (3 stars), **REMOVE** (1-2 stars).

### Per-Agent Output Format

```
### code                                        ★★★★    KEEP
  Tokens: 2,456
  Model: opus
  Skills: code-implementation
  DisallowedTools: 14 patterns

  Rubric:
    Specificity:        5/5  Five named phases with concrete steps
    Constraint clarity:  4/5  13/14 body constraints enforced by disallowedTools
    Zero-trust:         5/5  Explicit section; verifies issue claims against code
    Token efficiency:   3/5  2,456 tokens — secret scanning duplicated with fix.md
    Content quality:    5/5  Output format, exit codes, failure handling defined

  + Zero-trust principle with concrete verification steps
  ! 340 tokens of secret scanning text identical to fix.md — extract to shared skill
  x Skill 'code-implementation' not found (Layer 1 error)
```

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

**Agent ↔ Skill consistency** — Do the agent's referenced skills exist? Do the agent's instructions conflict with the referenced skill's instructions? Is the agent duplicating content that's already in its referenced skills?

**Agent ↔ Agent overlap** — Do multiple agents share large blocks of identical text (zero-trust sections, constraint lists, secret scanning paragraphs)? If so, suggest extraction to a shared skill.

**Agent ↔ CLAUDE.md** — Are there rules in CLAUDE.md that should be in agent definitions? Are there rules in agent definitions that should be in CLAUDE.md?

**Skill structure optimization** — For skills with SKILL.md over ~800 tokens that contain detailed procedures, tables, or multi-step processes: recommend splitting into a thin SKILL.md (~200 tokens with routing) + reference files in a `skills/` subdirectory. This follows Anthropic's progressive disclosure pattern — reference files cost zero context until Claude reads them on demand. Not an error if missing — just a recommendation for improving token efficiency.

**Guidelines extraction** — For skills that contain hard limits, safety constraints, or behavioral rules (MUST/NEVER/ALWAYS patterns) inline in SKILL.md: recommend extracting to a separate `guidelines.md` file. This improves separation of concerns (what to do vs. how to behave) and makes behavioral rules easier to evaluate. Not a requirement — just a recommendation for complex skills.

### Setup-wide checks:

- **Merge candidates**: Skills covering related topics that would be stronger combined
- **Overlapping triggers**: Skills whose descriptions might cause multiple to load unnecessarily
- **Coverage gaps**: Obvious missing areas based on what's present
- **Total context budget**: Sum all skills + CLAUDE.md + commands tokens, warn if >20% of context window
- **Redundancy across types**: Same instruction appearing in CLAUDE.md AND a skill (double token cost)
- **Conflicts across types**: CLAUDE.md says one thing, a skill says the opposite

### Behavioral pattern checks (setup-wide):

These checks look at patterns across the whole setup, not individual items:

- **Mandate stacking**: Count skills that use coercive language (MUST, ALWAYS, NEVER) in descriptions or hard gates in body. If >2 skills mandate pre-conditions, they create conflicting demands — Claude can't MUST do everything before every task. Flag: "N skills use mandatory language — this creates competing mandates that erode reliability. Consider making most of them advisory ('Use when...') and keeping hard mandates only for genuine safety constraints."
- **Autonomy erosion**: If the setup has skills that intercept broad work categories (e.g., "any creative work", "all code changes") AND those skills contain hard gates, the user loses control of their workflow. Flag when broad-trigger + hard-gate skills exist: "This skill claims authority over [broad category] and blocks progress until its precondition is met. This fights user autonomy — consider narrowing the trigger or removing the hard gate."
- **Broad trigger collision**: Multiple skills with overlapping broad triggers (e.g., two skills both triggering on "Python files" or "code changes") waste context by loading redundant instructions. Different from "overlapping triggers" above — this specifically checks for skills that cast too wide a net individually, not just overlap with each other.

### Example transformation suggestions:

```
## Cross-Type Optimization

  ⟳ Skill → Hook: <skill> says "always run X before pushing" —
    this should be a hook to guarantee it runs every time, not a skill that
    Claude might skip.

  ⟳ Skill → Command: <skill> says "you MUST use this before any creative work" —
    the hard gate makes it behave like a command. Consider making it a /command
    instead.

  ⟳ CLAUDE.md → Skill: The "<section>" in CLAUDE.md (lines N-M) contains
    domain-specific rules that only matter sometimes. Move to a skill that
    loads on demand.

  ✓ No conflicts detected between CLAUDE.md and skills.
  ✓ No redundant content detected across types.
```

These are illustrative patterns — always use the actual skill/command names from the workspace being evaluated.

## Step 5: Produce the Report

Read `commands/evaluate-setup/report-format.md` for the full report structure, per-item output format, and terminal summary rules.

## Step 6: Deep Evaluation (Layer 3)

*Run this step if the user chose "All" or "Layer 3 only" for layers.*

Read `commands/evaluate-setup/layer3-protocol.md` for the complete Layer 3 protocol: prerequisites, repo discovery, skill screening, A/B test execution (3-condition design with 12 subagents), judging, aggregation, and log format.
