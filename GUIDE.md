# Guide

Everything this workspace gives you — skills, commands, hooks, and how they work together.

---

## Setup

1. **Clone the workspace**, install dependencies, and run setup:
   ```bash
   git clone https://github.com/redhat-community-ai-tools/claude-code-setup-evaluator.git
   cd claude-code-setup-evaluator
   uv sync
   uv run .ai-workspace/scripts/setup.py
   ```
   Setup installs pre-commit hooks and validates the workspace. Safe to re-run.

2. **Clone your repos** into the `repositories/` folder:
   ```bash
   cd repositories/
   git clone <your-repo-url>
   cd ..
   ```

3. **Start Claude Code** from the workspace root:
   ```bash
   claude
   ```

4. **Tell Claude which repo to focus on** — e.g., "work on my-project" or type `/focus` to pick from a list.

5. **Type `/toolkit`** to see what's available and get recommendations.

> **Note:** Your cloned repos are gitignored — they belong to you, not the workspace. Push changes from inside the repo folder.

---

## Start Here

Your daily workflow in 3 commands:

```
/verify        → after coding, check it works
/review        → code review
/quality-gate  → before pushing
```

Everything else is available when you need it. Skills activate automatically.

---

## Skills (automatic)

Skills activate on their own — you just get better results. They live in `skills/*/SKILL.md` and are loaded by Claude when relevant.

| Skill | Purpose | When it activates |
|-------|---------|-------------------|
| `python-conventions` | Dotenv conventions, API client rules, LLM response parsing, TDD workflow, pytest patterns | When you edit Python files or API client code |
| `security-check` | Credential leak detection (API keys for GitHub, Stripe, AWS, etc.), insecure code patterns (eval, pickle, shell injection), LLM-specific risks | When you edit code that touches credentials, APIs, or security-sensitive patterns |
| `data-pipeline-patterns` | Pipeline stage design, data validation, circuit breakers, checkpoint/resume, debugging | When you work on pipeline scripts or data processing code |
| `systematic-debugging` | 4-phase root cause analysis — reproduce, isolate, hypothesize, verify. 3-strikes escalation rule. | When a test fails, an error appears, or a previous fix didn't work |
| `refactoring-patterns` | Measurement-driven refactoring — profile before, measure after, keep only if metrics improve. Bulk mode for 10+ files. | When you say "refactor", "clean up", or code has high complexity |
| `verification-loop` | Unified engine behind `/verify`, `/review`, `/quality-gate` — environment, types, lint, tests, review, security | When you invoke /verify, /review, or /quality-gate |
| `brainstorming` | Design exploration before implementation — asks questions, proposes approaches, presents design for approval | When creative/design work is detected |
| `writing-plans` | Creates implementation plans from approved specs — bite-sized tasks, exact file paths, TDD steps | After brainstorming completes or when you need a detailed plan |

### On-demand docs (agent-docs/)

These are NOT loaded every session. Claude reads them only when the task requires it — saving tokens for normal work.

| Doc | Purpose |
|-----|---------|
| `mcp-patterns` | Building and securing MCP servers |
| `deep-research` | Multi-source research with citations |
| `codebase-onboarding` | Systematic onboarding to unfamiliar codebases |
| `writing-skills` | TDD methodology for creating new skills |
| `subagent-driven-development` | Dispatching subagents per task with two-stage review |

---

## Commands (you trigger these)

Type the command name in the chat to run it.

| Command | When | What it does |
|---------|------|-------------|
| `/evaluate-setup` | Anytime | Evaluates your entire Claude Code setup — skills, commands, CLAUDE.md, hooks |
| `/evaluate-skill` | Testing a skill | Deep-evaluates one skill with L1+L2+L3 (including A/B testing) |
| `/verify` | After coding | Checks if your code works (types, lint, tests) |
| `/review` | Before pushing | Code review with security and anti-pattern checks |
| `/quality-gate` | Right before `git push` | Pre-push safety check (tests + secret scan) |
| `/refactor-safe` | After review | Refactors internals without changing public API |
| `/test-coverage` | When adding tests | Finds untested code and generates missing tests |
| `/env-check` | First clone / something broke | Validates Python version, dependencies, env vars, config |
| `/recap` | End of session | Summarizes what you did — copy-paste for standup |
| `/diff-explain` | Reviewing changes | Explains a branch's changes by intent, not file count |
| `/explain-code` | Onboarding / unfamiliar code | Explains code at the right level of detail |
| `/explain-simple` | Non-technical audience | Explains a file or folder like you're 15 — no jargon |
| `/prompt-test` | After editing LLM prompts | Tests prompts against sample inputs, checks quality, catches regressions |
| `/ai-engineer-review` | Architecture check | Brutally honest architecture and code review |
| `/architecture-docs` | Documentation | Generates architecture docs with diagrams (`--quick` for just a Mermaid diagram) |
| `/focus` | Switch repos mid-session | Re-presents the repo menu, replaces current focus |
| `/toolkit` | First time / discovery | Shows everything available and recommends what to use |

