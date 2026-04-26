# the-evaluator

**Status:** v1 scope defined · not yet built
**Author:** project lead (Red Hat data scientist) + design review with Claude
**Last updated:** April 2026

---

## Quick Overview

the-evaluator evaluates your Claude Code setup — skills, commands, CLAUDE.md, and how they all fit together. Run `/evaluate-setup` to evaluate everything, or `/evaluate-setup <path>` to focus on a specific skill or file. Either way, you get a report telling you what to keep, what to remove, what to merge, and what to fix.

It works in three layers, each going deeper than the last:

**Layer 1 — Count and check (Python script).** A script scans your skill files and does mechanical checks. It counts how many tokens each skill uses, detects near-duplicate skills using text similarity, checks if referenced files actually exist, and validates that each skill has proper formatting and a description. No AI involved — just parsing and math. Outputs a JSON report.

**Layer 2 — Expert review (Claude in your session).** Claude — the one already running in your conversation — reads the output of layer 1 results plus every skill and command file and CLAUDE.md, and evaluates the whole setup according to pre-define best practices. Per skill: is it telling Claude something it doesn't already do by default? Is the description clear enough to trigger correctly? Are the instructions specific or vague? Across the setup: should some skills be merged? Should any skill be a command instead (or vice versa)? Does CLAUDE.md duplicate or conflict with skills? Is the total context budget reasonable? This costs nothing extra because Claude is already running.

**Layer 3 — A/B experiment (optional).** Gemini generates test tasks from each skill's description. The Claude API runs those tasks twice — once with the skill loaded, once without. Then Gemini judges which output was better and provides a score + recommandation for future steps.

Layers 1 and 2 always run. Layer 3 is opt-in with `--deep` and requires API key from .env.

The tool is read-only — it never modifies, moves, or deletes any of your files. It just tells you what it found.

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

The system has three layers. The first two always run and are free. The third is optional and costs a few dollars.

**Layer 1: The robot inspector** (Python script, no AI, free, 2 seconds)

A Python script scans your skill files and checks the basics mechanically:
- How many tokens does each skill use?
- Are any two skills near-identical copies of each other?
- Do referenced files actually exist?
- Does each skill have a proper description so Claude knows when to load it?
- Is the formatting correct per the skill spec?

This catches the obvious stuff — broken files, duplicates, missing fields. It outputs structured JSON that layer 2 uses.

**Layer 2: Claude reviews your setup** (current session, free, ~30 seconds)

Claude — the one already running in your session, the one you're already paying for — reads the static analysis results AND reads each actual skill file, command file, and CLAUDE.md. Then it evaluates the whole setup according to pre-defined best practices:

- Is this skill telling Claude something it doesn't already know by default?
- Is the description specific enough that Claude Code will activate it at the right time?
- Are the instructions specific ("always use `raise from` for exception chaining") or vague ("handle errors properly")?
- Is it bloated — could the same value be delivered in half the tokens?
- Does it conflict with other skills or CLAUDE.md?
- Should any skills be merged? Should any skill be a command instead (or vice versa)?

This costs nothing extra because Claude is already running in your session.

**Layer 3: The science experiment** (optional, requires API keys, ~$0.15 per skill)

For users who want empirical proof, not just an expert opinion. This requires `ANTHROPIC_API_KEY` and `GEMINI_API_KEY` in your `.env` file.

Here's what happens for each skill:

1. **Gemini writes a test.** It reads the skill's description and content, then creates 3 tasks that the skill should help with — graded easy, medium, hard.

2. **Claude takes the test twice.** The script calls the Claude API with the same task, once with the skill text loaded into the system prompt and once without. Same model, same task, only difference is whether the skill instructions are present. This is repeated 3 times per task to account for randomness.

3. **Gemini grades blind.** A separate Gemini call receives both responses in randomized order without knowing which had the skill. It picks the better response, or calls it a tie, and explains its reasoning.

4. **The verdict.** If the skill version won most comparisons — the skill actually makes Claude's output better, keep it. If mostly ties — the skill makes no measurable difference, it's dead weight. If the skill version lost — the skill is actively making things worse.

### 3.2 How the layers flow together

