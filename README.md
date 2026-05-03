# Claude Code Setup Evaluator — Multi-Tool Branch

A workspace for **Claude Code** and **Cursor** users who work across multiple repositories. Clone your repos, get shared skills and commands out of the box, add your own — and use `/evaluate-setup` to make sure your setup is actually helping.

> This is the `multi-tool` branch with Claude Code + Cursor support. For Claude Code only, see the [`main`](../../tree/main) branch.

## How It Works

This is a **meta-workspace**. You clone your project repositories into the `repositories/` folder and start your AI tool from the workspace root. Both tools automatically get access to all skills and commands. Your repos stay independent — they push to their own remotes, the workspace never touches them.

```
claude-code-setup-evaluator/
  repositories/           # Clone your repos here (gitignored — yours, not shared)
  skills/                 # AI skills — activate automatically when relevant
  commands/               # Slash commands — you trigger with /command
  .claude/                # Claude Code hooks and config
  .cursor/                # Cursor rules and commands
```

## Quick Start

```bash
git clone -b multi-tool https://github.com/redhat-community-ai-tools/claude-code-setup-evaluator.git
cd claude-code-setup-evaluator
uv sync
uv run .ai-workspace/scripts/setup.py

# Clone your repos
cd repositories/
git clone <your-repo-url>
cd ..
```

Then start your tool:

| Tool | How to start |
|------|-------------|
| **Claude Code** | Run `claude` in the terminal |
| **Cursor** | Open the workspace folder in Cursor |

## Claude Code vs Cursor — What's Different

Both tools get the same skills and commands, but the underlying mechanisms differ:

| Capability | Claude Code | Cursor |
|------------|------------|--------|
| **Skills** | `skills/*/SKILL.md` — loaded by Claude when relevant | `.cursor/rules/*.mdc` — some auto-attach by file type, others picked by description |
| **Commands** | `.claude/commands/*.md` — type `/command` in chat | `.cursor/commands/*.md` — type `/command` in chat |
| **Session start hook** | Reports git status of all repos | Reports git status of all repos |
| **Secret scan hook** | Blocks `git commit`/`push` if API keys detected | Not available — run `/quality-gate` manually before pushing |
| **Skill suggestion hook** | Reminds Claude which skills match your current files | Partial — rules with `globs` auto-attach when matching files are open |

## What You Get

### Skills (activate automatically)

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
| `/evaluate-setup` | Anytime | Evaluate your entire setup (skills, commands, CLAUDE.md, hooks) |
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

## Adding Your Own

- **Add a skill** — Create a folder in `skills/` with a `SKILL.md` file
- **Add a command** — Create a folder in `commands/` with a `command.md` file

After adding, run the alignment script to distribute to both tools:
```bash
uv run .ai-workspace/scripts/align-workspace.py
```

Then run `/evaluate-setup` to check quality.

## The Evaluator (`/evaluate-setup`)

Checks whether your skills, commands, CLAUDE.md, and hooks are actually helping — or wasting context.

**Layer 1 — Static Analysis.** 15 rules scan for mechanical issues: missing descriptions, broken references, duplicates, prompt injection, token budget violations.

**Layer 2 — AI Review.** Claude scores each item on a 5-dimension rubric and suggests optimizations.

**Layer 3 — A/B Testing** (optional, `--deep`). Tests whether skills actually change Claude's behavior.

> **Note:** `skills/clean-code-guide` and `commands/check-code` are intentionally low-quality examples for testing the evaluator.

## Learn More

- [`GUIDE.md`](GUIDE.md) — Full reference for all skills, commands, and hooks
- [`docs/spec.md`](docs/spec.md) — Full evaluator specification
- [`instructions.md`](instructions.md) — Detailed guide including Cursor-specific notes

## Credits

Built on top of [ai-workspace-template](https://github.com/MichaelYochpaz/ai-workspace-template) by Michael Yochpaz.
