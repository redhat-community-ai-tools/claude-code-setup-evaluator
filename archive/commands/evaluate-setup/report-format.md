## Step 5: Produce the Report

### Step 5a: Full Review

If the user chose **terminal output**, print the full review directly. If they chose **file output**, write it to `evaluation-results/evaluate-setup-YYYY-MM-DD-HHMM.md` (create the directory if needed; if the file exists, append a counter: `-2`, `-3`, etc.) and tell the user where to find it.

Full review format:

```
## How This Evaluation Works

This report evaluates the Claude Code setup across four dimensions:

- **Readiness** — Can each component load and function?
- **Correctness** — Does each component work as intended and safely?
- **Redundancy** — Is each component adding value beyond defaults and other components?
- **Compliance** — Does each component follow Anthropic's published best practices?

Two layers produce the evidence:

**Layer 1 (Static Analysis)** runs deterministically — no AI involved. A Python
tool scans every file and checks mechanical rules: does the file exist? Does the
YAML parse? Are referenced files real? Are there prompt injection patterns?
Credential references? Dangerous commands? Same input always produces same output.

**Layer 2 (Rubric Scoring)** uses Claude to read every file and score it on
weighted rubric dimensions. This is where human-like judgment happens: is this
skill teaching something Claude doesn't already know? Is the description good
enough to trigger at the right time?

---

## Layer 1 Rules Reference

Each item below includes a Layer 1 checklist showing which Python rules passed
or failed. Here is what each rule checks:

### Skills (9 rules)
- **SKILL.md exists** — the skill directory contains a SKILL.md file
- **Frontmatter valid** — YAML frontmatter parses correctly, name matches directory
- **Description required** — description field exists and is not empty
- **Description quality** — description uses third-person, includes "use when" context, reasonable length
- **Token budget** — SKILL.md is under the token limit and under 500 lines
- **Broken references** — all file links and references point to files that exist
- **Duplicate detection** — no other skill is >85% similar (TF-IDF cosine similarity)
- **No prompt injection** — no patterns that could hijack Claude's behavior (17 regex patterns)
- **No credential access** — no references to ~/.ssh, ~/.aws, $API_KEY, sudo, chmod 777

### Commands (6 rules)
- **Description required** — description field exists for the UI menu
- **Script exists** — referenced script files actually exist
- **Skill overlap** — no command is >60% similar to a skill body (cross-type duplication)
- **Duplicate detection** — no other command is >85% similar (TF-IDF cosine similarity)
- **No prompt injection** — same 17-pattern check as skills
- **No credential access** — same credential/dangerous command check as skills

### CLAUDE.md (2 rules)
- **File exists** — CLAUDE.md is present in the project
- **Skill duplication** — no section is >60% similar to a skill body (wasted tokens)

### Hooks (1 rule)
- **Valid structure** — commands exist, no dangerous patterns (rm -rf, git push --force, curl|bash)

### Agents (6 rules)
- **Description required** — description field exists and is not empty
- **Referenced skills exist** — every skill listed in frontmatter has a matching SKILL.md
- **DisallowedTools format** — entries match ToolName or ToolName(pattern) format
- **Constraint-body match** — body constraints ("cannot push") are backed by disallowedTools
- **No prompt injection** — same 17-pattern check
- **No credential access** — same credential check

---

## Inventory

| Type | Count | Total Tokens | Errors | Warnings |
|------|-------|-------------|--------|----------|
| Skills | [N] | [N] | [N] | [N] |
| Commands | [N] | [N] | [N] | [N] |
| CLAUDE.md | [N] | [N] | [N] | [N] |
| Hooks | [N] | [N] | [N] | [N] |
| Agents | [N or 0] | [N] | [N] | [N] |

## Skills

### skill-name                              ★★★★    KEEP
  Tokens: [SKILL.md tokens] (+[reference file tokens] in reference files)
  Reference files: [list or "none"]
  Guidelines: [yes/no]

  Layer 1:
    [For each of the 9 skill rules, show ✓ if passed, ⚠ with message if warning, ✗ with message if error]
    [Example when all pass:]
    ✓ SKILL.md exists     ✓ Frontmatter valid      ✓ Description required
    ✓ Description quality ✓ Token budget (663)      ✓ No broken references
    ✓ No duplicates       ✓ No prompt injection     ✓ No credential access

    [Example with issues:]
    ✓ SKILL.md exists     ✓ Frontmatter valid      ✓ Description required
    ⚠ Description quality — lacks "Use when" context
    ✓ Token budget (1,485)
    ✗ Prompt injection — line 49 contains a word the scanner flagged, but it's normal accessibility terminology — not a real risk
    ✓ No broken references ✓ No duplicates          ✓ No credential access

    [When a Layer 1 rule flags something, explain it in plain language.
    Don't use jargon like "WCAG SC 3.3.7" or "false positive" — just say
    what the scanner found and whether it's a real problem or not.]

  Rubric:
    **Readiness:**    [PASS/FAIL] — [one sentence from Layer 1 results]
    **Correctness:**  [PASS/FAIL] — [one sentence]
    **Redundancy:**   [score/5] — [one sentence: what's unique vs what Claude already knows]
    **Compliance:**   [overall score — weighted average of the 4 sub-scores below]
      Specificity: [score/5]  [one sentence justification]
      Trigger:     [score/5]  [one sentence justification]
      Token eff:   [score/5]  [one sentence justification]
      Content:     [score/5]  [one sentence justification]

  + What's good
  ! What could improve
  x What's broken

[Repeat for each skill]

## Commands

### command-name                            ★★★★    KEEP
  Tokens: [tokens]

  Layer 1:
    ✓ Description required  ✓ Script exists
    ✓ No prompt injection   ✓ No credential access

  Rubric:
    Readiness: PASS | Correctness: PASS | Redundancy: [unique/redundant] | Compliance: [score]

[For commands with issues, use the full format with per-dimension details.
For clean commands, the compact format above is fine.]

[Repeat for each command]

## Hooks

For each hook entry:

  Layer 1:
    [✓/⚠/✗ Valid structure — result]

  Readiness: [command exists, script exists]
  Correctness: [no dangerous patterns, correct mechanism]

## CLAUDE.md

### CLAUDE.md                               ★★★★    KEEP
  Tokens: [tokens] | Lines: [lines]

  Layer 1:
    ✓ File exists
    ✓ No skill duplication

  Rubric:
    **Readiness:** PASS
    **Correctness:** PASS — no conflicts with skills
    **Redundancy:** [signal-to-noise score] — [generic advice?]
    **Compliance:**
      Conciseness:      [score/5]  [one sentence]
      Signal-to-noise:  [score/5]  [one sentence]
      Skill separation: [score/5]  [one sentence]
      Structure:        [score/5]  [one sentence]
      Conflict-free:    [score/5]  [one sentence]

## Agents (if found)

### agent-name                              ★★★★    KEEP
  Tokens: [tokens]

  Layer 1:
    ✓ Description required     ✓ Referenced skills exist
    ✓ DisallowedTools format   ✓ Constraint-body match
    ✓ No prompt injection      ✓ No credential access

  Rubric:
    [Same 4-dimension format as skills, with agent-specific dimensions]

## Cross-Type Optimization

Answer each of the 21 checks explicitly. Do not skip any.

### Transformations
  1. Skill → Hook:               [YES/NO] — [one-line explanation]
  2. Skill → Command:            [YES/NO] — [one-line explanation]
  3. Command → Skill:            [YES/NO] — [one-line explanation]
  4. Skill content → CLAUDE.md:  [YES/NO] — [one-line explanation]
  5. CLAUDE.md → Skill:          [YES/NO] — [one-line explanation]
  6. CLAUDE.md → Hook:           [YES/NO] — [one-line explanation]
  7. Agent ↔ Skill consistency:  [YES/NO] — [one-line explanation]
  8. Agent ↔ Agent overlap:      [YES/NO] — [one-line explanation]
  9. Agent ↔ CLAUDE.md:          [YES/NO] — [one-line explanation]
  10. Skill structure optimization: [YES/NO] — [which skills and why]
  11. Guidelines extraction:      [YES/NO] — [which skills and why]

### Setup-Wide
  12. Merge candidates:           [YES/NO] — [which skills or "none"]
  13. Overlapping triggers:       [YES/NO] — [which skills or "none"]
  14. Coverage gaps:              [YES/NO] — [what's missing or "none"]
  15. Total context budget:       [tokens] ([pct]% of context) — [OK/WARNING]
  16. Redundancy across types:    [YES/NO] — [what's duplicated or "none"]
  17. Conflicts across types:     [YES/NO] — [what conflicts or "none"]
  18. Command shadows built-in:   [YES/NO] — [which commands shadow built-ins or "none"]

### Behavioral Patterns
  19. Mandate stacking:           [YES/NO] — [how many mandates, acceptable?]
  20. Autonomy erosion:           [YES/NO] — [which skills or "none"]
  21. Broad trigger collision:    [YES/NO] — [which skills or "none"]

## Suggestions
  [Numbered actionable items]
```