```
User types: /evaluate-setup

  +----------------------------------+
  |  Layer 1: Static analysis        |  Free, instant
  |  Python script, no AI            |
  |  Token counts, duplicates,       |
  |  broken refs, format checks      |
  +----------------+-----------------+
                   | JSON output
                   v
  +----------------------------------+
  |  Layer 2: Claude review          |  Free (current session)
  |  Reads JSON + skill/command      |
  |  files + CLAUDE.md               |
  |  Evaluates quality, redundancy,  |
  |  triggers, setup-wide issues     |
  |  Produces the report             |
  +----------------+-----------------+
                   |
             --deep flag?
            /            \
          no              yes
          |                |
     Done. Show     Check for API keys.
     report.        Show cost estimate.
                    User confirms.
                           |
                   +-------v--------------+
                   |  Layer 3: A/B eval   |  ~$0.15/skill
                   |  Gemini writes tasks  |
                   |  Claude API runs     |
                   |  with + without      |
                   |  Gemini judges blind  |
                   +---------+------------+
                             |
                        Done. Report
                        includes A/B
                        evidence.
```

### 3.3 What this does NOT test

Layer 3 tests: "Does having this skill's text in Claude's context make the output better?"

Layer 3 does NOT test: "Does Claude Code correctly decide when to load this skill?" That would require running real Claude Code in subprocess mode, which is a v2 feature. This limitation is stated clearly in the output so users aren't misled.

Layer 2 partially compensates — Claude can review the skill's description and tell you whether it's likely to trigger correctly, even without empirically testing it.

---

## 4. How the user uses it

### 4.1 The command

```
/evaluate-setup [path] [--deep]
```

The user types `/evaluate-setup` inside Claude Code with optional arguments:

```
/evaluate-setup
  Claude asks what to evaluate, or scans the default ~/.claude/ path.

/evaluate-setup ~/.claude/skills/
  Check all skills. Layers 1+2. Free.

/evaluate-setup ~/.claude/skills/python-error-handling/
  Check just one skill. Layers 1+2. Free.

/evaluate-setup ~/.claude/ --deep
  Full evaluation with A/B testing. Claude warns about cost first.

/evaluate-setup ~/.claude/skills/react-helper/ --deep
  Deep eval on one suspicious skill. Cheap (~$0.15).
```

Natural language works too. The command prompt tells Claude to handle things like:
- "evaluate my setup"
- "is my python-error-handling skill any good?"
- "which of my skills should I remove?"
- "run the deep test on react-helper"

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
- If `--deep`: A/B results — win/loss/tie counts with the judge's reasoning

### 4.3 Example output

```
/evaluate-setup ~/.claude/skills/

Analyzing setup at ~/.claude/skills/ ...

## Static Analysis
  14 skills found | 34,200 tokens total (17% of context budget)
  1 duplicate pair detected
  3 skills missing descriptions
  1 broken file reference

## Per-Skill Review

### python-error-handling                    ****    KEEP
  Tokens: 663 | Well-scoped | Specific instructions
  + Actionable rules (raise from, exception hierarchies)
  + Clear trigger scope (Python error handling tasks)
  ! Could add examples to improve activation

### be-helpful                               *       REMOVE (redundant)
  Tokens: 168 | Redundant with baseline
  x No description -- Claude can't decide when to activate
  x "Be helpful and thorough" -- Claude already does this by default
  x References scripts/helper.sh which doesn't exist

### pdf-wizard                               ****    KEEP
  Tokens: 3,800 | Domain-specific
  + Specific PDF manipulation instructions
  ! 91% similar to pdf-creator -- keep one, remove the other

### react-helper                             **      REVIEW
  Tokens: 5,200 | Oversized
  ! 5,200 tokens is excessive -- most skills work under 1,500
  ! Mixes React, CSS, testing, deployment -- should be split
  x Trigger condition too broad: "when working with frontend"

## Summary
  Keep:    5 skills (total: 14,200 tokens)
  Remove:  6 skills (total: 18,400 tokens)  <- potential savings
  Review:  3 skills

  3 skills scored poorly. Want me to run deep evaluation on those?
  It'll make ~54 API calls, estimated cost ~$0.50.
  Requires ANTHROPIC_API_KEY and GEMINI_API_KEY in your .env.
```

