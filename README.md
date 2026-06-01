# Claude Code Setup Evaluator

A workspace for Claude Code users who work across multiple repositories. Clone your repos, get shared skills and commands out of the box, add your own.

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
| `refactoring-patterns` | Measurement-driven refactoring with before/after metrics |
| `verification-loop` | Powers `/verify`, `/quality-gate` |
| `brainstorming` | Design exploration before implementation |

### Commands (you trigger these)

| Command | When to use | What it does |
|---------|-------------|-------------|
| `/verify` | After coding | Check types, lint, tests |
| `/quality-gate` | Before `git push` | Tests + secret scan |
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

After adding, Claude picks them up automatically.

## Learn More

- [`GUIDE.md`](GUIDE.md) — Full reference for all skills, commands, and hooks

## Credits

Built on top of [ai-workspace-template](https://github.com/MichaelYochpaz/ai-workspace-template) by Michael Yochpaz.