### Step 5b: Terminal Summary (ALWAYS printed, regardless of output format)

This is the last thing the user sees. Keep it short — 10-15 lines max. It tells the user the bottom line.

```
## Evaluation Summary

<Overall verdict — one sentence. E.g., "Your setup is solid" or "Found 2 issues that need attention.">
Reviewed <N> skills, <M> commands, CLAUDE.md, <H> hooks. Total: <tokens> tokens (<pct>%).

Cross-type: <count>/20 checks flagged issues.

Suggestions (say "do 1", "do 2", "skip 3" to act on them):
  1. <one-line suggestion>
  2. <one-line suggestion>
  3. <one-line suggestion>

Full review: <"printed above" or "saved to evaluation-results/evaluate-setup-YYYY-MM-DD-HHMM.md">
```

**Numbering rules:**
- Every suggestion gets a number, starting from 1
- Each number is one actionable item Claude can execute if the user says "do N"
- Keep each suggestion to one line — the full explanation is in the detailed review
- If the setup is healthy, it's fine to have just 1-2 suggestions or even zero. Don't pad.

**Key principle:** If nothing significant needs to change, say "your setup is solid" and list only the minor items. Don't pad the summary with nice-to-have suggestions. The user should be able to read the summary in 10 seconds and know: do I need to act or not?