### 4.4 Safety

- **Read-only.** The tool never modifies, moves, or deletes any files. It only recommends.
- **Cost controls.** Deep evaluation shows a cost estimate and asks for confirmation before making any API calls.
- **Privacy.** No data leaves your machine except API calls to Anthropic and Google (layer 3 only). Layers 1+2 are completely local.

---

## 5. Technical details

### 5.1 File structure

The entire tool is three files:

```
the-evaluator/
  commands/
    evaluate-setup/
      prompt.md              # The /evaluate-setup command prompt
  scripts/
    static_analyze.py        # Layer 1: static analysis
    deep_eval.py             # Layer 3: A/B evaluation
```

`prompt.md` is the brain — it tells Claude what to do, what criteria to evaluate against, and how to format the output. The two Python scripts are the hands — they do the mechanical work that Claude can't or shouldn't do itself.

### 5.2 Layer 1 details: `static_analyze.py`

Pure Python. No LLM calls. Uses PEP 723 inline dependencies so `uv run static_analyze.py` just works — no install step.

**Input:** A path. Can be a single skill file, a skill directory, a folder of skills, or `~/.claude/`.

**What it checks:**

| Check | How |
|---|---|
| Token count per skill | `tiktoken` tokenizer |
| Total context budget | Sum all skill tokens, show as percentage of model context window |
| Duplicate detection | TF-IDF or Jaccard similarity on word sets, flag pairs above 0.85 |
| Broken file references | Parse skill content for file paths, check each exists |
| Missing description | Parse YAML frontmatter, check `description` field |
| Missing trigger | Check if description starts with "Use when" or similar |
| Format validation | Validate frontmatter structure against skill spec |
| Oversized | Flag skills over 1,500 tokens |

**Output:** JSON to stdout. Example:

```json
{
  "scan_path": "~/.claude/skills/",
  "total_skills": 14,
  "total_tokens": 34200,
  "context_budget_pct": 17.1,
  "skills": [
    {
      "name": "python-error-handling",
      "path": "~/.claude/skills/python-error-handling/SKILL.md",
      "tokens": 663,
      "has_description": true,
      "has_trigger": true,
      "description_starts_with_use_when": true,
      "broken_refs": [],
      "format_valid": true,
      "oversized": false
    }
  ],
  "duplicates": [
    {"skill_a": "pdf-wizard", "skill_b": "pdf-creator", "similarity": 0.91}
  ],
  "issues": [
    {"skill": "be-helpful", "issue": "missing_description"},
    {"skill": "be-helpful", "issue": "broken_ref", "detail": "scripts/helper.sh"},
    {"skill": "react-helper", "issue": "oversized", "tokens": 5200}
  ]
}
```

**Dependencies** (PEP 723 inline):
- `tiktoken` — token counting
- `pyyaml` — frontmatter parsing
- `scikit-learn` — TF-IDF for duplicate detection

### 5.3 Layer 2 details: the command prompt

The command prompt (`prompt.md`) is where the product logic lives. It encodes the evaluation criteria that Claude applies to each skill, command, and CLAUDE.md file. This is the part that requires the most craft — it's the difference between a generic "look at these files" and a rigorous quality audit.

**The prompt instructs Claude to:**

1. Run `static_analyze.py` via Bash and read the JSON
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

### 5.4 Layer 3 details: `deep_eval.py`

Python script with PEP 723 inline dependencies. Requires `ANTHROPIC_API_KEY` and `GEMINI_API_KEY` in environment (typically via `.env` file).

**Input:** Path to a skill + optionally the JSON from layer 1 for context.

**The flow for one skill:**

