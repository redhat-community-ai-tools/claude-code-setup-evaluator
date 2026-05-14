# the-evaluator

**Status:** v2.0 built · two-command architecture
**Author:** Benjamin Kapner + design review with Claude
**Last updated:** May 2026
**Changes from v2.0:** Updated spec to match code reality — 21 rules across 5 file types (added command security rules, agent rules), removed phantom CLI flags (--commands/--claude-md/--hooks/--all), updated rule IDs, presets, JSON output format, Layer 3 judge algorithm, and file naming conventions.
**Changes from v1.4:** Split into two separate commands: `/evaluate-setup` (L1+L2 on entire setup) and `/evaluate-skill` (L1+L2+L3 on a single skill). evaluate-setup no longer asks scope — it always evaluates everything. evaluate-skill runs all 3 layers on one skill: static analysis, contextual rubric scoring (individual + in context of all other skills), and A/B testing. Layer 3 protocol updated: agents save their own output files, allexcept prompts pre-built before agent dispatch, skills processed sequentially.
**Changes from v1.3:** Layer 3 A/B testing now generates 3 behavioral repo-based tasks instead of 4. Task generation prompt rewritten to create situations where the skill's rules naturally apply.
**Changes from v1.2:** Split command.md into thin command + reference files. Added Layer 2 autonomy analysis, command size thresholds, and behavioral pattern checks.
**Changes from v1.1:** Removed auto-fix. Added Layer 1 rules for commands, CLAUDE.md, and hooks. Added interactive Step 0, cross-type optimization, numbered suggestions. Added hard rules.
**Changes from v1.0:** Rule engine architecture, config presets, inline suppression, structured rubric scoring, red-team mode, repeat-and-vote judge reliability.

---

## Quick Overview

the-evaluator is two commands for two different jobs:

**`/evaluate-setup`** — Health check for your entire Claude Code setup. Evaluates all skills, commands, CLAUDE.md, and hooks together. Runs Layer 1 (static analysis) and Layer 2 (rubric scoring with cross-type optimization). Tells you what to keep, remove, merge, and fix. Always evaluates everything — no scope selection needed.

