---
description: "Evaluate your Claude Code setup — skills, commands, CLAUDE.md. Identifies what to keep, remove, merge, and fix."
---

# /evaluate-setup

You are running **the-evaluator** — a health check for Claude Code setups. You will evaluate skills, commands, and CLAUDE.md files, then produce a report with verdicts and recommendations.

## Arguments

`$ARGUMENTS` may include:
- A path (e.g., `~/.claude/skills/`, `skills/python-conventions/`)
- `--preset strict` or `--preset security` (default: recommended)
- `--fix` (auto-fix trivial formatting issues)
- `--deep` (run Layer 3 A/B evaluation — requires API keys)
- `--deep --red-team` (adversarial testing for preventive skills)
- Natural language like "evaluate my setup", "is my python skill any good?"

If no path is given, ask the user what to evaluate or default to scanning the current directory's skills.

## Step 1: Run Layer 1 (Static Analysis)

Find the static analyzer script relative to this command:

```bash
SCRIPT_DIR="$(dirname "$(readlink -f commands/evaluate-setup/command.md 2>/dev/null || echo commands/evaluate-setup/command.md)")"
ANALYZER="$(find "$(dirname "$SCRIPT_DIR")" -path '*/evaluate-setup/src/the_evaluator/cli.py' 2>/dev/null | head -1)"
PROJECT_DIR="$(echo "$ANALYZER" | sed 's|/src/the_evaluator/cli.py||')"
```

Run the analysis:

```bash
uv run --project "$PROJECT_DIR" evaluate-setup scan <PATH> [--preset <PRESET>] [--fix]
```

Read the JSON output. This gives you per-skill diagnostics with rule IDs, severities, token counts, and fixable issues.

If `--fix` was requested, report what was auto-fixed before proceeding.

## Step 2: Read Actual Files (Layer 2 Preparation)

Read the actual content of:
1. Every skill file (SKILL.md) in the scan path
2. Every command file (command.md) found nearby
3. The user's CLAUDE.md files (project and user level)

You need the actual content — not just the Layer 1 JSON — to evaluate quality, redundancy, and content.

## Step 3: Evaluate Each Skill (Layer 2)

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

## Step 4: Setup-Wide Recommendations

After grading all skills individually, evaluate the **whole setup**:

- **Merge candidates**: Skills covering related topics that would be stronger combined
- **Skill → command conversion**: Skills describing explicit workflows that should be user-triggered commands
- **Command → skill conversion**: Commands describing general behavior that should auto-trigger
- **CLAUDE.md review**: Is it too long? Does it duplicate skills? Does it conflict? Is it well-structured?
- **Overlapping triggers**: Groups of skills whose descriptions might cause multiple to load unnecessarily
- **Coverage gaps**: Obvious missing areas based on what's present
- **Total context budget**: Sum all skills + CLAUDE.md tokens, warn if >20% of context window

## Step 5: Produce the Report

Output the report in this format:

```
## Static Analysis (Layer 1)
  Preset: <preset> | <N> skills found | <tokens> tokens total (<pct>% of context budget)
  <errors> errors | <warnings> warnings | <info> info
  <fixable> fixable with --fix

## Per-Skill Review (Layer 2)
  [Per-skill rubric output as shown above, one per skill]

## Setup-Wide Recommendations
  [Bullet points for each recommendation]

## Summary
  Keep:    N skills (total: X tokens)
  Remove:  N skills (total: X tokens)  <- potential savings
  Review:  N skills
  Fixable: N issues (run with --fix to auto-correct)
```

## Step 6: Deep Evaluation (Layer 3 — only if --deep was passed)

If `--deep` was requested:

1. Check that `ANTHROPIC_API_KEY` and `GEMINI_API_KEY` are available in the environment
2. Show estimated cost: 46 API calls per skill × number of skills to test
3. Ask the user for confirmation before proceeding
4. Run `deep_eval.py`:

```bash
uv run --project "$PROJECT_DIR" --extra deep python -m the_evaluator.deep_eval <PATH> [--red-team] [--model sonnet]
```

5. Read the JSON results
6. For each skill tested, add A/B evidence to the report:
   - Standard mode: wins/ties/losses, confidence levels, overall verdict (HELPS/NO IMPACT/HURTS)
   - Red-team mode: held/broke/partial, red-team score, overall verdict (STRONG/WEAK/FRAGILE)

If `--deep` was NOT requested but some skills scored 2 stars or below:
- Suggest: "3 skills scored poorly. Want me to run deep evaluation on those? Requires ANTHROPIC_API_KEY and GEMINI_API_KEY in your .env."
