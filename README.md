# Claude Code Setup Evaluator

A workspace for Claude Code users who work across multiple repositories. Clone your repos, get shared skills and commands out of the box, add your own — and use `/evaluate-setup` to make sure your setup is actually helping.

## How It Works

This is a **meta-workspace**. You clone your project repositories into the `repositories/` folder and run Claude Code from the workspace root. Claude automatically gets access to all skills and commands. Your repos stay independent — they push to their own remotes, the workspace never touches them.

```
claude-code-setup-evaluator/
  repositories/           # Clone your repos here (gitignored — yours, not shared)
    my-api/
    frontend/
    data-pipeline/
  skills/                 # AI skills — activate automatically when relevant
  commands/               # Slash commands — you trigger with /command
  .claude/                # Claude Code hooks and config
  scripts/evaluate-setup/ # The evaluator engine
```

## Quick Start

```bash
git clone https://github.com/redhat-community-ai-tools/claude-code-setup-evaluator.git
cd claude-code-setup-evaluator
uv sync
uv run .ai-workspace/scripts/setup.py

# Clone your repos
cd repositories/
git clone <your-repo-url>
cd ..

# Start working
claude
```

Tell Claude which repo to focus on — "I'm working on my-api" or type `/focus` to pick from a list. Skills activate automatically. Commands are there when you need them.

## What You Get

### Skills (activate automatically)

Skills are knowledge that Claude carries in the background. You don't trigger them — they activate when relevant to what you're doing.

| Skill | What it does |
|-------|-------------|
| `security-check` | Detects credential leaks, insecure patterns, LLM-specific risks |
| `python-conventions` | Dotenv conventions, API client rules, TDD workflow |
| `data-pipeline-patterns` | Pipeline stage design, validation, circuit breakers |
| `verification-loop` | Powers `/verify`, `/review`, `/quality-gate` |
| `brainstorming` | Design exploration before implementation |
| `writing-plans` | Creates implementation plans from approved specs |

### Commands (you trigger these)

| Command | When to use | What it does |
|---------|-------------|-------------|
| `/evaluate-setup` | Anytime | Evaluate your entire Claude Code setup (see below) |
| `/plan` | Before coding | Design approach, wait for your OK |
| `/verify` | After coding | Check types, lint, tests |
| `/review` | Before pushing | Code review with security checks |
| `/quality-gate` | Before `git push` | Tests + secret scan |
| `/commit` | Ready to commit | Generate message, preview, approve |
| `/refactor-safe` | After review | Refactor without changing public API |
| `/test-coverage` | Adding tests | Find untested code, generate tests |
| `/diff-explain` | Reviewing changes | Explain by intent, not file count |
| `/explain-code` | Unfamiliar code | Layered explanation scaled to complexity |
| `/explain-simple` | Non-technical audience | Plain language, no jargon |
| `/prompt-test` | Editing LLM prompts | Test against samples, catch regressions |
| `/ai-engineer-review` | Architecture check | Brutally honest review |
| `/architecture-docs` | Documentation | Architecture docs with Mermaid diagrams |
| `/env-check` | Something broke | Validate environment setup |
| `/recap` | End of session | Summarize for standup |
| `/focus` | Switch repos | Pick repos from a list |
| `/toolkit` | Discovery | See everything available |

### Hooks (automatic safety nets)

| Hook | What it does |
|------|-------------|
| Session start | Reports git status of all your repos |
| Secret scan | Blocks `git commit`/`push` if API keys detected in tracked files |
| Skill suggestion | Reminds Claude which skills are relevant to files you're editing |

## Adding Your Own Skills and Commands

You can extend the workspace with your own skills and commands:

- **Add a skill** — Create a folder in `skills/` with a `SKILL.md` file. Claude picks it up automatically.
- **Add a command** — Create a folder in `commands/` with a `command.md` file. It becomes a `/command` you can type.

After adding, run `/evaluate-setup` to check that your new skill or command meets quality standards.

## The Evaluator (`/evaluate-setup`)

The built-in evaluation command checks whether your skills, commands, CLAUDE.md, and hooks are actually helping — or wasting context and making Claude worse.

**Layer 1 — Static Analysis.** A rule engine with 15 rules scans for mechanical issues: missing descriptions, broken references, duplicate content, prompt injection patterns, token budget violations.

**Layer 2 — AI Review.** Claude scores each item on a structured rubric (5 dimensions, 1-5 scale) and suggests cross-type optimizations — e.g., "this skill should be a hook" or "move this from CLAUDE.md to a skill."

**Layer 3 — A/B Testing** (optional, `--deep`). Tests whether skills actually change Claude's behavior by running tasks with and without each skill and judging the difference.

```
You: /evaluate-setup

Claude: What do you want to evaluate?
        > Everything / Skills only / A specific item

        ## Evaluation Summary
        Your setup is solid. Found 1 issue that needs attention.
        Reviewed 6 skills, 17 commands, CLAUDE.md. Total: 8,234 tokens (4%).

        Suggestions:
          1. Remove clean-code-guide skill (100% redundant with Claude defaults)
```

> **Note:** `skills/clean-code-guide` and `commands/check-code` are intentionally low-quality examples included for testing the evaluator. Run `/evaluate-setup` to see how they get flagged.

## Cursor Support

The `main` branch is Claude Code only. For Claude Code + Cursor support, see the [`multi-tool`](../../tree/multi-tool) branch.

## Learn More

- [`GUIDE.md`](GUIDE.md) — Full reference for all skills, commands, and hooks
- [`docs/spec.md`](docs/spec.md) — Full evaluator specification

## Credits

Built on top of [ai-workspace-template](https://github.com/MichaelYochpaz/ai-workspace-template) by Michael Yochpaz.