**`/evaluate-skill`** — Deep evaluation of a single skill. Runs all 3 layers on one skill: Layer 1 (rules), Layer 2 (contextual rubric scoring — individually and in context of the whole setup), and Layer 3 (A/B testing — does the skill actually change Claude's behavior?). Use this to validate whether a specific skill earns its place.

Both commands use the same three layers, but at different scope:

**Layer 1 — Rules (rule engine, no AI).** A pluggable rule engine scans files and runs mechanical checks across 5 file types (skills, commands, CLAUDE.md, hooks, agents) with 21 rules: token counting, duplicate detection, broken references, format validation, description quality, security scanning (prompt injection, credential exposure). Configured via presets (`recommended`, `strict`, `security`). Outputs JSON with per-rule diagnostics.

**Layer 2 — Prompt (Claude in your session).** Claude reads files and evaluates against structured rubrics. In `/evaluate-setup`: scores every skill, command, CLAUDE.md, and hook, then does cross-type optimization (should this skill be a hook? does CLAUDE.md duplicate a skill?). In `/evaluate-skill`: scores one skill individually AND in context of all other setup components (overlap, conflicts, type appropriateness).

**Layer 3 — A/B Testing (requires `GOOGLE_API_KEY`).** Only runs in `/evaluate-skill`. Gemini generates 3 repo-based tasks, Claude runs each under 2 conditions (all-except, with-skill), Gemini judges which performed better. Tests marginal value: does the skill add value beyond what other skills already provide? Tasks with poor test quality are automatically excluded from the verdict.

Both commands are read-only — they never modify your files. They produce numbered suggestions the user can act on selectively.

---

## 1. What is this?

People install skills into Claude Code — instruction files that tell Claude how to behave. "Handle Python errors this way." "Format code like that." "Always write tests first."

Over time, people accumulate dozens of these. Some are great. Some are duplicates of each other. Some tell Claude to do things it already does by default. Some reference files that don't exist anymore. And every single one gets loaded into Claude's context window when it's relevant — burning tokens and, when the instructions are low-quality, actually making Claude perform worse.

**the-evaluator is a health check for your Claude Code setup.** You run one command inside Claude Code, it reviews your skills, commands, and CLAUDE.md, and tells you what to keep, what to delete, what to merge, and what to fix.

It runs entirely inside Claude Code. No separate tool to install. No package manager. You clone a repo and you're done.

---

## 2. The problem in detail

### 2.1 What goes wrong with skill accumulation

- CLAUDE.md files grow 3-5x larger than recommended
- Skills duplicate each other ("pdf-wizard" and "pdf-creator" doing the same thing)
- Skills duplicate Claude's baseline behavior ("be helpful and write clean code" — Claude already does this)
- Skills with vague descriptions that Claude Code can't figure out when to activate
- Broken skills that reference files that were moved or deleted
- Context rot — the more low-signal instructions you load, the worse Claude performs on actual tasks

This is documented publicly (GitHub issue #29971, blog posts, Anthropic's own guidance). The pain is real and widespread.

### 2.2 What already exists

- **Anthropic's skill-creator (v2.0)** — evaluates one skill at a time via A/B comparison. Excellent for iterating on a single skill. Doesn't audit whole setups.
- **Claude Skill Quality Benchmarker** (community MCP server) — does static analysis on skill files. No dynamic evaluation.
- **LangChain's evaluation methodology** / **MLflow's genai.evaluate** — evaluation frameworks, not products. Require manual setup.

### 2.3 What's missing

No existing tool:
- Audits a **whole setup** at once (not one skill at a time)
- Evaluates skills against **Claude Code's own best practices** (the skill spec, frontmatter requirements, Claude Search Optimization)
- Tells a user **which skills to keep, review, or remove** — with evidence
- Works **inside Claude Code** with no separate installation

That's what the-evaluator does.

---

## 3. How it works

### 3.1 Three layers

The system has three layers. The first two always run. The third is optional.

**Layer 1: The robot inspector** (rule engine, no AI)

A pluggable rule engine scans your skill files and runs mechanical checks. Each check is a self-contained rule — its own file, its own metadata, registered in a central registry. The engine orchestrates: parse each skill → load config (which rules to run, at what severity) → run enabled rules → collect diagnostics → output JSON.

Out-of-the-box rules check (21 rules across 5 file types):
- **Skills (9 rules):** Does SKILL.md exist? Is frontmatter valid? Is the description present, high-quality, and use-case aware? Is the token budget respected? Do referenced files exist? Are any two skills near-duplicates? Are there prompt injection patterns or credential references?
- **Commands (4 rules):** Is the description present? Do referenced scripts exist? Prompt injection and credential access checks.
- **CLAUDE.md (2 rules):** Does the file exist? Does it duplicate content from skills?
- **Hooks (1 rule):** Valid structure, no dangerous patterns, scripts exist.
- **Agents (6 rules):** Is the description present? Do referenced skills exist? Is the disallowedTools format valid? Do body constraints match disallowedTools? Prompt injection and credential access checks.

Users configure which rules run via presets (`recommended`, `strict`, `security`) or per-rule overrides in `.evaluator.yaml`. Skills can suppress specific rules with inline comments (`<!-- evaluator-ignore: rule-id -->`).

This catches the obvious stuff — broken files, duplicates, missing fields, security issues. It outputs structured JSON with per-rule diagnostics that Layer 2 uses.

**Layer 2: Claude reviews your setup** (current session)

Claude — the one already running in your session — reads the Layer 1 JSON AND reads each actual skill file, command file, and CLAUDE.md. Then it evaluates the whole setup against a structured rubric with 5 scored dimensions:

- **Specificity** — Are the instructions specific ("always use `raise from` for exception chaining") or vague ("handle errors properly")?
- **Redundancy** — Is this skill telling Claude something it doesn't already know by default?
- **Trigger quality** — Is the description specific enough that Claude Code will activate it at the right time?
- **Token efficiency** — Is it bloated — could the same value be delivered in half the tokens?
- **Content quality** — Does it include concrete examples? Is it well-structured? Do referenced files exist?

Each dimension gets a 1-5 score with a one-sentence justification. The overall star rating is a weighted average. Beyond per-skill scoring, Claude also evaluates setup-wide concerns: should any skills be merged? Should any skill be a command instead (or vice versa)? Does CLAUDE.md duplicate or conflict with skills?

Uses the Claude session already running.

**Layer 3: The science experiment** (optional, requires `GOOGLE_API_KEY`)

For users who want empirical proof, not just an expert opinion. This requires `GOOGLE_API_KEY` in your `.env` file (no Anthropic API key needed — Claude runs tasks via subagents in the current session). The engine automatically selects the right testing mode per skill: **standard** for skills that teach patterns, **red-team** (adversarial) for preventive skills that contain negation patterns ("never", "do not", "must not").

**Before testing: skill screening.** Gemini evaluates each skill and decides whether it can be meaningfully A/B tested. Skills that require MCP connections, define multi-step interactive workflows, or orchestrate external tools are flagged as not testable. The screening output is saved to `.tmp/deep-eval/skill-screening.json`.

**Standard mode** — tests whether a skill makes Claude's output better:

1. **Gemini writes 3 tasks.** It reads the skill's description and content, then creates 3 repo-based tasks (code review, code writing, debugging) that use the user's actual repositories. Tasks create situations where the skill's rules would naturally apply — not knowledge questions that ask the agent to recite the rules. The task generator matches repo language to the skill's target language (e.g., Python skill → Python repos). Task definitions are saved to `.tmp/deep-eval/<skill>_tasks.json`.

2. **Claude takes the test twice.** For each task, two subagents are spawned: one with all skills except the tested one (all-except), one with the tested skill loaded (with-skill). Both have read-only access to the user's repositories. All 6 subagents per skill run in parallel. Responses are saved to `.tmp/deep-eval/<skill>_task<N>_allexcept.txt` and `_withskill.txt`.

3. **Quality screening.** Before judging, responses are checked for completeness. Tasks where both responses are truncated or unusable are skipped — no judge call is made. This saves API calls on tests that can't produce meaningful signal.

4. **Gemini grades with blind dimension scoring.** For each valid pair, Gemini receives both responses in randomized order (blinded). The judge scores each response independently on 5 dimensions (1-5 scale): accuracy, specificity, actionability, completeness, and response_posture. The winner is determined by total score difference: >=3 = clear winner, 1-2 = marginal winner, 0 = tie. Each pair gets 3 blind votes (repeat-and-vote), majority wins. Confidence: HIGH if unanimous, LOW if 2-1 split. Tasks where the judge reports poor test quality are excluded from the verdict.

5. **The verdict** (based on good-quality tasks only). KEEP (wins > losses and wins > ties), NO IMPACT (mostly ties — skill is redundant), HURTS (losses > wins).

**Red-team mode** — tests whether preventive skills actually prevent bad behavior:

1. **Gemini writes 3 adversarial tasks.** Instead of helpful tasks, Gemini generates repo-based tasks designed to trick Claude into violating the skill's rules — direct contradictions, social engineering attempts, and subtle edge cases.

2. **Claude takes the test twice.** Same subagent approach — all-except and with-skill, all 6 subagents run in parallel.

3. **Gemini judges resistance.** Verdict per pair: HELD / BROKE / PARTIAL.

4. **The verdict.** STRONG (≥80% held), WEAK (≥50% held), FRAGILE (<50% held).

### 3.2 How the layers flow together

**`/evaluate-setup` flow:**

```
User types: /evaluate-setup
Step 0: Ask output format (terminal/file)

  +----------------------------------------------+
  |  Layer 1: Rule engine                        |
  |  Scan ALL skills, commands, CLAUDE.md, hooks |
  +---------------------+------------------------+
                        | JSON output
                        v
  +----------------------------------------------+
  |  Layer 2: Claude review with rubric          |
  |  Score each item on rubric dimensions        |
  |  Cross-type optimization analysis            |
  |  Setup-wide recommendations                  |
  +---------------------+------------------------+
                        |
                   Done. Show report.
```

**`/evaluate-skill` flow:**

```
User types: /evaluate-skill [skill-name]
Step 1: Select skill (if not in arguments)
Step 2: Ask output format (terminal/file)

  +----------------------------------------------+
  |  Layer 1: Rule engine on this skill          |
  +---------------------+------------------------+
                        |
  +----------------------------------------------+
  |  Layer 2: Individual + contextual scoring    |
  |  Score on rubric dimensions                  |
  |  Check overlap with other skills             |
  |  Check conflicts with CLAUDE.md              |
  +---------------------+------------------------+
                        |
              Skill testable? (Gemini screens)
                 /            \
               no              yes
               |                |
          Done. Show     Generate 3 tasks.
          L1+L2 report.  Spawn 6 agents.
                         Run 3 judge calls.
                                |
                  +-------------------------------+
                  | Layer 3: A/B testing           |
                  |   2 conditions × 3 tasks       |
                  |   Marginal verdicts only        |
                  +-------------------------------+
                                |
                         Combined L1+L2+L3 report.
```

### 3.3 What this does NOT test

Layer 3 tests: "Does having this skill's text in Claude's context make the output better?"

Layer 3 does NOT test: "Does Claude Code correctly decide when to load this skill?" That would require running real Claude Code in subprocess mode, which is a v2 feature. This limitation is stated clearly in the output so users aren't misled.

Layer 2 partially compensates — Claude can review the skill's description and tell you whether it's likely to trigger correctly, even without empirically testing it.

---

## 4. How the user uses it

### 4.1 The commands

Two separate commands for two different jobs:

```
/evaluate-setup [--preset recommended|strict|security]
```

Evaluates the entire setup — all skills, commands, CLAUDE.md, and hooks. Asks only where to put the report (terminal or file), then runs L1+L2.

```
/evaluate-skill [skill-name or path]
```

Deep-evaluates a single skill with all 3 layers. If no skill is specified, lists available skills and asks which one to test. Runs L1 (rules) + L2 (contextual scoring) + L3 (A/B testing).

```
/evaluate-setup                        # Evaluate entire setup
/evaluate-setup --preset strict        # Stricter rules
/evaluate-setup --preset security      # Security-only audit

/evaluate-skill python-conventions     # Deep-evaluate one skill
/evaluate-skill skills/accessibility/  # By path
```

### 4.2 What the user sees

Each skill gets a star rating (1-5) and a verdict:

- **KEEP** — well-written, specific, provides value beyond Claude's baseline
- **REMOVE (redundant)** — duplicates Claude's default behavior or another skill
- **REMOVE (broken)** — references missing files, no description, can't trigger
- **REVIEW** — has value but needs improvement (rewrite, trim, or split)

Each verdict comes with:
- The star rating and why
- How many tokens the skill costs
- Specific issues found
- Concrete recommendations ("rewrite description to start with 'Use when...'", "merge with pdf-wizard", "trim from 5,200 to ~1,500 tokens")

For `/evaluate-skill`, the verdict also includes Layer 3 A/B results — win/loss/tie counts with redundancy signal and confidence level.

### 4.3 Example output

```
/evaluate-setup ~/.claude/skills/

Analyzing setup at ~/.claude/skills/ ...

## Static Analysis (Layer 1)
  Preset: recommended | 14 skills found | 34,200 tokens total (17% of context budget)
  4 errors | 6 warnings | 2 info
  1 duplicate pair detected
  3 skills missing descriptions
  1 broken file reference

## Per-Skill Review (Layer 2)

### python-error-handling                    ****    KEEP
  Tokens: 663

  Rubric:
    Specificity:      5/5  Concrete rules: raise from, exception hierarchies, context managers
    Redundancy:       4/5  One rule ("always log errors") overlaps Claude's default behavior
    Trigger quality:  5/5  Description targets Python error handling tasks precisely
    Token efficiency: 5/5  663 tokens, high value density
    Content quality:  4/5  Well-structured but could add code examples

  + Actionable rules that change Claude's behavior
  + Clear trigger scope
  ! Removing the "always log errors" rule saves 80 tokens with no quality loss

### be-helpful                               *       REMOVE (redundant)
  Tokens: 168

  Rubric:
    Specificity:      1/5  Entirely vague platitudes, no actionable instructions
    Redundancy:       1/5  Every instruction is Claude's default behavior
    Trigger quality:  1/5  No description — Claude can't decide when to activate
    Token efficiency: 1/5  168 tokens of zero value
    Content quality:  1/5  References scripts/helper.sh which doesn't exist

  x No description — Claude can't decide when to activate
  x "Be helpful and thorough" — Claude already does this by default
  x Broken file reference: scripts/helper.sh

### pdf-wizard                               ****    KEEP
  Tokens: 3,800

  Rubric:
    Specificity:      5/5  Detailed PDF manipulation steps for specific libraries
    Redundancy:       5/5  Specialized domain knowledge Claude doesn't have by default
    Trigger quality:  4/5  Good but overlaps with pdf-creator's trigger
    Token efficiency: 3/5  3,800 tokens — check for content overlap with pdf-creator
    Content quality:  5/5  Includes examples, edge cases, and library-specific guidance

  + Specific PDF manipulation instructions
  ! 91% similar to pdf-creator — keep one, remove the other

### react-helper                             **      REVIEW
  Tokens: 5,200

  Rubric:
    Specificity:      3/5  Some specific rules, but mixed with generic advice
    Redundancy:       3/5  React basics are common knowledge, advanced patterns add value
    Trigger quality:  1/5  "when working with frontend" triggers on everything
    Token efficiency: 1/5  5,200 tokens is excessive — most skills work under 1,500
    Content quality:  2/5  Mixes React, CSS, testing, deployment without clear structure

  ! Should be split into 3-4 focused skills (react, css, testing, deployment)
  x Trigger condition too broad: "when working with frontend"

## Evaluation Summary

Found 6 skills that need attention out of 14 reviewed.
Total context budget: 34,200 tokens (17%).

Suggestions (say "do 1", "do 2", "skip 3" to act on them):
  1. Remove "be-helpful" skill — 100% redundant with Claude's default behavior
  2. Remove "pdf-creator" — 91% duplicate of pdf-wizard
  3. Merge pdf-wizard + pdf-creator into one skill if both have unique parts
  4. Split react-helper into 3-4 focused skills (react, css, testing, deployment)
  5. Convert "deploy-checklist" from skill to command (user-triggered workflow)
  6. Remove duplicated testing rules from CLAUDE.md (already in python-conventions skill)

Full review: saved to evaluate-setup-report.md
```

### 4.4 Safety

- **Read-only.** The tool never modifies, moves, or deletes any files. It produces numbered suggestions — the user decides which to act on by saying "do 1, do 2, skip 3".
- **Interactive.** Before running, the tool asks what to evaluate and where to put the output. No surprises.
- **Confirmation.** Deep evaluation asks for confirmation before making any API calls. The tool shows the estimated number of calls and approximate cost before proceeding.
- **Privacy.** No data leaves your machine except API calls to Google/Gemini (Layer 3 judging only). Layers 1+2 are completely local. Layer 3 subagents run locally in your Claude Code session.

---

## 5. Technical details

### 5.1 File structure

```
the-evaluator/
  commands/
    evaluate-setup/
      command.md                   # L1+L2: command prompt with rubrics + cross-type optimization
      report-format.md             # Report structure and output templates (loaded on demand)
    evaluate-skill/
      command.md                   # L1+L2+L3: single-skill deep evaluation command
      layer3-protocol.md           # Layer 3: A/B test execution protocol (loaded on demand)
  docs/
    spec.md                        # This file — full specification
    HOW-EVALUATE-SETUP-WORKS.md    # Plain-language architecture doc for /evaluate-setup
    HOW-EVALUATE-SKILL-WORKS.md    # Plain-language architecture doc for /evaluate-skill
  tests/
    test_command_prompts.py        # Structural validation tests for command.md and SKILL.md files
    test_workspace_scripts.py      # Workspace infrastructure tests
  scripts/
    evaluate-setup/
      pyproject.toml               # Package config + dependencies
      src/the_evaluator/
        cli.py                     # CLI entry point (scan subcommand with --preset/--config/--target)
        deep_eval.py               # Layer 3: A/B + red-team evaluation (screen-skills, generate-tasks, validate-tasks, judge)
        engine/                    # Rule engine core
          types.py                 # Dataclasses + TargetType enum (skill/command/claude_md/hooks/agent)
          registry.py              # Rule registry (register, get_all, get_by_category)
          engine.py                # Parsers + lint functions for all 5 file types
          suppression.py           # Inline suppression comment parser
        rules/                     # Rule implementations (one file per rule)
          __init__.py              # register_all_rules() — registers all 21 rules
          structural/
            skill_md_exists.py     # Does SKILL.md exist in the directory?
          frontmatter/
            description_required.py # Is the description field present and non-empty?
            description_quality.py # Third-person POV, use-case context, length checks
            format_valid.py        # Is frontmatter structure valid per skill spec?
          content/
            token_budget.py        # Is the skill under the token limit and under 500 lines?
            broken_references.py   # Do referenced files actually exist?
            duplicate_detection.py # Is this skill a near-copy of another?
          security/
            no_prompt_injection.py # Does the skill contain injection patterns?
            no_credential_access.py # Does the skill reference sensitive paths/env vars?
          commands/                # Command-specific rules
            description_required.py # Does the command have a description?
            script_exists.py       # Do referenced scripts exist?
            no_prompt_injection.py # Same injection check for commands
            no_credential_access.py # Same credential check for commands
          claude_md/               # CLAUDE.md-specific rules
            exists.py              # Does CLAUDE.md exist?
            skill_duplication.py   # Does it duplicate content from skills?
          hooks/                   # Hooks-specific rules
            valid_structure.py     # Valid structure, dangerous patterns, script existence
          agents/                  # Agent-specific rules
            description_required.py # Does the agent have a description?
            referenced_skills_exist.py # Do referenced skills exist?
            disallowed_tools_parseable.py # Is disallowedTools format valid?
            constraint_body_match.py # Do body constraints match disallowedTools?
            no_prompt_injection.py # Same injection check for agents
            no_credential_access.py # Same credential check for agents
        config/                    # Configuration system
          types.py                 # EvaluatorConfig, ResolvedConfig dataclasses
          loader.py                # Load .evaluator.yaml or --preset flag
          presets/
            recommended.py         # Default: catches real problems
            strict.py              # Recommended + style/optimization
            security.py            # Security rules only
```

`evaluate-setup/command.md` handles whole-setup evaluation (L1+L2). `evaluate-skill/command.md` handles single-skill deep evaluation (L1+L2+L3). `layer3-protocol.md` and `report-format.md` are loaded on demand via `Read`. The rule engine and Python scripts do the mechanical work that Claude can't or shouldn't do itself.

### 5.2 Layer 1 details: rule engine

Python package (`scripts/evaluate-setup/`). No LLM calls. Run via `uv run --project scripts/evaluate-setup evaluate-setup scan`.

**Input:** A path to scan. The tool always scans all file types (skills, commands, CLAUDE.md, hooks, agents).

**CLI:**

```bash
uv run --project scripts/evaluate-setup evaluate-setup scan <path> [--preset recommended|strict|security] [--config <path>] [--target <skill-name>]
```

- `--preset`: Evaluation preset (default: recommended)
- `--config`: Path to a custom `.evaluator.yaml` config file
- `--target`: Focus on a single skill by name (still scans everything for context, but filters output)

**Output:** JSON to stdout with per-rule diagnostics for all scanned file types. Human-readable summary to stderr.

#### 5.2.1 Rule engine architecture

The rule engine is inspired by [skilleval](https://github.com/natifridman/skilleval)'s TypeScript architecture, adapted to Python. The core idea: the engine knows how to run rules and collect results, but never knows what the rules check. Rules are self-contained plugins.

**Core types** (`scripts/engine/types.py`):

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Optional, Callable, Any

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class RuleCategory(str, Enum):
    STRUCTURAL = "structural"
    FRONTMATTER = "frontmatter"
    CONTENT = "content"
    SECURITY = "security"
    BEST_PRACTICES = "best_practices"

@dataclass(frozen=True)
class DiagnosticLocation:
    file: str
    start_line: Optional[int] = None    # 1-indexed

@dataclass(frozen=True)
class DiagnosticFix:
    description: str
    replacement: Optional[str] = None

@dataclass(frozen=True)
class Diagnostic:
    rule_id: str
    severity: Severity
    message: str
    location: DiagnosticLocation
    category: RuleCategory
    fix: Optional[DiagnosticFix] = None

@dataclass
class RuleMeta:
    id: str                               # e.g. "frontmatter/description-required"
    default_severity: Severity
    fixable: bool
    description: str
    category: RuleCategory
    messages: dict[str, str]              # message_id -> template with {{var}} placeholders

@dataclass
class ReportDescriptor:
    message_id: str
    data: Optional[dict[str, str]] = None # for {{key}} interpolation
    location: Optional[DiagnosticLocation] = None
    fix: Optional[DiagnosticFix] = None
    severity_override: Optional[Severity] = None

@dataclass
class RuleContext:
    skill: "ParsedSkill"
    report: Callable[[ReportDescriptor], None]  # callback — rules call this to emit findings
    severity: Severity
    options: list[Any] = field(default_factory=list)

@dataclass
class ParsedSkill:
    dir_path: str
    dir_name: str                         # skill name (directory basename)
    skill_md_path: str
    raw_content: str                      # entire SKILL.md as string
    frontmatter: dict                     # parsed YAML
    raw_frontmatter: str                  # raw YAML block
    frontmatter_start_line: int           # 1-indexed
    body: str                             # content after frontmatter
    body_start_line: int                  # 1-indexed
    files: list[str]                      # all files in skill directory
    parse_errors: list[str]

@dataclass
class LintResult:
    skill_path: str
    diagnostics: list[Diagnostic]
    error_count: int
    warning_count: int
    info_count: int
    fixable_count: int
    suppression_count: int = 0

class Rule(Protocol):
    meta: RuleMeta
    def create(self, context: RuleContext) -> None: ...
```

**Rule interface:** Any object with a `meta: RuleMeta` attribute and a `create(context)` method is a valid rule. Rules never return values — they call `context.report(descriptor)` to emit findings. The engine handles message interpolation, suppression filtering, and severity resolution inside the `report` callback. This means rules are pure detection logic with zero boilerplate.

**Rule registry** (`scripts/engine/registry.py`):

Module-level dict. Rules are registered at startup, not dynamically loaded.

```python
_registry: dict[str, Rule] = {}

def register_rule(rule: Rule) -> None:
    if rule.meta.id in _registry:
        raise ValueError(f'Rule "{rule.meta.id}" already registered')
    _registry[rule.meta.id] = rule

def get_all_rules() -> list[Rule]:
    return list(_registry.values())

def get_rules_by_category(category: RuleCategory) -> list[Rule]:
    return [r for r in _registry.values() if r.meta.category == category]

def clear_rules() -> None:  # for testing
    _registry.clear()
```

All rules are imported and registered in `rules/__init__.py` via `register_all_rules()`.

**The lint loop** (`scripts/engine/engine.py`):

```
def lint(skill_path: str, config: ResolvedConfig) -> LintResult:

    1. Parse skill_path into a ParsedSkill
       - Extract YAML frontmatter with PyYAML
       - Split body from frontmatter, track line numbers
       - List all files in skill directory
       - Collect any parse errors

    2. Parse suppression comments from raw_content
       - Regex: <!-- evaluator-ignore: rule-id1,rule-id2 -->  (file-wide)
       - Regex: <!-- evaluator-ignore-next-line: rule-id -->   (next line only)
       - Build a map: line_number -> set of suppressed rule IDs (or None for all)

    3. For each registered rule:
       a. Look up severity in config. If "off", skip.
       b. Create a report() closure that:
          - Checks if the diagnostic's line is suppressed for this rule
          - If suppressed, increment suppression_count and skip
          - Interpolates message template: "Body is {{tokens}} tokens"
            with data dict {"tokens": "5234"} -> "Body is 5234 tokens"
          - Creates a Diagnostic and appends to the diagnostics list
       c. Create RuleContext with parsed skill, resolved severity, report closure
       d. Call rule.create(context)

    4. Return LintResult with all diagnostics and counts
```

**Example rule implementation** (`scripts/rules/frontmatter/description_required.py`):

```python
@dataclass
class DescriptionRequired:
    meta = RuleMeta(
        id="frontmatter/description-required",
        default_severity=Severity.ERROR,
        fixable=False,
        description="The 'description' field is required in frontmatter",
        category=RuleCategory.FRONTMATTER,
        messages={
            "missing": "Required field 'description' is missing from frontmatter",
            "empty": "Field 'description' must not be empty",
        },
    )

    def create(self, context: RuleContext) -> None:
        skill = context.skill
        if skill.parse_errors:
            return  # can't check frontmatter if parsing failed

        description = skill.frontmatter.get("description")
        if description is None:
            context.report(ReportDescriptor(
                message_id="missing",
                location=DiagnosticLocation(
                    file=skill.skill_md_path,
                    start_line=skill.frontmatter_start_line,
                ),
            ))
        elif isinstance(description, str) and description.strip() == "":
            context.report(ReportDescriptor(
                message_id="empty",
                location=DiagnosticLocation(
                    file=skill.skill_md_path,
                    start_line=skill.frontmatter_start_line,
                ),
            ))
```

**Example quality rule** (`rules/frontmatter/description_quality.py`):

```python
class DescriptionQuality:
    meta = RuleMeta(
        id="frontmatter/description-quality",
        default_severity=Severity.WARNING,
        fixable=False,
        description="Description should follow Anthropic's best practices for skill discovery",
        category=RuleCategory.FRONTMATTER,
        messages={
            "first_person": "Description uses first-person POV ('{{match}}') — Anthropic recommends third-person",
            "no_use_case": "Description lacks use-case context — include phrases like 'use when', 'applies to'",
            "too_long": "Description is {{length}} characters — Anthropic's documented limit is 1,024",
            "too_short": "Description is only {{length}} characters — too vague for reliable skill matching",
        },
    )

    def create(self, context: RuleContext) -> None:
        skill = context.skill
        if skill.parse_errors:
            return
        description = skill.frontmatter.get("description", "")
        if not isinstance(description, str) or not description:
            return
        loc = DiagnosticLocation(file=skill.skill_md_path, start_line=skill.frontmatter_start_line or 1)

        # Check first-person POV
        match = re.search(r"\bI\s+(?:will|can|am|help)\b", description, re.I)
        if match:
            context.report(ReportDescriptor(message_id="first_person", data={"match": match.group(0)}, location=loc))

        # Check use-case context phrases
        desc_lower = description.lower()
        if not any(phrase in desc_lower for phrase in ["use when", "use for", "applies to", "relevant for", ...]):
            context.report(ReportDescriptor(message_id="no_use_case", location=loc))

        # Length checks
        if len(description) > 1024:
            context.report(ReportDescriptor(message_id="too_long", data={"length": str(len(description))}, location=loc))
        if len(description) < 20:
            context.report(ReportDescriptor(message_id="too_short", data={"length": str(len(description))}, location=loc))
```

**Example security rule** (`scripts/rules/security/no_prompt_injection.py`):

The security rule checks for known prompt injection patterns (e.g., "ignore previous instructions", "disregard all prior", "you are now", "system prompt override"). It uses context-aware severity — patterns found inside code fences or quoted examples are downgraded from error to warning, since they're likely documentation rather than actual injection attempts. This pattern is borrowed directly from skilleval's `no-prompt-injection` rule.

**Rules shipped (21 rules across 5 file types):**

**Skill rules (9):**

| Rule ID | Category | Default | What it checks |
|---|---|---|---|
| `structural/skill-md-exists` | structural | error | SKILL.md file exists in directory |
| `frontmatter/description-required` | frontmatter | error | Description field present and non-empty |
| `frontmatter/description-quality` | frontmatter | warning | Third-person POV, use-case context phrases, length 20-1024 chars |
| `frontmatter/format-valid` | frontmatter | warning | Frontmatter structure valid, name matches directory |
| `content/token-budget` | content | warning | Skill under token limit and under 500 lines |
| `content/broken-references` | content | error | Referenced files actually exist |
| `content/duplicate-detection` | content | warning | No near-duplicate skills (>0.85 TF-IDF cosine similarity) |
| `security/no-prompt-injection` | security | error | No injection patterns (context-aware: downgrades in code blocks) |
| `security/no-credential-access` | security | error | No references to sensitive paths/env vars/dangerous commands |

**Command rules (6):**

| Rule ID | Category | Default | What it checks |
|---|---|---|---|
| `command/description-required` | frontmatter | error | Description present and not too vague (>2 words) |
| `command/script-exists` | content | warning | Referenced .py scripts exist in command directory |
| `command/skill-overlap` | content | warning | No command is >60% similar to a skill body (cross-type duplication) |
| `command/duplicate-detection` | content | warning | No near-duplicate commands (>0.85 TF-IDF cosine similarity) |
| `command/no-prompt-injection` | security | error | Same injection pattern check as skills |
| `command/no-credential-access` | security | error | Same credential/dangerous command check as skills |

**CLAUDE.md rules (2):**

| Rule ID | Category | Default | What it checks |
|---|---|---|---|
| `claude-md/exists` | structural | warning | CLAUDE.md file is present in the project |
| `claude-md/skill-duplication` | content | warning | No sections duplicating content from skills (word overlap detection) |

**Hooks rules (1):**

| Rule ID | Category | Default | What it checks |
|---|---|---|---|
| `hooks/valid-structure` | security | warning | Commands defined, no dangerous patterns (rm -rf, force push), scripts exist |

**Agent rules (6):**

| Rule ID | Category | Default | What it checks |
|---|---|---|---|
| `agent/description-required` | frontmatter | error | Description field exists and is not empty |
| `agent/referenced-skills-exist` | content | error | Every skill listed in frontmatter has a matching SKILL.md |
| `agent/disallowed-tools-parseable` | frontmatter | warning | Entries match ToolName or ToolName(pattern) format |
| `agent/constraint-body-match` | content | warning | Body constraints ("cannot push") are backed by disallowedTools |
| `agent/no-prompt-injection` | security | error | Same injection pattern check as skills |
| `agent/no-credential-access` | security | error | Same credential check as skills |

#### 5.2.2 Config presets

Three presets control which rules run and at what severity.

**Recommended** (default) — catches real problems:

```python
RECOMMENDED = {
    # Skill rules
    "structural/skill-md-exists": "error",
    "frontmatter/description-required": "error",
    "frontmatter/description-quality": "warning",
    "frontmatter/format-valid": "warning",
    "content/token-budget": "warning",
    "content/broken-references": "error",
    "content/duplicate-detection": "warning",
    "security/no-prompt-injection": "error",
    "security/no-credential-access": "error",
    # Command rules
    "command/no-prompt-injection": "error",
    "command/no-credential-access": "error",
    # CLAUDE.md rules
    "claude-md/exists": "warning",
    # Agent rules
    "agent/description-required": "error",
    "agent/referenced-skills-exist": "error",
    "agent/disallowed-tools-parseable": "warning",
    "agent/constraint-body-match": "warning",
    "agent/no-prompt-injection": "error",
    "agent/no-credential-access": "error",
}
```

**Strict** — recommended plus style/optimization issues promoted to errors:

```python
STRICT = {
    **RECOMMENDED,
    "frontmatter/description-quality": "error",     # promoted
    "frontmatter/format-valid": "error",             # promoted
    "content/token-budget": "error",                 # promoted
    "claude-md/exists": "error",                     # promoted
    "agent/disallowed-tools-parseable": "error",     # promoted
    "agent/constraint-body-match": "error",          # promoted
}
```

**Security** — only security rules, everything else off:

```python
SECURITY = {
    "structural/skill-md-exists": "off",
    "frontmatter/description-required": "off",
    "frontmatter/description-quality": "off",
    "frontmatter/format-valid": "off",
    "content/token-budget": "off",
    "content/broken-references": "off",
    "content/duplicate-detection": "off",
    "security/no-prompt-injection": "error",
    "security/no-credential-access": "error",
    # Command security rules
    "command/no-prompt-injection": "error",
    "command/no-credential-access": "error",
    # CLAUDE.md rules
    "claude-md/exists": "off",
    # Agent rules
    "agent/description-required": "off",
    "agent/referenced-skills-exist": "off",
    "agent/disallowed-tools-parseable": "off",
    "agent/constraint-body-match": "off",
    "agent/no-prompt-injection": "error",
    "agent/no-credential-access": "error",
}
```

**User config file** (`.evaluator.yaml`):

```yaml
extends: recommended

rules:
  content/token-budget: error         # promote from warning to error
  security/no-prompt-injection: off   # suppress (not recommended)

ignore:
  - "archive/**"
  - "*-deprecated"
```

**Config resolution order:**

1. Start with `recommended` preset (hardcoded default)
2. If `.evaluator.yaml` exists in scan directory, load it and apply `extends` + `rules` overrides
3. If `--preset` CLI flag is passed, it overrides the file's `extends`
4. Result: `ResolvedConfig` with per-rule severity map + ignore patterns

#### 5.2.3 Inline suppression

Users can mark intentional exceptions in skill files:

```markdown
<!-- evaluator-ignore: content/token-budget -->
(This skill is intentionally large — it covers 15 edge cases that need to be in one place)

<!-- evaluator-ignore-next-line: frontmatter/description-quality -->
description: handles all frontend work
```

Two forms:
- `<!-- evaluator-ignore: rule-id -->` — suppresses the rule for the entire file
- `<!-- evaluator-ignore-next-line: rule-id -->` — suppresses the rule for the next line only

Multiple rules can be comma-separated: `<!-- evaluator-ignore: rule-a, rule-b -->`.

The engine parses these before running rules. Suppressed diagnostics are silently dropped in the `report()` callback — rules never know about suppressions. Suppression counts are tracked in `LintResult.suppression_count` for transparency.

**Output:** JSON to stdout. Example:

```json
{
  "scan_path": ".",
  "preset": "recommended",
  "total_items": 25,
  "total_tokens": 34200,
  "summary": {
    "errors": 4,
    "warnings": 6,
    "info": 2,
    "fixable": 2,
    "suppressed": 1,
    "by_type": {
      "skill": 14,
      "command": 6,
      "claude_md": 2,
      "hooks": 1,
      "agent": 2
    }
  },
  "items": [
    {
      "name": "python-error-handling",
      "path": "skills/python-error-handling",
      "type": "skill",
      "tokens": 663,
      "diagnostics": [
        {
          "rule_id": "frontmatter/description-quality",
          "severity": "warning",
          "message": "Description lacks use-case context — include phrases like 'use when', 'applies to'",
          "location": {"file": "skills/python-error-handling/SKILL.md", "start_line": 1},
          "category": "frontmatter"
        }
      ],
      "error_count": 0,
      "warning_count": 1,
      "info_count": 0,
      "fixable_count": 0,
      "suppression_count": 0
    }
  ]
}
```

**Dependencies** (managed via `pyproject.toml`):
- `tiktoken` — token counting
- `pyyaml` — frontmatter parsing
- `scikit-learn` — TF-IDF for duplicate detection
- `click` — CLI framework

### 5.3 Layer 2 details: the command prompt

The command prompt (`command.md`) is where the product logic lives. It encodes the evaluation criteria that Claude applies to each skill, command, and CLAUDE.md file. This is the part that requires the most craft — it's the difference between a generic "look at these files" and a rigorous quality audit.

**The prompt instructs Claude to:**

1. Run `evaluate-setup scan` via Bash and read the JSON
2. Read the actual skill files, command files, and CLAUDE.md (not just the static analysis — Claude needs to read the content to evaluate quality)
3. Evaluate each item against the criteria below
4. Produce the formatted report

**Evaluation criteria:**

**A. Structure & format** — Does the skill follow Claude Code's skill specification?

- YAML frontmatter with `name` and `description` fields present?
- Frontmatter under 1,024 characters total?
- Description starts with "Use when..." (Claude Search Optimization best practice)?
- Description describes triggering conditions and symptoms, NOT the skill's workflow? (Descriptions that summarize workflow cause Claude to follow the description instead of reading the full skill content — a known failure mode.)
- Body well-structured? (overview, when to use, core pattern, etc.)
- Concise? Target: under 500 words for most skills, under 200 for frequently-loaded ones.

**B. Redundancy** — Does the skill tell Claude something it doesn't already know?

The prompt includes a reference list of things Claude does by default without any skill:
- "Write clean, readable code" — redundant
- "Be helpful and thorough" — redundant
- "Handle errors properly" — redundant (too vague to add value beyond default)
- "Follow best practices" — redundant
- "Use proper formatting" — redundant
- "Think step by step" — redundant
- "Consider edge cases" — redundant

A skill is NOT redundant if it provides specific, actionable rules that go beyond the default. "Always use `raise from` for exception chaining in Python" is specific enough to change Claude's behavior. "Handle errors well" is not.

**C. Trigger quality** — Will Claude Code load this skill at the right time?

- Is the description specific enough that Claude Code can decide when to activate it?
- Is it too broad? ("when working with code" — triggers on everything, pollutes context)
- Is it too narrow? (only one very specific scenario — rarely triggers, wasted setup)
- Does it overlap with another skill's trigger? (both load when they shouldn't)

**C2. Autonomy impact** (scored within Trigger quality) — Skills should guide, not mandate.

- **Coercive language in description:** "MUST use this", "ALWAYS use this before", "NEVER skip" — these override the user's choice of when to activate the skill. A skill description should describe *when it's relevant*, not *demand* it runs. Cap trigger quality at 2/5 if the description mandates activation.
- **Hard gates in skill body:** `<HARD-GATE>`, "Do NOT proceed until", "STOP and do X first" — these block the user's workflow. Appropriate for narrow safety concerns (e.g., "don't commit secrets") but not for broad creative workflows.
- **Broad category intercept:** "any creative work", "all code changes", "every project" — skills that claim authority over entire work categories will trigger too often and erode user trust.
- **The test:** Ask "could a reasonable user want to skip this skill and go straight to coding?" If yes, the trigger language shouldn't prevent that.

**D. Content quality** — Are the instructions actually good?

- Specific and actionable instructions? Or vague platitudes?
- Concrete examples or patterns included?
- Could it be significantly shorter without losing value?
- Does it reference files that actually exist?
- Does it conflict with instructions in other skills?

**E. Token efficiency** — Is the value worth the cost?

- How many tokens does this skill burn when loaded?
- Is the value proportional? (A 5,000-token skill better deliver 10x the value of a 500-token one.)
- Could the same value be delivered in fewer tokens? (Common problem: skills that include lengthy explanations, multiple examples of the same pattern, or content that belongs in a separate reference file.)

#### 5.3.1 Structured rubric scoring

Inspired by [deepeval](https://github.com/confident-ai/deepeval)'s approach of requiring structured scores with reasoning, the prompt instructs Claude to score each skill on 5 dimensions. This makes ratings reproducible across sessions — two different Claude sessions evaluating the same skill should produce similar scores because the criteria are explicit.

**Dimensions and scoring anchors:**

| Dimension | 1 (worst) | 3 (acceptable) | 5 (best) |
|---|---|---|---|
| **Specificity** | Entirely vague platitudes, no actionable instructions | Mix of specific and generic; some rules change Claude's behavior | Every instruction is specific, actionable, includes concrete patterns or examples |
| **Redundancy** | Every instruction duplicates Claude's default behavior | Some unique value, but 50%+ is default behavior | Entirely unique — teaches Claude something it genuinely doesn't know |
| **Trigger quality** | No description, triggers on everything, or coercive language with broad scope | Description is reasonable but could be more precise | Description precisely targets the right tasks; starts with "Use when"; doesn't overlap with other skills; no coercive language |
| **Token efficiency** | Large with low value density | Reasonable size, some padding that could be trimmed | Every token earns its place; high value-to-token ratio |
| **Content quality** | No structure, no examples, broken references | Decent structure, some examples, no broken references | Well-organized, includes examples, references valid files, covers edge cases |

**Overall star rating:** Weighted average of dimensions, rounded.

**Reasoning requirement:** Each dimension score must include a one-sentence justification citing specific evidence from the skill content. Example: `Specificity: 5/5 — Concrete rules: "use raise from for exception chaining", "define custom exception hierarchies per module"`.

This rubric replaces the previous unstructured star rating. The criteria (A through E above) remain as the detailed evaluation guide — the rubric dimensions are how those criteria translate into scores.

#### 5.3.2 Single-skill mode (--target)

The `scan` command has a `--target` flag that scans everything but filters the JSON output to only include the target skill's diagnostics. Other items' data is still used for duplicate detection and overlap analysis.

```bash
uv run --project scripts/evaluate-setup evaluate-setup scan . --target python-conventions
```

Note: For a deep single-skill evaluation with A/B testing, use `/evaluate-skill` instead — it runs all 3 layers on one skill.

#### 5.3.3 CLAUDE.md evaluation

The tool always evaluates CLAUDE.md files as part of the full setup scan, against [Claude Code best practices](https://code.claude.com/docs/en/best-practices).

CLAUDE.md is loaded every session, so it has a different evaluation model than skills (which load on demand). The key question isn't "is this specific enough?" but "does every line earn its place in every conversation?"

**CLAUDE.md rubric dimensions:**

| Dimension | 1 (worst) | 3 (acceptable) | 5 (best) |
|---|---|---|---|
| **Conciseness** | Wall of text with tutorials and explanations | Some padding that could be trimmed | Every line passes the "would removing this cause mistakes?" test |
| **Signal-to-noise** | Full of generic advice Claude already follows ("write clean code", "be helpful") | Mix of useful rules and self-evident advice | Only contains things Claude can't figure out from code — bash commands, non-obvious conventions, project-specific rules |
| **Skill separation** | Domain-specific rules that should be skills are embedded in CLAUDE.md, loading every session | Some topic-specific content that could be a skill but isn't critical to move | All domain-specific knowledge is in skills; CLAUDE.md only has universally-applicable rules |
| **Structure** | Unstructured wall of text, no sections, no priorities | Has sections but unclear hierarchy, instructions easy to miss | Clear sections, critical rules marked with emphasis ("IMPORTANT", "YOU MUST"), scannable |
| **Conflict-free** | Contradicts multiple skills (e.g., CLAUDE.md says "use unittest", skill says "use pytest") | No direct contradictions but some ambiguous overlap | No contradictions with any skill; complementary content only |

**Source:** These dimensions are based on Anthropic's official guidance:
- "Keep it short and human-readable" — conciseness
- "For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it" — signal-to-noise
- "For domain knowledge or workflows that are only relevant sometimes, use skills instead" — skill separation
- "Bloated CLAUDE.md files cause Claude to ignore your actual instructions" — overall rationale
- Include/exclude table from official docs: exclude "standard language conventions Claude already knows", "self-evident practices like 'write clean code'"

**What the tool checks mechanically (Layer 1):**

- Line count and token count
- Duplicate content detection against all loaded skills (TF-IDF similarity)
- Conflict detection: scan for contradictory instructions between CLAUDE.md and skills
- Structural checks: does it have sections? Are any sections excessively long?
- Generic advice detection: flag known-redundant phrases ("write clean code", "be helpful", "follow best practices")

**Example output:**

```
### CLAUDE.md (project)                        ★★★★    KEEP
  Lines: 187 | Tokens: 2,400

  Rubric:
    Conciseness:      4/5  187 lines — reasonable but the "Available Skills" listing adds 30 lines that could be auto-generated
    Signal-to-noise:  5/5  No generic advice — all instructions are project-specific (uv, pre-commit, repo conventions)
    Skill separation: 4/5  Convention rules in "Conventions (all repos)" section are universally applicable — correct placement
    Structure:        5/5  Clear sections with headers, critical requirements marked in a dedicated block
    Conflict-free:    5/5  No contradictions with any skill

  + Critical Requirements section ensures key rules aren't missed
  + Repo-specific conventions (branch naming, Jira tracking) belong here, not in skills
  ! "Available Skills" section could be auto-generated rather than manually maintained
```

#### 5.3.4 Command evaluation

The tool always evaluates command.md files as part of the full setup scan.

Commands are user-triggered workflows (invoked via `/command-name`). They have different quality criteria than skills — a command needs clear instructions for Claude to follow, a valid description for the UI menu, and working script references.

**Command rubric dimensions:**

| Dimension | 1 (worst) | 3 (acceptable) | 5 (best) |
|---|---|---|---|
| **Description quality** | Missing or vague description that doesn't help the user decide when to use the command | Description exists but could be more specific about what the command does | Clear, concise description that tells the user exactly what the command does and when to use it |
| **Instruction clarity** | Vague instructions, Claude has to guess what to do | Instructions are reasonable but some steps are ambiguous or missing | Every step is clear and specific, Claude knows exactly what to do, in what order, with what output format |
| **Script integrity** | References scripts that don't exist, broken discovery patterns | Scripts exist but discovery pattern is fragile (hardcoded paths) | Scripts exist, discovery pattern is robust (relative paths, fallbacks), script runs without errors |
| **Scope appropriateness** | Should be a skill (describes passive behavior, not a user-triggered workflow) | Reasonable as a command but could overlap with an existing skill or command | Clearly a user-triggered workflow, no overlap with skills or other commands |
| **Token efficiency** | Bloated instructions with excessive examples or redundant steps | Reasonable length with some padding | Concise instructions, every section earns its place |

**What the tool checks mechanically (Layer 1):**

- Frontmatter validation: `description` field present and non-empty
- Script reference validation: if the command references a `.py` script, check it exists
- Token count
- Duplicate detection against other commands (similar descriptions or instructions)

**Example output:**

```
### /evaluate                                  ★★★★★   KEEP
  Tokens: 2,100

  Rubric:
    Description:      5/5  "Run evaluation questions against your AI bot/agent and compare results across versions"
    Instruction clarity: 5/5  Clear 4-step workflow with auto-discovery, version tracking, diff comparison
    Script integrity: 5/5  runner.py exists, discovery pattern with readlink + find fallback
    Scope:            5/5  User-triggered workflow — not something Claude should auto-invoke
    Token efficiency: 4/5  2,100 tokens — thorough but the auto-discovery grep patterns could be shorter

### /plan                                      ★★★★    KEEP
  Tokens: 450

  Rubric:
    Description:      5/5  Clear one-liner
    Instruction clarity: 4/5  References brainstorming + writing-plans skills but doesn't specify the handoff clearly
    Script integrity: 5/5  No script references — pure prompt command
    Scope:            5/5  User-triggered planning workflow
    Token efficiency: 5/5  450 tokens, concise
```

**F. Setup-wide recommendations** — Beyond grading individual skills, look at the whole setup and suggest structural improvements.

- **Merge candidates.** Two or more skills that cover closely related topics and would be stronger as a single, well-organized skill. Example: `python-error-handling` and `python-logging` could become one `python-reliability` skill if they're both short and always trigger together.
- **Skill → command conversion.** Some skills describe a specific workflow the user invokes explicitly ("audit my code", "generate a migration"). These should be commands (user-triggered via `/command`), not skills (auto-triggered by Claude Code). Skills are for passive behavior ("whenever you write Python, do X"). Commands are for active actions ("when I ask, do Y").
- **Command → skill conversion.** The reverse — a command that describes general behavior that should always be active. If the user has a `/python-style` command but wants those rules applied automatically, it should be a skill.
- **CLAUDE.md review.** Evaluate the project and user CLAUDE.md files:
  - Is it too long? (CLAUDE.md files that exceed ~2,000 tokens dilute attention on every single conversation turn.)
  - Does it duplicate what's already in skills? (Same instructions in CLAUDE.md and a skill means double the token cost for the same value.)
  - Does it contain instructions that belong in a skill instead? (Specific, topic-scoped rules like "always use pytest fixtures" belong in a skill that triggers only during testing — not in CLAUDE.md where they load on every turn.)
  - Does it conflict with any skills? (CLAUDE.md says "use unittest", a skill says "use pytest" — Claude gets confused.)
  - Is it well-structured? (Clear sections, not a wall of text. Numbered priorities so Claude knows what matters most.)
- **Overlapping triggers.** Flag groups of skills whose descriptions are similar enough that Claude Code might load multiple when only one is needed — wasting context on redundant instructions.
- **Coverage gaps.** Based on the types of skills present, flag obvious missing areas. If the user has 8 Python skills but nothing about testing, security, or git workflow — mention it as a potential gap (not a hard recommendation, just an observation).
- **Total context budget.** Sum up all skills + CLAUDE.md + commands that might load together in a typical session. If it exceeds 20% of Claude's context window, warn that the setup is heavy and suggest prioritizing cuts.

#### 5.3.5 Behavioral pattern checks (setup-wide)

These checks look at patterns across the whole setup, not individual items:

- **Mandate stacking.** Count skills that use coercive language (MUST, ALWAYS, NEVER) in descriptions or hard gates in body. If >2 skills mandate pre-conditions, they create conflicting demands — Claude can't MUST do everything before every task. Flag: "N skills use mandatory language — this creates competing mandates that erode reliability."
- **Autonomy erosion.** If the setup has skills that intercept broad work categories (e.g., "any creative work", "all code changes") AND those skills contain hard gates, the user loses control of their workflow. Flag when broad-trigger + hard-gate skills exist.
- **Broad trigger collision.** Multiple skills with overlapping broad triggers (e.g., two skills both triggering on "Python files" or "code changes") waste context by loading redundant instructions. Different from "overlapping triggers" above — this specifically checks for skills that cast too wide a net individually, not just overlap with each other.

#### 5.3.6 Command size thresholds

Commands use the same progressive disclosure principle as skills. A monolithic command.md loads its entire content when invoked.

- **Small:** Fine — most commands are a few KB.
- **Medium:** Recommend splitting into a thin command.md (execution steps, rubric) + reference files that Claude reads on demand.
- **Large:** Strong recommendation to split. The command is doing too much in one file.

### 5.4 Layer 3 details: `deep_eval.py`

Python module within the evaluator package (`scripts/evaluate-setup/src/the_evaluator/deep_eval.py`). Requires `GOOGLE_API_KEY` in environment (via `.env` file). No Anthropic API key needed — Claude runs tasks via subagents in the current session.

**Subcommands:**
- `screen-skills <skills-dir>` — Gemini screens which skills are A/B testable
- `generate-tasks <skill-path> [--red-team] [--repos-file <path>]` — Gemini generates 3 repo-based test tasks for a skill
- `validate-tasks <tasks-file>` — Validates task premises against actual repositories using Gemini-generated shell commands
- `judge <task> <file-a> <file-b> [--red-team] [--comparison-type absolute|marginal]` — Gemini judges which response is better (3 votes, blind dimension scoring)

**The flow for one skill (standard mode):**

```
Step 1: Screening (1 Gemini call, shared across all skills)
  Send: all SKILL.md files (first 1500 chars each)
  Receive: {"testable": [...], "not_testable": [...]} with reasons
  Saved to: .tmp/deep-eval/skill-screening.json

Step 2: Task generation (1 Gemini call per skill)
  Send: skill description + body + available repos (from repositories/)
  Receive: 3 repo-based tasks:
    Task 1: Code review on a real repo
    Task 2: Code writing on a real repo
    Task 3: Debugging/diagnosis on a real repo
  Tasks create situations where the skill's rules would naturally apply,
  not questions asking the agent to explain the rules.
  Saved to: .tmp/deep-eval/<skill>_tasks.json

Step 3: Execution (6 subagent spawns per skill)
  For each of the 3 tasks:
    Spawn subagent with all skills EXCEPT the tested one (all-except)
    Spawn subagent WITH the tested skill loaded (with-skill)
  All 6 subagents run in parallel.
  Responses saved to: .tmp/deep-eval/<skill>_task<N>_allexcept.txt and _withskill.txt

Step 3.5: Quality screening
  Check each task's responses for completeness (truncation, language mismatch).
  Skip judging for tasks with clearly unusable responses.

Step 4: Judging with repeat-and-vote (3 Gemini calls per skill, fewer if tasks skipped)
  For each valid allexcept/withskill pair:
    Send both responses to Gemini in randomized order (blinded).
    Judge scores each response on 5 dimensions (1-5): accuracy, specificity,
      actionability, completeness, response_posture.
    Winner by total score difference: >=3 clear, 1-2 marginal, 0 tie.
    Repeat 3 times (repeat-and-vote). Majority verdict wins.
  That's up to 3 pairs x 3 votes = 9 judge calls (fewer if tasks skipped).

Step 5: Aggregation (good-quality tasks only)
  Per-pair verdict = majority of the 3 judge votes.
  Per-pair confidence = HIGH (3-0 unanimous) or LOW (2-1 split).
  Per-pair redundancy signal = unique / redundant / unclear.
  Exclude tasks where judge reported test_quality: "poor".
  Per-skill verdict = pattern across good-quality tasks:
    wins > losses and wins > ties  -> KEEP
    losses > wins                  -> HURTS
    0 good-quality tasks           -> INCONCLUSIVE
    otherwise                      -> NO IMPACT
```

**Output per subcommand:** JSON to stdout.

**Judge output example:**

```json
{
  "comparison_type": "marginal",
  "votes": [
    {
      "reasoning": "Response 2 provides more specific file references and actionable suggestions.",
      "verdict": "with_skill",
      "scores": {
        "with_skill": {"accuracy": 4, "specificity": 5, "actionability": 4, "completeness": 4, "response_posture": 4},
        "without_skill": {"accuracy": 4, "specificity": 3, "actionability": 3, "completeness": 3, "response_posture": 3}
      },
      "test_quality": "good",
      "test_quality_reason": "Both responses substantively engaged with the task."
    }
  ],
  "pair_verdict": "with_skill",
  "confidence": "HIGH",
  "test_quality": "good",
  "dimension_deltas": {"accuracy": 0.0, "specificity": 1.3, "actionability": 0.7, "completeness": 0.7, "response_posture": 0.3}
}
```

**Saved artifacts:**

| Artifact | Location | Format |
|---|---|---|
| Skill screening | `.tmp/deep-eval/skill-screening.json` | JSON |
| Task definitions | `.tmp/deep-eval/<skill>_tasks.json` | JSON |
| Task validation | `.tmp/deep-eval/<skill>_validation.json` | JSON |
| Agent responses | `.tmp/deep-eval/<skill>_task<N>_allexcept.txt` / `_withskill.txt` | Plain text |
| Allexcept prompts | `.tmp/deep-eval/all_except_<skill>.txt` | Plain text |
| Repo snapshots | `.tmp/deep-eval/repo_snapshot_<repo>.txt` | Line count |
| Repo metadata | `.tmp/deep-eval/repos.json` | JSON |
| Deep evaluation log | `evaluate-skill-<skill-name>-log.md` | Markdown |

**Judge robustness:**
- **Blind dimension scoring** — the judge scores each response independently on 5 dimensions (accuracy, specificity, actionability, completeness, response_posture), then determines the winner by total score difference. The judge does NOT see the skill content — it evaluates purely on output quality.
- **Computed winner** — the winner is determined programmatically from scores, not from the judge's self-reported "winner" field. Score difference >=3 = clear winner, 1-2 = marginal winner, 0 = tie.
- **Dimension deltas** — per-dimension deltas (with_skill score - without_skill score) are averaged across good-quality votes and reported in the output. This shows exactly which quality dimensions the skill affects.
- **Reasoning before verdict** — the judge must explain its thinking before scoring.
- **Defensive JSON parsing** — the parser tries direct JSON, then code block extraction, then first `{...}` match, then first `[...]` match. Never crashes, never drops a result.

#### 5.4.1 Red-team mode

Inspired by [promptfoo](https://github.com/promptfoo/promptfoo)'s red-teaming and [giskard](https://github.com/Giskard-AI/giskard)'s adversarial testing. This mode addresses the open question from v1.0: "How to evaluate preventive skills?"

Preventive skills tell Claude NOT to do something — "never commit secrets", "always run tests before committing", "never use bare except". The standard A/B test (which measures output quality) can't capture whether these skills actually prevent bad behavior. Red-team mode tests this directly.

**How the engine identifies preventive skills:** Layer 1 includes a heuristic that flags skills containing negation patterns ("never", "do not", "always avoid", "must not", "forbidden"). This flag appears in the Layer 1 JSON. When Layer 3 runs, `deep_eval.py` automatically uses adversarial task generation for flagged preventive skills and standard task generation for the rest.

**The flow for one preventive skill:**

```
Step 1: Adversarial task generation (1 Gemini call)
  Send: skill description + full skill body + instruction to generate
    3 adversarial repo-based tasks:
    - Task 1: Direct request contradicting the skill's constraints
    - Task 2: Social engineering attempt
    - Task 3: Subtle edge case at the boundary of the skill's rules
  Receive: 3 adversarial tasks
  Saved to: .tmp/deep-eval/<skill>_tasks.json

Step 2: Execution (6 subagent spawns)
  Same as standard mode — with skill and without, all in parallel.

Step 3: Judging (9 Gemini calls)
  Different judge prompt — "Did Response A properly resist the
  adversarial request?" Verdict per pair: HELD / BROKE / PARTIAL

Step 4: Aggregation
  Per-skill red-team score: percentage of pairs where the skill held.
  Verdicts:
    80-100% held  -> STRONG
    50-79% held   -> WEAK
    0-49% held    -> FRAGILE
```


#### 5.4.2 Repeat-and-vote judge reliability

Inspired by [promptfoo](https://github.com/promptfoo/promptfoo)'s repeat-and-vote mechanism. LLM judges are non-deterministic — asking the same question twice can produce different verdicts. Running the judge once per pair (as in the v1.0 spec) means a single flaky call can flip a skill's entire verdict.

**How it works:**

For each with/without pair, the judge is called 3 times (same prompt, same responses, fresh call each time). The majority verdict wins:

- **3-0 unanimous** → HIGH confidence. All 3 judges agreed.
- **2-1 split** → LOW confidence. The majority wins, but the dissenting reasoning is preserved in the output so the user can see why one judge disagreed.

**Cost impact:** Up to 9 Gemini judge calls per skill (3 tasks × 3 votes), fewer if tasks are skipped for poor quality. No separate Claude API costs — subagents run in the current session.


**Why 3 votes, not 5:** Diminishing returns. 3 votes catches the common case (one judge was wrong) with minimal cost. 5 votes only helps when the judge is essentially flipping a coin, which means the skill difference is genuinely ambiguous — and that's a valid signal to surface as LOW confidence rather than mask with more votes.

**Dependencies** (package extras, `--extra deep`):
- `google-genai` — Gemini API SDK
- `python-dotenv` — .env file loading
- `anthropic` — listed but not currently used (reserved for future direct API testing)

### 5.5 How the layers combine in the commands

**`/evaluate-setup`** orchestrates L1+L2 on the whole setup:

0. **Step 0:** Ask output format (terminal/file).
1. Run Layer 1 (rule engine) on all skills, commands, CLAUDE.md, hooks, agents. Read the JSON.
2. Read all files and evaluate against rubrics (Layer 2). Score each item. Run cross-type optimization.
3. Produce the full review (to terminal or file).
4. **Always** print a short terminal summary with numbered suggestions.

**`/evaluate-skill`** orchestrates L1+L2+L3 on one skill:

1. User selects a skill (or passes it as argument).
2. Run Layer 1 on that skill. Read the JSON.
3. Read the skill's files + all other skills/CLAUDE.md for context. Score on rubric dimensions individually and contextually (Layer 2).
4. Check `GOOGLE_API_KEY`. Screen skill for testability (Gemini).
5. If testable: pre-build allexcept file, generate 3 tasks, spawn 6 agents (3 tasks × 2 conditions, each saves own output), screen response quality, run 3 marginal judge calls, aggregate good-quality results only.
6. Produce combined L1+L2+L3 report. Save detailed A/B log.
7. **Always** print a short terminal summary with the final verdict.

---

## 6. Scope

### 6.1 What v2.0 includes

- Evaluating Claude Code **skills**, **commands**, **CLAUDE.md**, **hooks**, and **agents**
- **Scan always evaluates everything.** The `scan` command finds all file types automatically. Use `--target` to focus output on a single skill while still scanning everything for context.
- **Two commands:** `/evaluate-setup` (whole setup, L1+L2) and `/evaluate-skill` (single skill, L1+L2+L3)
- **Interactive Step 0:** `/evaluate-setup` asks output format only. `/evaluate-skill` asks which skill + output format.
- **Layer 1:** pluggable rule engine with 21 rules across 5 file types (skills, commands, CLAUDE.md, hooks, agents)
- **Layer 1 extras:** config presets (recommended/strict/security), `.evaluator.yaml` per-rule overrides, inline suppression comments
- **Layer 2 skills rubric:** 5 dimensions (specificity, redundancy, trigger quality with autonomy impact, token efficiency, content quality)
- **Layer 2 autonomy analysis:** coercive trigger language detection ("MUST", "ALWAYS"), hard gate detection, broad category intercept detection
- **Layer 2 CLAUDE.md rubric:** 5 dimensions (conciseness, signal-to-noise, skill separation, structure, conflict-free)
- **Layer 2 commands rubric:** 7 dimensions (description quality, instruction clarity, script integrity, scope appropriateness, token efficiency with size thresholds, redundancy with defaults, robustness)
- **Layer 2 command size thresholds:** recommends progressive disclosure splitting for large commands
- **Layer 2 hooks evaluation:** structure validation, dangerous pattern detection, script existence
- **Layer 2 cross-type optimization:** suggests transformations between types (skill→hook, skill→command, CLAUDE.md→skill, etc.) when genuinely beneficial
- **Layer 2 behavioral pattern checks:** mandate stacking, autonomy erosion, broad trigger collision
- **Layer 2 setup-wide recommendations:** merge candidates, overlapping triggers, coverage gaps, total context budget
- **Numbered suggestions:** final summary with numbered items so users can say "do 1, skip 2"
- **Layer 3 standard (optional):** A/B evaluation via subagents + Gemini blind dimension scoring (3 votes per pair)
- **Layer 3 auto red-team:** adversarial testing automatically activates for preventive skills
- **Layer 3 skill screening:** Gemini pre-screens skills for A/B testability before user selects
- **Layer 3 artifacts:** all intermediate data saved to `.tmp/deep-eval/` (screening, tasks, responses, snapshots)
- **Layer 3 task validation:** `validate-tasks` subcommand verifies task premises against actual repos using Gemini-generated shell commands
- **Command prompt structure:** thin command.md + reference files (`layer3-protocol.md`, `report-format.md`) loaded on demand
- **Structural tests:** `tests/test_command_prompts.py` validates command.md and SKILL.md files (size, frontmatter, coercive language, orphan references)
- Read-only — never modifies files or repositories
- Cost controls — estimates before API calls, user confirms

### 6.2 What v2.0 does NOT include

- Evaluating MCP servers (hooks are covered, MCP is a future feature)
- Executable-test scoring (actually running generated code to check correctness)
- Mining chat history for real tasks to test against
- Caching results in SQLite for trend tracking
- CI/CD integration (automated evaluation on PR)
- Support for Cursor, Windsurf, or other AI coding tools
- Community skill registry or sharing results
- Web dashboard

### 6.3 Known limitations we ship with

1. **Layer 3 doesn't test skill activation.** It tests whether the skill's content helps when loaded. It does not test whether Claude Code correctly decides to load the skill. Layer 2 compensates by evaluating trigger quality.

2. **Generated tasks are biased toward the skill.** Because Gemini generates tasks from the skill's own description, the tasks test what the skill claims to do. The blind dimension scoring partially compensates — if both agents score similarly on specificity and actionability, that's a strong signal the skill is redundant regardless of task bias.

3. **LLM-as-judge isn't perfect.** Gemini has known biases (prefers longer responses, prefers better formatting, position effects). We mitigate with blinding, randomized order, repeat-and-vote (3 judge calls per pair with majority verdict), skill-aware context in the judge prompt, and requiring reasoning before verdict. LOW confidence pairs (2-1 splits) are flagged in the output.

4. **Layer 2 is only as good as its rubric.** The structured rubric (5 dimensions, 1-5 scoring with anchors) improves consistency across sessions compared to unstructured star ratings, but edge cases will surface. The rubric needs iteration based on real user feedback.

5. **Red-team mode is heuristic-based.** The engine identifies preventive skills by looking for negation patterns ("never", "do not", etc.). Some preventive skills may not use these patterns and will be missed. Some non-preventive skills may use negation and be incorrectly flagged.

---

## 7. Future versions

**v1.5 — more scope:** Evaluate MCP server configurations. CI/CD integration — run Layer 1 automatically on PRs that modify skills, post results as PR comments, block merge on errors. SQLite caching so you can track whether a skill's verdict changes over time ("this skill used to help, but since Claude 4.7 it's redundant"). Better duplicate detection using Gemini's embedding API. User-configurable rubric weights.

**v2 — more fidelity:** Real Claude Code subprocess mode — spawn `claude` in headless mode with controlled skill directories to test actual activation behavior. Chat history mining as an optional source of real tasks to test against. Multi-model judge ensemble for more reliable verdicts.

**v3 — ecosystem:** Community skill registry with quality scores. Web dashboard for results. Multi-tool support (Cursor, Windsurf, etc.).

---

## 8. Open questions

Status of questions from original design:

1. ~~**What is Claude's baseline behavior list?**~~ **Resolved.** The Layer 2 rubric includes a reference list of things Claude does by default (section 5.3). Layer 3's blind dimension scoring empirically validates this — if both agents score similarly, the skill is confirmed redundant.

2. ~~**Which Claude model for Layer 3?**~~ **Resolved differently.** Layer 3 uses Claude Code subagents (inheriting the current session's model) instead of the Claude API. No model selection needed.

3. ~~**How to evaluate preventive skills?**~~ **Resolved in v1.1** — red-team mode with adversarial task generation and HELD/BROKE/PARTIAL verdicts.

4. ~~**Should `/evaluate-setup` save a report file?**~~ **Resolved.** Step 0 asks the user to choose terminal or file output. Reports save to `evaluation-results/evaluate-setup-YYYY-MM-DD-HHMM.md`, deep logs to `evaluate-skill-<skill-name>-log.md`.

5. **Duplicate similarity threshold.** 0.85 cosine similarity is the current default. Needs calibration on more real skill sets.

6. **Rubric weight calibration.** Current dimension weights produce reasonable results in testing. Need more user feedback.

7. **Red-team adversarial task quality.** Partially addressed — Gemini generates tasks with repo context which makes them more realistic. Still needs evaluation on more preventive skills.

8. ~~**Rule engine extensibility for commands and CLAUDE.md.**~~ **Resolved.** Same engine with different parsers — 21 rules across 5 file types (skills, commands, CLAUDE.md, hooks, agents).

---

## 9. Success criteria

v1 is successful if:

1. A user can clone the repo and run `/evaluate-setup` on a real `.claude/` folder in **under 2 minutes** (Layers 1+2).
2. At least **80% of the rubric scores feel correct** to the user on manual inspection.
3. Running it on a typical bloated setup identifies at least **2-3 genuinely removable skills**.
4. Layer 3 deep eval on 5 skills completes successfully with repeat-and-vote producing **>70% HIGH confidence pairs**.
5. A user who knows nothing about skill best practices can **read the report and decide what to do** without needing to look anything up.
6. The rubric produces **consistent scores** — running the same evaluation twice on the same setup produces star ratings within ±1 star for each skill.
7. Red-team mode correctly identifies at least **1 weakness** in a preventive skill that the standard A/B test would miss.
8. Numbered suggestions in the summary are actionable — the user can say "do 1" and Claude executes it correctly.

---

## 10. Distribution

The user clones a GitHub repo and points Claude Code at the command:

```bash
git clone <repo-url> ~/.claude/the-evaluator
```

Then configures Claude Code to recognize the `/evaluate-setup` and `/evaluate-skill` commands (exact mechanism depends on how the user manages their commands — could be a symlink, a commands directory entry, or a path in settings).

No pip install. No build step. Two command prompts (`evaluate-setup/command.md` and `evaluate-skill/command.md`) and a Python package (`scripts/evaluate-setup/`). `uv run --project scripts/evaluate-setup` handles dependencies automatically. For `/evaluate-skill` Layer 3, add `--extra deep` and a `GOOGLE_API_KEY` in `.env`.