```
Step 1: Task generation (1 Gemini Flash call)
  Send: skill description + full skill body
  Receive: 3 tasks, graded easy / medium / hard
  These are realistic tasks that the skill claims to help with.

Step 2: Execution (18 Claude API calls)
  For each of the 3 tasks:
    Call Claude API WITH the skill text in the system prompt.
    Call Claude API WITHOUT the skill text (neutral system prompt).
    Repeat each 3 times (to reduce randomness).
  That's 3 tasks x 2 conditions x 3 runs = 18 calls.

Step 3: Judging (9 Gemini calls)
  For each of the 9 with/without pairs:
    Send both responses to Gemini, blinded.
    Randomize which response is shown first (prevents position bias).
    Gemini picks the better response or calls it a tie.
    Gemini explains its reasoning.

Step 4: Aggregation
  Per-task verdict = majority of the 3 judgment runs.
  Per-skill verdict = pattern across the 3 tasks:
    Majority of tasks won     -> skill HELPS
    Majority of tasks tied    -> skill has NO IMPACT (dead weight)
    Majority of tasks lost    -> skill HURTS
```

**API call count per skill:**

| Call type | Count |
|---|---|
| Gemini Flash (generate tasks) | 1 |
| Claude API (with skill) | 9 |
| Claude API (without skill) | 9 |
| Gemini (blind judge) | 9 |
| **Total** | **28** |

**Cost:** ~$0.10-0.25 per skill depending on task complexity and skill length.

**Output:** JSON to stdout. Example:

```json
{
  "skill": "python-error-handling",
  "tasks": [
    {
      "description": "Write a function that reads a config file and returns parsed settings, handling all failure modes.",
      "difficulty": "easy",
      "runs": [
        {
          "judge_verdict": "with_skill",
          "judge_reasoning": "Response A uses raise from for exception chaining and provides specific error messages with file path context. Response B uses bare except clauses."
        },
        {
          "judge_verdict": "with_skill",
          "judge_reasoning": "Response A defines a custom ConfigError hierarchy. Response B catches generic Exception."
        },
        {
          "judge_verdict": "with_skill",
          "judge_reasoning": "Response A includes context managers and cleanup. Response B does not."
        }
      ],
      "task_verdict": "with_skill"
    }
  ],
  "ab_verdict": "KEEP",
  "wins": 3,
  "ties": 0,
  "losses": 0
}
```

**Dependencies** (PEP 723 inline):
- `anthropic` — Claude API SDK
- `google-genai` — Gemini API SDK

### 5.5 How the layers combine in the command

The prompt instructs Claude to orchestrate the layers:

1. **Always** run `static_analyze.py` and read the JSON (layer 1).
2. **Always** read the actual skill files and evaluate them against the criteria (layer 2).
3. Produce the report with star ratings, verdicts, and recommendations.
4. **After** the report:
   - If the user passed `--deep`: check for API keys in environment, show cost estimate, ask for confirmation, then run `deep_eval.py` on the requested skills.
   - If the user did NOT pass `--deep` but some skills scored 2 stars or below: suggest running deep eval on just those few skills (cheap, targeted).
5. If layer 3 ran, incorporate the A/B results into the final report — each skill's verdict card gets a line showing win/loss/tie counts and whether the A/B evidence confirms or contradicts the layer 2 assessment.

---

## 6. Scope

### 6.1 What v1 includes

- Evaluating Claude Code **skills**, **commands**, and **CLAUDE.md** files
- Scope selection: single skill or command, a folder, or entire `~/.claude/` setup
- **Layer 1:** token counts, duplicate detection, broken refs, format validation, oversized flags
- **Layer 2:** evaluation against skill best practices, redundancy with Claude's baseline, trigger quality, content quality, token efficiency, setup-wide recommendations (merge candidates, skill/command conversion, CLAUDE.md review, overlapping triggers, coverage gaps, total context budget)
- **Layer 3 (optional):** A/B evaluation with Gemini-generated tasks, Claude API execution, Gemini blind judging
- Read-only — never touches your files
- Cost controls — estimates before API calls, user confirms

### 6.2 What v1 does NOT include

- Evaluating hooks or MCP servers (skills, commands, and CLAUDE.md only — other types are a v1.5 feature)
- Running real Claude Code in subprocess mode (v1 uses the Claude API directly — see section 3.3 for why this matters)
- Executable-test scoring (actually running generated code to check correctness)
- Mining chat history for real tasks to test against
- Caching results in SQLite for trend tracking
- Support for Cursor, Windsurf, or other AI coding tools
- Community skill registry or sharing results
- Web dashboard
- Auto-fix or auto-delete (the tool will never modify files — by design, permanently)

