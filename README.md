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
| `systematic-debugging` | 4-phase root cause analysis: reproduce, isolate, hypothesize, verify |
| `refactoring-patterns` | Measurement-driven refactoring with before/after metrics |
| `verification-loop` | Powers `/verify`, `/quality-gate` |
| `brainstorming` | Design exploration before implementation |
| `writing-plans` | Creates implementation plans from approved specs |

### Commands (you trigger these)

| Command | When to use | What it does |
|---------|-------------|-------------|
| `/evaluate-setup` | Anytime | Evaluate your entire Claude Code setup (see below) |
| `/evaluate-skill` | Testing a skill | Deep-evaluate one skill with A/B testing (see below) |
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

After adding, run `/evaluate-setup` to check that your new skill or command meets quality standards, then `/evaluate-skill` on the new skill to A/B test it.

## The Evaluator

Two commands for two different jobs:

### `/evaluate-setup` — Health check for your entire setup

Evaluates all skills, commands, CLAUDE.md, and hooks together. Always evaluates everything — no scope selection needed.

**Layer 1 — Static Analysis.** A rule engine with 21 rules across 5 file types (skills, commands, CLAUDE.md, hooks, agents) scans for mechanical issues: missing descriptions, broken references, duplicate content, prompt injection patterns, token budget violations, credential access.

**Layer 2 — AI Review.** Claude scores each item on a structured rubric (5 dimensions, 1-5 scale) and suggests cross-type optimizations — e.g., "this skill should be a hook" or "move this from CLAUDE.md to a skill."

```
You: /evaluate-setup

Claude: Where do you want the report? > Terminal / File

        ## Evaluation Summary
        Your setup is solid. Found 1 issue that needs attention.
        Reviewed 9 skills, 17 commands, CLAUDE.md. Total: 2,690 tokens (1.3%).

        Suggestions:
          1. Add "Use when" prefix to 3 skill descriptions
```

### `/evaluate-skill` — Deep-evaluate a single skill

Runs all 3 layers on one skill to determine if it earns its place. Pick a skill from the list and get static analysis + contextual rubric scoring + A/B testing.

**Layer 3 — A/B Testing** (requires `GOOGLE_API_KEY`). Gemini generates 3 tasks on your actual repos. Claude runs each task twice — once with all skills except the tested one, once with it. Gemini judges the difference. Answers: "does this skill add value beyond what other skills already provide?"

```
You: /evaluate-skill python-conventions

Claude: Layer 1: 0 errors, 1 warning
        Layer 2: ★★★★★ KEEP — specific team conventions Claude doesn't know
        Layer 3: KEEP (2W/0L/1T) — skill made a measurable difference
        Final:   KEEP
```

## Cursor Support

The `main` branch is Claude Code only. For Claude Code + Cursor support, see the [`multi-tool`](../../tree/multi-tool) branch.

## Learn More

- [`GUIDE.md`](GUIDE.md) — Full reference for all skills, commands, and hooks
- [`docs/spec.md`](docs/spec.md) — Full evaluator specification
- [`docs/HOW-EVALUATE-SETUP-WORKS.md`](docs/HOW-EVALUATE-SETUP-WORKS.md) — How /evaluate-setup works (plain language)
- [`docs/HOW-EVALUATE-SKILL-WORKS.md`](docs/HOW-EVALUATE-SKILL-WORKS.md) — How /evaluate-skill works (plain language)

## Credits

Built on top of [ai-workspace-template](https://github.com/MichaelYochpaz/ai-workspace-template) by Michael Yochpaz.