---

## Hooks (automatic safety nets)

Hooks fire on specific events — you don't trigger them manually.

| Hook | Event | What it does |
|------|-------|-------------|
| Session start | When Claude starts | Reports git status of all repos in `repositories/` |
| Secret scan | Before `git commit` or `git push` | Blocks if API keys detected in tracked files (GitHub, AWS, Anthropic, Atlassian, HuggingFace patterns) |
| Skill suggestion | When you edit files | Reminds Claude which skills are relevant to the files you're working on |

The secret scan hook catches these patterns:
- `AIzaSy...` (Google API keys)
- `sk-...` (OpenAI keys)
- `sk-ant-...` (Anthropic keys)
- `ATATT3x...` (Atlassian tokens)
- `AKIA...` (AWS access keys)
- `ghp_...` (GitHub personal tokens)
- `hf_...` (HuggingFace tokens)

---

## The Evaluator

Two commands for two different jobs:

### `/evaluate-setup` — Health check for the whole setup

Evaluates all skills, commands, CLAUDE.md, and hooks together. Always evaluates everything.

**Layer 1 — Static Analysis:** A rule engine with 15 rules checks for mechanical issues (missing descriptions, broken references, token budget violations, prompt injection patterns, duplicate content).

**Layer 2 — AI Review:** Claude scores each item on a 5-dimension rubric, suggests cross-type optimizations (e.g., "this skill should be a hook"), and produces numbered suggestions you can act on.

**Typical workflow:** Run this first to get the overview. Takes ~2 minutes.

### `/evaluate-skill` — Deep-evaluate one skill

Runs all 3 layers on a single skill to determine if it earns its place:

- **Layer 1** — Same static analysis, focused on this skill
- **Layer 2** — Scores the skill individually AND in context of all other skills/CLAUDE.md (overlap, conflicts, type appropriateness)
- **Layer 3 — A/B Testing** (requires `GOOGLE_API_KEY` in `.env`): Gemini generates 3 tasks on your actual repos. Claude runs each task twice — with all skills except this one, and with it included. Gemini judges whether the skill made a difference. Tasks with poor test quality are automatically excluded from the verdict.

**Typical workflow:** Run this on any skill you're unsure about, or after creating a new skill. Takes ~5 minutes.

See [docs/spec.md](docs/spec.md) for the full specification.

---

## Credential Hygiene

Claude Code accumulates permission entries in `.claude/settings.local.json` as you approve commands. If you approve a `curl` command with a token in it, that token gets saved in plaintext on disk. This file is gitignored, but the habit is still dangerous.

**Rules:**
- **Never approve curl commands with inline tokens.** Use environment variables: `curl -H "Authorization: Bearer $MY_TOKEN"`
- **Periodically clean your settings.local.json.** Search for `PRIVATE-TOKEN`, `Bearer`, or `Authorization` and remove entries with real tokens.
- **Rotate tokens if they've been in settings.local.json.** Treat any token saved in plaintext as potentially compromised.
- **The secret scan hook only protects git.** It blocks commits/pushes with API key patterns, but doesn't prevent tokens from landing in untracked local config files.

---

## Contributing

- **Add a skill** — Add it to `skills/` following the [Agent Skills spec](https://agentskills.io/specification)
- **Add a command** — Add it to `commands/` with a `command.md` file
- **Add a rule** — Extend the evaluator in `scripts/evaluate-setup/src/the_evaluator/rules/`
- **Add docs** — Add to `agent-docs/` for on-demand documentation

After making changes, run:
```bash
uv run .ai-workspace/scripts/align-workspace.py
```
