---
description: "Get a brutally honest review of your project from the perspective of a principal AI engineer. Covers architecture, code quality, skills/commands/hooks setup, redundancy, gaps, and concrete improvement suggestions."
---

# AI Engineer Review

Act as a **principal AI engineer** with 15+ years of experience reviewing this project. Be honest, specific, and critical — the goal is to find real problems, not to be encouraging or mean.

## Instructions

### Step 1: Understand the Project

Read the project's key files to understand what it does and how it's built:

```bash
# What is this project?
cat README.md 2>/dev/null | head -50
cat CLAUDE.md 2>/dev/null | head -50

# Structure
find . -maxdepth 2 -type f -name "*.py" -o -name "*.md" -o -name "*.yaml" | head -40

# Recent activity
git log --oneline -15
git diff --stat HEAD~5..HEAD 2>/dev/null

# Tests
ls tests/ 2>/dev/null
```

### Step 2: Review Architecture

Assess the project's architecture and design decisions:

- **Is the structure logical?** Are files in the right places? Are responsibilities clear?
- **Is it modular?** Can you change one part without breaking others?
- **Is it over-engineered or under-engineered?** Too many abstractions? Not enough?
- **Are there dead ends?** Features started but not finished, orphaned files, unused code?
- **Data flow** — is it clear how data moves through the system?

### Step 3: Review Code Quality

For the main source files, check:

- **Duplication** — same logic in multiple places
- **Complexity** — functions doing too many things, deep nesting, long files
- **Error handling** — swallowed errors, bare excepts, missing validation
- **Naming** — unclear variable/function names, inconsistent conventions
- **Testing** — coverage gaps, untested critical paths, brittle tests
- **Security** — hardcoded secrets, injection risks, PII handling
- **Separation of concerns** — each file/module has one clear responsibility with a well-defined interface
- **Coupling** — can units be understood and tested independently? Can you change internals without breaking consumers?
- **SOLID principles** — proper abstractions, dependency direction, interface segregation

### Step 4: Review AI Workspace Setup (if applicable)

If this is a Claude Code workspace with skills/commands/hooks:

- **Read every SKILL.md** in `skills/` — are they useful or bloat?
- **Read every command.md** in `commands/` — are they distinct or redundant?
- **Read `.claude/settings.json`** — are hooks well-designed?
- **Check for overlap** — multiple items doing the same thing
- **Check for gaps** — important patterns missing
- **Are skills teaching Claude things it already knows?** (generic tutorials = waste)
- **Are skills teaching team-specific knowledge?** (conventions, workflows = value)

### Step 5: Plan Alignment Check (SKIP if no specs/plans exist)

Check for design specs or implementation plans in `docs/`, `.tmp/`, or similar. If none exist, skip this step entirely and move to Step 6.

If specs/plans are found:

- **Compare implementation against the plan** — did the code deliver what was specified?
- **Identify deviations** — are they justified improvements or problematic departures?
- **Check for missing pieces** — requirements specified but not implemented
- **Check for scope creep** — features built that weren't in any plan
- **Verify integration** — does the implementation integrate well with existing systems?

Categorize findings as:
- **Critical** — must fix, blocks production readiness
- **Important** — should fix, causes maintenance burden or risk
- **Suggestions** — nice to have, improves quality but not urgent

### Step 6: Produce the Review

Format the review as:

```
PRINCIPAL AI ENGINEER REVIEW
=============================
Project: [name]
Date: [today]
Verdict: [STRONG / SOLID / NEEDS WORK / CONCERNING]

WHAT'S GOOD:
  Things that are genuinely well-done. Be specific — name files, patterns,
  decisions that show good engineering judgment.

WHAT'S PROBLEMATIC:
  Things that would concern me in a production codebase or a team setting.
  For each issue:
  - WHAT: the specific problem
  - WHY IT MATTERS: the real-world impact
  - FIX: concrete suggestion (not "improve this" — say exactly what to do)

ARCHITECTURE ASSESSMENT:
  [2-3 sentences on the overall design]

CODE QUALITY SCORE: [A/B/C/D/F]
  - Readability: [score]
  - Maintainability: [score]
  - Test coverage: [score]
  - Security: [score]

REDUNDANCY CHECK:
  [List any items that duplicate each other]

PLAN ALIGNMENT (only if specs/plans were found — omit this section otherwise):
  [How well does the implementation match the design?
   Deviations found — justified or problematic?
   Missing requirements, scope creep, integration issues]

MISSING:
  [Things that should exist but don't]

TOP 3 IMPROVEMENTS (in priority order):
  1. [Most impactful change with specific instructions]
  2. [Second most impactful]
  3. [Third most impactful]

THINGS I WOULDN'T CHANGE:
  [Decisions that are correct — acknowledge what's working so the team
  doesn't accidentally break good patterns while fixing problems]
```

## Important

- **Be brutally honest.** If something is bad, say it's bad. Don't hedge.
- **Be specific.** "The code needs improvement" is useless. "Function X in file Y is 120 lines with 6 nested if-statements" is useful.
- **Distinguish nitpicks from real problems.** Don't give equal weight to a missing docstring and a security vulnerability.
- **Acknowledge good decisions.** A review that only criticizes teaches nothing — call out what's working and WHY it's working so the team preserves those patterns.
- **Give actionable fixes.** Every problem should have a concrete "do this instead" suggestion.
- **Use parallel agents** (Explore, general-purpose) to read multiple files simultaneously for a thorough review.

## Arguments

$ARGUMENTS can specify:
- A specific area: `/ai-engineer-review architecture`, `/ai-engineer-review security`, `/ai-engineer-review skills`
- A specific repo: `/ai-engineer-review repositories/my-project`
- Default: review the entire workspace
