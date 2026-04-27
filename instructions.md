# Getting Started with the AI Workspace

Welcome! This workspace gives you superpowers when working with AI coding assistants. It supports both **Claude Code** and **Cursor** — same skills, same commands, same workflow.

---

## Setup

1. **Clone the workspace**, install dependencies, and run setup:
   ```bash
   git clone <workspace-repo-url>
   cd ai-workspace-template-ds
   uv sync
   uv run .ai-workspace/scripts/setup.py
   ```
   Setup installs pre-commit hooks and validates the workspace. Safe to re-run.

2. **Clone your repo** into the `repositories/` folder:
   ```bash
   cd repositories/
   git clone <your-repo-url>
   cd ..
   ```

3. **Start your AI tool** in the workspace root:

   | Tool | How to start |
   |---|---|
   | Claude Code | Run `claude` in the terminal |
   | Cursor | Open the workspace folder in Cursor |

4. **Tell the AI which repo to focus on** — e.g., "work on site-analysis" or type `/focus` to pick from a list.

5. **Type `/toolkit`** to see what's available and get recommendations based on your current repo.

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

| Name | Purpose | Example | How it works backstage |
|---|---|---|---|
| python-conventions | Team dotenv conventions, API client rules, LLM response parsing, TDD workflow, pytest patterns | You write `os.getenv("API_KEY", "AIza...")` — the AI flags the real key in the default and fixes it | Loaded into context when you edit Python files or API client code. ~480 words. |
| security-check | Credential leak detection (Gemini, Jira, AWS keys), insecure code (eval, pickle, shell injection), LLM-specific risks | You send raw email addresses to Gemini — the AI flags PII leakage and suggests sanitizing | Loaded when you edit code that touches credentials, APIs, or security-sensitive patterns. Also runs as a git hook before commit/push. ~1,020 words. |
| data-pipeline-patterns | Pipeline stage design, data validation, circuit breakers, checkpoint/resume, debugging | You add a new pipeline step — the AI structures it with validation, checkpoints, and a circuit breaker | Loaded when you work on pipeline scripts or data processing code. Teaches team-specific stage structure. ~908 words. |
| verification-loop | Unified engine behind `/verify`, `/review`, `/quality-gate` — environment, types, lint, tests, review, security | You run `/review` — the AI checks for bare excepts, long functions, data leakage | Loaded only when you invoke /verify, /review, or /quality-gate. Powers all three commands. ~503 words. |
| brainstorming | Design exploration before implementation — asks questions, proposes approaches, presents design for approval | You say "I want to add retry logic" — the AI asks about failure modes, proposes approaches, writes a spec | Loaded when creative/design work is detected. Hard gate prevents coding before design approval. ~332 words. |
| writing-plans | Creates implementation plans from approved specs — bite-sized tasks, exact file paths, TDD steps | The AI produces: "Task 1: write failing test, Task 2: implement, Task 3: verify..." | Loaded after brainstorming completes or when you need a detailed plan. ~914 words. |

**On-demand docs (agent-docs/):** These are NOT loaded every session. The AI reads them only when the task requires it — saving tokens for normal work.

| Name | Purpose | How it works backstage |
|---|---|---|
| mcp-patterns | Building and securing MCP servers | Read on demand when you're building MCP servers. Not loaded otherwise. ~781 words saved per session. |
| deep-research | Multi-source research with citations | Read on demand when you ask for thorough research. ~706 words saved. |
| codebase-onboarding | Systematic onboarding to unfamiliar codebases | Read on demand when you're exploring a new repo. ~637 words saved. |
| writing-skills | TDD methodology for creating new skills | Read on demand when you're extending the workspace. ~3,249 words saved. |
| subagent-driven-development | Dispatching subagents per task with two-stage review | Read on demand for complex multi-task implementations. ~1,567 words saved. |

---

## Commands (you trigger these)

Type the command name in the chat to run it. Commands work the same in both Claude Code and Cursor.

