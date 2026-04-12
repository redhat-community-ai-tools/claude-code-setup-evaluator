# Getting Started with the AI Workspace

Welcome! This workspace gives you superpowers when working with AI coding assistants. It supports both **Claude Code** and **Cursor** — same skills, same commands, same workflow.

---

## Setup

1. **Clone your repo** into the `repositories/` folder:
   ```bash
   cd repositories/
   git clone <your-repo-url>
   ```

2. **Start your AI tool** in the workspace root:

   | Tool | How to start |
   |---|---|
   | Claude Code | Run `claude` in the terminal |
   | Cursor | Open the workspace folder in Cursor |

3. **Tell the AI which repo to focus on** — e.g., "work on site-analysis" or "I'm working on repositories/my-project."

4. **Type `/toolkit`** to see what's available and get recommendations based on your current repo.

That's it. Everything else activates automatically as you work.

> **Note:** Your cloned repos are gitignored — they belong to you, not the workspace. Push changes from inside the repo folder and they go to that repo's remote. The workspace never tracks your repos.

---

## Start Here

Your daily workflow in 4 commands:

```
/plan          → before coding anything complex
/verify        → after coding, check it works
/review        → code review
/commit        → commit with a good message
```

Everything else is available when you need it. Skills activate automatically — you don't need to do anything to benefit from them.

---

## How It Works

This workspace has four types of capabilities:

| Capability | What it is | Claude Code | Cursor |
|---|---|---|---|
| **Skills** | Knowledge the AI carries. Activates automatically when relevant. | `skills/*/SKILL.md` | `.cursor/rules/*.mdc` |
| **Commands** | Workflows you trigger by typing `/command` in chat. | `.claude/commands/` | `.cursor/commands/` |
| **Agents** | Helpers the AI spawns for parallel work. You don't control them. | Built-in (Explore, Plan, general-purpose) | Built-in (background agents) |
| **Hooks** | Tripwires that fire on events (like blocking a push if secrets are detected). | Full support (session start, pre-commit, skill suggestion) | Session start only |

### Hooks: What's different between tools

| Hook | Claude Code | Cursor |
|---|---|---|
| Session start (repo status) | Yes | Yes |
| Pre-commit secret scan | Yes (blocks git commit/push if API keys detected) | No — run `/quality-gate` manually before pushing |
| Auto-skill suggestion | Yes (reminds AI which skills are relevant) | Partial — rules with `globs` auto-attach when matching files are open |

---

## Skills (automatic)

Skills activate on their own — you just get better results. In Claude Code they live in `skills/`, in Cursor they live in `.cursor/rules/`. Same content, different format.

| Name | Purpose | Example |
|---|---|---|
| python-patterns | Team dotenv conventions — `.env` structure, loading patterns, secure defaults | You write `os.getenv("API_KEY", "AIza...")` — the AI flags the real key in the default and fixes it to `os.getenv("API_KEY")` with a validation check |
| python-testing | TDD workflow (red/green/refactor), pytest patterns, data science testing (DataFrames, models) | You say "add a validation function" — the AI writes a failing test first with `pd.testing.assert_frame_equal`, then implements to make it pass |
| security-check | Credential leak detection (Gemini, OpenAI, Jira, AWS, GitHub keys), insecure code (eval, pickle, shell injection), LLM-specific risks | You send raw email addresses to Gemini — the AI flags PII leakage and suggests sanitizing before sending |
| data-pipeline-patterns | Pipeline stage design, data validation at boundaries, circuit breakers, checkpoint/resume, debugging workflow | You add a new pipeline step — the AI structures it with input validation, checkpoints every 100 items, and a circuit breaker after 5 consecutive API failures |
| api-client-patterns | Retry with exponential backoff, rate limiting, auth, pagination, LLM response parsing | You build a Jira API client — the AI adds `timeout=30`, retry for 429/500/502/503 with `Retry-After` support, and validates the response structure |
| git-workflow | GitLab/GitHub conventions, branch workflow, commit practices | You commit changes in a repo — the AI follows team conventions: feature branches, clear commit messages, MRs for review |
| mcp-patterns | Building/securing MCP servers — schema-first design, auth, input validation, audit logging, DS-specific patterns | You build an MCP tool for querying datasets — the AI enforces Pydantic input schemas with limits (`max_rows=10000`) and adds audit logging |
| verification-loop | Unified verification engine behind `/verify`, `/review`, `/quality-gate` — environment checks, types, lint, tests, code review, security scans | You say "review my changes" — the AI checks for bare `except` clauses, functions over 50 lines, data leakage, and gives APPROVE or REQUEST CHANGES |
| deep-research | Multi-source research — breaks questions into sub-queries, searches in parallel, synthesizes with citations | You ask "best Python library for HTML-to-PDF?" — the AI researches weasyprint, pdfkit, playwright, compares tradeoffs, and recommends one |
| codebase-onboarding | 4-phase analysis of unfamiliar codebases — reconnaissance, architecture mapping, convention detection, guide generation | You open a repo you've never seen — the AI maps the structure, identifies entry points, detects testing conventions, and produces a "start here" guide |
| brainstorming | Collaborative design exploration before implementation — asks clarifying questions one at a time, proposes 2-3 approaches with trade-offs, presents design for approval, writes spec doc | You say "I want to add retry logic" — the AI asks about failure modes, proposes approaches (simple retry vs exponential backoff vs circuit breaker), presents a design, writes a spec, and only then moves to planning |
| writing-plans | Creates detailed implementation plans from approved specs — bite-sized tasks (2-5 min each), exact file paths, complete code blocks, TDD steps, no placeholders | The AI takes your approved design and produces a step-by-step plan: "Task 1: write failing test for X, Task 2: implement X, Task 3: write failing test for Y..." with full code in every step |

