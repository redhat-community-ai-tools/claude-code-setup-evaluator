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
| **Token efficiency** | 0.10 | Concise or bloated? |
| **Redundancy with defaults** | 0.15 | Does Claude already do this without the command? Claude has built-in plan mode, generates commit messages, explains code, and reviews code by default. A command is only justified if it adds specific rules, constraints, or structure that Claude wouldn't follow unprompted. Ask: "if I deleted this command, could I get the same result by just asking Claude?" If yes → redundant. |
| **Robustness** | 0.10 | Does the command handle edge cases? Does it hardcode assumptions (specific tools, languages, thresholds) that should be detected from the project? Does it depend on skills loading reliably? Does it gracefully handle missing dependencies? |

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

*Skip this step if the user chose "Layer 3 only".*

### Step 5a: Full Review

If the user chose **terminal output**, print the full review directly. If they chose **file output**, write it to the chosen filename and tell the user where to find it.

Full review format — **structured around the four evaluation dimensions**:

```
## How This Evaluation Works

This report evaluates the Claude Code setup across four dimensions:

- **Readiness** — Can each component load and function?
- **Correctness** — Does each component work as intended and safely?
- **Redundancy** — Is each component adding value beyond defaults and other components?
- **Compliance** — Does each component follow Anthropic's published best practices?

Three layers produce the evidence:

**Layer 1 (Static Analysis)** — A set of Python rules that run
deterministically on every file. Each rule checks one thing mechanically:
does the file exist? Does the YAML parse? Are referenced files real? Is the
description well-formed (third-person, use-case context, length)? Is the
skill within the token/line budget? Are there prompt injection patterns (17
regex patterns)? Credential references? Dangerous commands (sudo, chmod 777)?
For skills with reference files, checks that routing targets exist. For
agents, checks disallowedTools format and constraint enforcement. Runs in
seconds, no AI involved, fully reproducible. Feeds into Readiness +
Correctness.

**Layer 2 (Rubric Scoring)** — A structured prompt that instructs Claude to
read every file and score it on weighted rubric dimensions. Claude reads the
actual content — SKILL.md, reference files, guidelines.md, command.md — and
judges quality, specificity, redundancy, and compliance with Anthropic's
published best practices. This is where human-like judgment happens: is this
skill teaching something Claude doesn't already know? Is the description
good enough to trigger at the right time? Are behavioral rules specific and
enforceable? Feeds into Redundancy + Compliance.

[If Layer 3 ran:]
**Layer 3 (A/B Testing)** — Empirical testing that runs ONLY for skills
(not commands, hooks, or agents). Tests whether a skill actually changes
Claude's behavior by running the same task under 3 conditions: (A) bare
Claude with no skills, (B) Claude with all skills EXCEPT the tested one,
(C) Claude with the tested skill. Gemini generates 4 tasks per skill (1
knowledge + 3 on real repositories) and judges two comparisons per task:
absolute value (A vs C: does the skill teach something new?) and marginal
value (B vs C: does the skill add value beyond what OTHER skills provide?).
Not all skills are testable — workflow orchestrators and multi-turn
interactive skills can't be meaningfully A/B tested in a single response.
Feeds into Redundancy.

---

## Inventory
  [table: type, count, tokens, reference files]

## Skills

Go through each skill one by one. For each skill, evaluate all four
dimensions and give a final verdict:

### skill-name                              ★★★★    KEEP
  Tokens: [SKILL.md tokens] (+[reference file tokens] in reference files)
  Reference files: [list or "none"]
  Guidelines: [yes/no]

  **Readiness:** [PASS/FAIL] — file exists, frontmatter valid, references resolve
  **Correctness:** [PASS/FAIL] — no injection patterns, no credential references,
    guidelines don't conflict with CLAUDE.md
  **Redundancy:** [score/5] — [one sentence: what's unique vs what Claude already knows]
    [If Layer 3 ran for this skill:]
    Layer 3 (A/B Testing): Tested with 4 Gemini-generated tasks:
      1. [task type]: "[short task description]" — Absolute: [verdict] | Marginal: [verdict]
      2. [task type]: "[short task description]" — Absolute: [verdict] | Marginal: [verdict]
      3. [task type]: "[short task description]" — Absolute: [verdict] | Marginal: [verdict]
      4. [task type]: "[short task description]" — Absolute: [verdict] | Marginal: [verdict]
      Overall: Absolute [verdict] ([wins]W/[losses]L/[ties]T) | Marginal [verdict] ([wins]W/[losses]L/[ties]T)
    [If Layer 3 did NOT run for this skill:]
    Layer 3: Not tested (skill is [reason: workflow orchestrator / multi-turn / not selected])
  **Compliance:** [summary of rubric scores]
    Specificity: [score/5] | Trigger: [score/5] | Token eff: [score/5] | Content: [score/5]

  + What's good
  ! What could improve
  x What's broken

[Repeat for each skill]

## Commands

Go through each command. For simple commands that score well, use a
compact format (one line per dimension). For commands with issues, use
the full format.

### command-name                            ★★★★    KEEP
  Tokens: [tokens]
  Readiness: PASS | Correctness: PASS | Redundancy: [unique/redundant] | Compliance: [score]

[Repeat for each command]

## Hooks

For each hook entry, evaluate:
  Readiness: [command exists, script exists]
  Correctness: [no dangerous patterns, correct mechanism]

## CLAUDE.md

### CLAUDE.md                               ★★★★    KEEP
  Tokens: [tokens] | Lines: [lines]

  **Readiness:** PASS
  **Correctness:** PASS — no conflicts with skills
  **Redundancy:** [signal-to-noise score] — [generic advice?]
  **Compliance:** Conciseness [score] | Signal-to-noise [score] | Skill separation [score] | Structure [score]

## Agents (if found)

[Same per-agent format with all 4 dimensions]

## Cross-Type Optimization
  [Transformation suggestions — only when genuinely beneficial]

## Suggestions
  [Numbered actionable items]
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
  - <skill-name>: "<Gemini's reason>"
  - <skill-name>: "<Gemini's reason>"

Proceed anyway, or remove them?
```

If the user hasn't selected skills yet, present the selection using screening results to pre-check/uncheck. Always use Gemini's actual screening output — never hardcode which skills are good or poor candidates.

Show estimated cost: ~25 Gemini API calls per skill (4 tasks × 6 judge votes + 1 task generation). Confirm before proceeding.

### 6.5: Run A/B tests (3-condition design)

**Create temp directory:**
```bash
uv run .ai-workspace/scripts/mktmpdir.py deep-eval 2>/dev/null || mkdir -p .tmp/deep-eval
```

**Before starting, read ALL skill files** so you can build the "all-except" prompt for each tested skill. For each skill in the `skills/` directory, read its SKILL.md content and store it.

**For each selected skill:**

**a. Generate 4 tasks** using Gemini:
```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval generate-tasks <SKILL_DIR> [--red-team] --repos-file .tmp/deep-eval/repos.json
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
  [--red-team] \
  --skill-file <SKILL_DIR>/SKILL.md \
  --comparison-type absolute
```

**Judgment 2 — Marginal value (B vs C):** Does the skill add value beyond what OTHER skills already provide?
```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval judge \
  "<TASK_DESCRIPTION>" \
  .tmp/deep-eval/<skill>_task<N>_withskill.txt \
  .tmp/deep-eval/<skill>_task<N>_allexcept.txt \
  [--red-team] \
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
**Mode:** standard / red-team

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
