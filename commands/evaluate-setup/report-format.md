## Step 5: Produce the Report

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
Reviewed <N> skills, <M> commands, CLAUDE.md. Total: <tokens> tokens (<pct>%.

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