### 6.3 Known limitations we ship with

1. **Layer 3 doesn't test skill activation.** It tests whether the skill's content helps when loaded. It does not test whether Claude Code correctly decides to load the skill. This is stated clearly in the output.

2. **Generated tasks are biased toward the skill.** Because Gemini generates tasks from the skill's own description, the tasks test what the skill claims to do. A skill could ace its own tasks but still be useless in real-world usage (e.g., it triggers too broadly and pollutes unrelated conversations). Layer 2 partially compensates by evaluating trigger quality independently.

3. **LLM-as-judge isn't perfect.** Gemini has known biases (prefers longer responses, prefers better formatting, position effects). We mitigate with blinding, randomized order, and majority-of-3 voting. Not eliminated.

4. **Layer 2 is only as good as its rubric.** The evaluation criteria in the prompt need iteration based on real user feedback. The initial rubric is based on Anthropic's skill spec and Claude Code best practices, but edge cases will surface.

---

## 7. Future versions

**v1.5 — more scope:** Evaluate hooks and MCP server configurations. SQLite caching so you can track whether a skill's verdict changes over time ("this skill used to help, but since Claude 4.7 it's redundant"). Better duplicate detection using Gemini's embedding API. Configurable rubric.

**v2 — more fidelity:** Real Claude Code subprocess mode — spawn `claude` in headless mode with controlled skill directories to test actual activation behavior. Chat history mining as an optional source of real tasks to test against. Multi-model judge ensemble for more reliable verdicts.

**v3 — ecosystem:** Community skill registry with quality scores. Web dashboard for results. Multi-tool support (Cursor, Windsurf, etc.).

---

## 8. Open questions

These need answers before or during v1 development:

1. **What is Claude's baseline behavior list?** The redundancy check needs a comprehensive list of things Claude already does without any skill. This needs research — read Anthropic's documentation, test Claude's default behavior on common tasks, and compile the list. Getting this wrong means false positives (flagging useful skills as redundant) or false negatives (missing actually redundant ones).

2. **Which Claude model for layer 3?** Sonnet is more representative of real usage but costs more per call. Haiku is cheaper but might not surface subtle quality differences. Recommendation: default to Sonnet, offer `--model haiku` flag for budget-conscious users.

3. **How to evaluate preventive skills?** Skills like "never commit secrets" or "always run tests before committing" are meant to prevent bad outcomes, not improve positive outcomes. The A/B test methodology (which compares quality of output) doesn't naturally capture "did it avoid doing something dangerous?" This needs a different evaluation approach — probably adversarial tasks designed to trigger the bad behavior.

4. **Should `/evaluate-setup` save a report file?** The in-session output might be enough for v1. But if the user evaluates 20+ skills, the output is long and scrolls off screen. A saved markdown file in `.tmp/` or the working directory could help. Low priority — easy to add later.

5. **Duplicate similarity threshold.** 0.85 cosine similarity is a guess. Needs calibration on real skill sets — too high and we miss duplicates, too low and we flag false positives.

---

## 9. Success criteria

v1 is successful if:

1. A user can clone the repo and run `/evaluate-setup` on a real `.claude/` folder in **under 2 minutes**.
2. At least **80% of the verdicts feel correct** to the user on manual inspection.
3. Running it on a typical bloated setup identifies at least **2-3 genuinely removable skills**.
4. Layer 3 deep eval on 5 skills costs **under $1.50**.
5. A user who knows nothing about skill best practices can **read the report and decide what to do** without needing to look anything up.

---

## 10. Distribution

The user clones a GitHub repo and points Claude Code at the command:

```bash
git clone <repo-url> ~/.claude/the-evaluator
```

Then configures Claude Code to recognize the `/evaluate-setup` command (exact mechanism depends on how the user manages their commands — could be a symlink, a commands directory entry, or a path in settings).

No pip install. No package manager. No build step. It's just files — a prompt and two Python scripts. `uv run` handles the Python dependencies automatically via PEP 723 inline metadata.