---

## Commands (you trigger these)

Type the command name in the chat to run it. Commands work the same in both Claude Code and Cursor.

| Name | Purpose | Example |
|---|---|---|
| /plan | Restate requirements, search for existing solutions, identify risks, create a step-by-step plan. Waits for your OK before writing code | "I need to add retry logic to the pipeline" — the AI searches for existing retry patterns, proposes a plan, and waits for approval |
| /verify | Run verification phases 1–4: environment, types, lint, tests. Use after coding, before review | After writing a new module — run `/verify` to catch type errors and failing tests before review |
| /review | Run phase 5: code review with DS anti-patterns and security checks. Produces APPROVE or REQUEST CHANGES. Use after `/verify` | The AI checks for bare `except` clauses, data leakage, functions over 50 lines, and gives a verdict |
| /quality-gate | Run phases 1–4 + 6: tests + secret scan + pre-commit. Gives READY TO PUSH or BLOCKED. Use right before `git push` | Before pushing — run `/quality-gate` to confirm no secrets leaked and all tests pass |
| /test-coverage | Analyze coverage, list untested files, prioritize what to test next (HIGH/MEDIUM/LOW) | The AI finds 3 core functions with no tests and marks them HIGH priority |
| /toolkit | Show all available skills, commands, and agents, recommend based on current context. Start here if you're new | Type `/toolkit` in a new repo — get a tailored list of what's available and what to use first |
| /recap | Summarize the session — what changed, why, key decisions. Copy-pasteable for standup or Slack | After a long session — get a structured update ready to paste into your team channel |
| /diff-explain | Explain changes grouped by intent, not file count | "The pipeline was split into 3 independent steps" instead of "14 files changed" |
| /visualize | Generate an interactive HTML project map with collapsible file tree, color-coded by language | Get a visual overview of the repo structure with file sizes and language breakdown |
| /ai-engineer-review | Brutally honest architecture/code/security review with scored assessment and top 3 prioritized improvements | `/ai-engineer-review security` — focused security audit with concrete fix instructions |
| /commit | Generate a short, accurate commit message from the diff + conversation context, show preview, commit after approval | You've been adding retry logic — type `/commit` and get `Add exponential backoff to Jira API client` instead of `update jira_client.py` |
| /refactor-safe | Refactor internals without changing public API — fixes long functions, duplication, poor naming while keeping the external interface identical | A 65-line handler doing validation + inference + logging → the AI extracts helpers, simplifies nesting, but the function signature and return type stay exactly the same |
| /env-check | Validate local development environment — Python version, dependencies, env vars, config files, pre-commit hooks | You clone a repo after two weeks — run `/env-check` and get a pass/fail summary: "GOOGLE_API_KEY missing, pre-commit not installed" with fix instructions |
| /explain-simple | Explain a file or folder in very simple words, like to a 15-year-old — no jargon, no code, just what it does and why | `/explain-simple scripts/fetch_jira_data.py` — "This script downloads work tickets from Jira. It goes through a list of people and looks up their tasks, one person at a time..." |
| /prompt-test | Test LLM prompts against sample inputs — checks completeness, format compliance, grounding, and parseability. Catches regressions when prompts change | `/prompt-test prompts/person_prompts.py` — runs the prompt with 3 sample inputs, calls Gemini, shows parsed results, flags hallucinations on sparse input |
| /explain-code | Explain code from high-level overview to line-by-line analysis, scaled to complexity | `/explain-code src/pipeline/jira_client.py` — get purpose, structure breakdown, data flow, and gotchas for onboarding or knowledge transfer |
| /architecture-docs | Generate architecture documentation with Mermaid diagrams — system overview, data flow, components, design decisions | `/architecture-docs repositories/ai-initiatives-observer` — produces a maintainable architecture doc with data flow diagrams and ADRs |

---

## Agents (automatic)

The AI spawns these as sub-processes for parallel or specialized work.

| Name | Purpose | Claude Code | Cursor |
|---|---|---|---|
| Explore | Fast codebase search across many files in parallel | Yes — dedicated Explore agent | Yes — background agent |
| Plan | Design implementation strategies for complex changes | Yes — dedicated Plan agent | Yes — background agent |
| general-purpose | Handle multi-step research or complex tasks autonomously | Yes — dedicated agent type | Yes — background agent |

---

## Recommended Workflow

This workflow is the same regardless of which tool you use:

```
/plan          →  align on approach, search for existing solutions
                  ↓
(write code)   →  skills activate automatically
                  ↓
/verify        →  does my code work? (tests, outputs)
                  ↓
/review        →  check code quality and security
                  ↓
/quality-gate  →  am I safe to push? (tests + secrets + lint)
                  ↓
git push       →  secret scan hook runs automatically (Claude Code)
                  /quality-gate covers this for Cursor users
                  ↓
/recap         →  summarize for standup or stakeholders
```

---

## Tool-Specific Notes

### Claude Code

- All hooks are active (session start, secret scan, skill suggestion)
- Skills live in `skills/*/SKILL.md` and are loaded by the agent when relevant
- Run `claude` in the workspace root to start

### Cursor

- Session start hook is active (reports repo status)
- Skills live in `.cursor/rules/*.mdc` — some auto-attach based on file type (Python files, test files, config files), others are picked by the agent based on the description
- No pre-commit secret scan hook — **always run `/quality-gate` before pushing**
- Open the workspace folder in Cursor to start