| Name | Purpose | Example | How it works backstage |
|---|---|---|---|
| /plan | Restate requirements, identify risks, create step-by-step plan. Waits for OK before coding | "Add retry logic to the pipeline" — proposes a plan, waits for approval | Loads the command markdown (~387 words) into context only when invoked. |
| /verify | Run environment, types, lint, tests | After coding — catch type errors and failing tests | Invokes the verification-loop skill, runs phases 1-4. Exits after tests. |
| /review | Code review with security and DS anti-pattern checks | Checks for bare excepts, data leakage, long functions | Invokes verification-loop phase 5 only. Produces APPROVE or REQUEST CHANGES. |
| /quality-gate | Pre-push safety check: tests + secret scan + pre-commit | Before pushing — confirms no secrets leaked, tests pass | Invokes verification-loop phases 1-4 + 6. Skips code review. |
| /commit | Generate commit message from diff, show preview, commit after approval | Type `/commit` → get "Add exponential backoff to Jira API client" | Reads git diff, analyzes changes, drafts message. Never commits without your approval. |
| /test-coverage | Analyze coverage, find untested code, generate missing tests | Finds 3 core functions with no tests, marks them HIGH priority | Runs pytest --cov, analyzes output, generates test files targeting gaps. |
| /focus | Switch which repo(s) to focus on mid-session | `/focus` → pick repos from numbered list | Re-presents the repo selection menu. Completely replaces previous focus. |
| /toolkit | Show all skills, commands, agents. Recommends based on current context | Type in a new repo — get tailored recommendations | Scans the repo type, recent changes, and project structure to suggest relevant tools. |
| /recap | Summarize session — what changed, why, key decisions. Copy-pasteable | Get a structured standup update after a long session | Reads git log, diffs, and conversation history to generate summary. |
| /diff-explain | Explain changes grouped by intent, not file count | "Pipeline was split into 3 steps" instead of "14 files changed" | Reads git diff, groups changes by purpose, explains the "why" not the "what". |
| /ai-engineer-review | Brutally honest architecture/code/security review | `/ai-engineer-review security` — focused security audit | Spawns parallel agents to read all skills, commands, source files. Produces scored assessment. |
| /refactor-safe | Refactor internals without changing public API | 65-line handler → extracted helpers, same signature | Documents the public API first, then refactors. Verifies API unchanged after. |
| /env-check | Validate local environment: Python, deps, env vars, config, hooks | "GOOGLE_API_KEY missing, pre-commit not installed" | Checks each component independently, reports pass/fail with fix instructions. |
| /explain-simple | Explain a file or folder like you're 15 — no jargon | "This script downloads work tickets from Jira..." | Reads the target, rewrites explanation with analogies, no code, under 200 words. |
| /explain-code | Explain code from high-level to line-by-line, scaled to complexity | Purpose, structure, data flow, gotchas for a pipeline file | Reads imports, call patterns, and usage to build layered explanation. |
| /prompt-test | Test LLM prompts against sample inputs, catch regressions | Runs prompt with 3 inputs, flags hallucinations on sparse data | Calls the prompt function, optionally calls the LLM, evaluates output quality. |
| /architecture-docs | Generate architecture docs with Mermaid diagrams | System overview, data flow, design decisions | Full mode: scans project, generates comprehensive docs. `--quick`: just a Mermaid diagram. |

---

## Agents (automatic)

The AI spawns these as sub-processes for parallel or specialized work.

| Name | Purpose | Claude Code | Cursor |
|---|---|---|---|
| Explore | Fast codebase search across many files in parallel | Yes — dedicated Explore agent | Yes — background agent |
| Plan | Design implementation strategies for complex changes | Yes — dedicated Plan agent | Yes — background agent |
| general-purpose | Handle multi-step research or complex tasks autonomously | Yes — dedicated agent type | Yes — background agent |

---

---

## Credential Hygiene

Claude Code accumulates permission entries in `.claude/settings.local.json` as you approve commands. If you approve a `curl` command with a token in it, that token gets saved in plaintext on disk. This file is gitignored, but the habit is still dangerous.

**Rules:**
- **Never approve curl commands with inline tokens.** Instead, use environment variables: `curl -H "Authorization: Bearer $MY_TOKEN"` not `curl -H "Authorization: Bearer ghp_abc123..."`.
- **Periodically clean your settings.local.json.** Search for `PRIVATE-TOKEN`, `Bearer`, or `Authorization` and remove any entries with real tokens. Replace with the broad `"Bash(curl *)"` permission.
- **Rotate tokens if they've been in settings.local.json.** Treat any token that was saved in plaintext as potentially compromised.
- **The secret scan hook only protects git.** It blocks commits/pushes with API key patterns in tracked files, but it doesn't prevent tokens from landing in untracked local config files.

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
