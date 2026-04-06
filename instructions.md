# Getting Started with the AI Workspace

Welcome! This workspace gives you superpowers when working with Claude Code. Here's how to get started and what's available to you.

---

## Setup

1. **Clone your repo** into the `repositories/` folder:
   ```bash
   cd repositories/
   git clone <your-repo-url>
   cd ../
   git submodule add <your-repo-url> repositories/<repo-name>
   ```

2. **Start Claude Code** in the workspace root:
   ```bash
   claude
   ```

3. **Type `/toolkit`** to see what's available and get recommendations based on your current repo.

That's it. Everything else activates automatically as you work.

---

## How It Works

This workspace has four types of capabilities:

- **Skills** — knowledge the AI carries. Activate automatically when relevant. You don't do anything.
- **Commands** — buttons you press. Type `/command` to trigger a specific workflow.
- **Agents** — helpers the AI sends to do work in parallel. You don't control them.
- **Hooks** — tripwires that fire on events (like blocking a push if secrets are detected).

---

## Skills (automatic)

Skills activate on their own — you just get better results.

| Name | Purpose | Example |
|---|---|---|
| python-patterns | Team dotenv conventions — `.env` structure, loading patterns, secure defaults | You write `os.getenv("API_KEY", "AIza...")` — the AI flags the real key in the default and fixes it to `os.getenv("API_KEY")` with a validation check |
| python-testing | TDD workflow (red/green/refactor), pytest patterns, data science testing (DataFrames, models) | You say "add a validation function" — the AI writes a failing test first with `pd.testing.assert_frame_equal`, then implements to make it pass |
| security-check | Credential leak detection (Gemini, OpenAI, Jira, AWS, GitHub keys), insecure code (eval, pickle, shell injection), LLM-specific risks | You send raw email addresses to Gemini — the AI flags PII leakage and suggests sanitizing before sending |
| data-pipeline-patterns | Pipeline stage design, data validation at boundaries, circuit breakers, checkpoint/resume, debugging workflow | You add a new pipeline step — the AI structures it with input validation, checkpoints every 100 items, and a circuit breaker after 5 consecutive API failures |
| api-client-patterns | Retry with exponential backoff, rate limiting, auth, pagination, LLM response parsing | You build a Jira API client — the AI adds `timeout=30`, retry for 429/500/502/503 with `Retry-After` support, and validates the response structure |
| git-workflow | GitLab/GitHub conventions, submodule push-before-parent pattern, common pitfalls | You push changes in a submodule — the AI pushes the submodule first, then updates the parent reference, following the correct order |
| mcp-patterns | Building/securing MCP servers — schema-first design, auth, input validation, audit logging, DS-specific patterns | You build an MCP tool for querying datasets — the AI enforces Pydantic input schemas with limits (`max_rows=10000`) and adds audit logging |
| verification-loop | Unified verification engine behind `/verify`, `/review`, `/quality-gate` — environment checks, types, lint, tests, code review, security scans | You say "review my changes" — the AI checks for bare `except` clauses, functions over 50 lines, data leakage, and gives APPROVE or REQUEST CHANGES |
| deep-research | Multi-source research — breaks questions into sub-queries, searches in parallel, synthesizes with citations | You ask "best Python library for HTML-to-PDF?" — the AI researches weasyprint, pdfkit, playwright, compares tradeoffs, and recommends one |
| codebase-onboarding | 4-phase analysis of unfamiliar codebases — reconnaissance, architecture mapping, convention detection, guide generation | You open a repo you've never seen — the AI maps the structure, identifies entry points, detects testing conventions, and produces a "start here" guide |
| compound-engineering | Captures reusable patterns from sessions — errors, corrections, workarounds — as persistent memories for future sessions | You spend 20 min debugging `.gitignore` negation — the AI saves "use `dir/*` not `dir/` for negation to work" so it knows next session |
| brainstorming | Collaborative design exploration before implementation — asks clarifying questions one at a time, proposes 2-3 approaches with trade-offs, presents design for approval, writes spec doc | You say "I want to add retry logic" — the AI asks about failure modes, proposes approaches (simple retry vs exponential backoff vs circuit breaker), presents a design, writes a spec, and only then moves to planning |
| writing-plans | Creates detailed implementation plans from approved specs — bite-sized tasks (2-5 min each), exact file paths, complete code blocks, TDD steps, no placeholders | The AI takes your approved design and produces a step-by-step plan: "Task 1: write failing test for X, Task 2: implement X, Task 3: write failing test for Y..." with full code in every step |
| subagent-driven-development | Executes implementation plans by dispatching a fresh subagent per task with two-stage review (spec compliance, then code quality) | You have a 5-task plan — the AI dispatches a subagent for Task 1, reviews its output against the spec, reviews code quality, then moves to Task 2. Each subagent gets isolated context so there's no pollution between tasks |
| writing-skills | Creates new AI skills using TDD for documentation — pressure-test baseline behavior, write skill, close loopholes | You want to add a "data-validation" skill — the AI first runs scenarios without the skill to see what agents get wrong, writes the skill to address those gaps, then re-tests until agents comply |

---

## Commands (you trigger these)

Type the command name in the chat to run it.

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
| /commit | Generate an accurate commit message from the diff + conversation context, show preview, commit after approval | You've been adding retry logic all session — type `/commit` and get "Add exponential backoff to Jira API client" with a body explaining why, not "update jira_client.py" |

---

## Agents (automatic)

The AI spawns these as sub-processes for parallel or specialized work.

| Name | Purpose | Example |
|---|---|---|
| Explore | Fast codebase search across many files in parallel | The AI needs to find all API endpoints — it spawns Explore to search the entire repo in seconds |
| Plan | Design implementation strategies for complex changes | You ask for a major refactor — the AI spawns Plan to map dependencies and propose an approach |
| general-purpose | Handle multi-step research or complex tasks autonomously | The AI needs to research a library, read its docs, and test compatibility — it spawns a general-purpose agent |

---

## Hooks (automatic)

These run in the background on specific events.

| Name | Purpose | Example |
|---|---|---|
| Session start | Reports git status of all submodules when you start a session | You open Claude Code — immediately see which repos have uncommitted changes or are behind remote |
| Pre-commit secret scan | Blocks `git commit`/`git push` if API keys are detected in tracked files | You accidentally stage a file with an API key — the hook blocks the commit and tells you which file |
| Auto-skill suggestion | Detects what files you're working with and reminds the AI which skills are relevant | You open a pipeline file — the AI is reminded to use `data-pipeline-patterns` and `security-check` |

---

## Recommended Workflow

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
git push       →  secret scan hook runs automatically
                  ↓
/recap         →  summarize for standup or stakeholders
```
