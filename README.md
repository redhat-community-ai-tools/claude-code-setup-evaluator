# Claude Code Setup Evaluator

A meta-workspace for Claude Code with a built-in 3-layer evaluator for your setup. Analyze your skills, commands, CLAUDE.md, and hooks for quality, redundancy, and optimization opportunities.

## What This Does

Most Claude Code users accumulate skills, commands, and configuration over time — but never check if they're actually helping. This workspace gives you:

- **`/evaluate-setup`** — A 3-layer evaluation command that scores your entire Claude Code setup
- **17 slash commands** — `/plan`, `/verify`, `/review`, `/commit`, `/evaluate-setup`, and more
- **6 built-in skills** — Security checks, Python conventions, pipeline patterns, TDD workflows
- **Cross-repo workspace** — Work across multiple repositories with shared AI capabilities

## The Evaluator (`/evaluate-setup`)

The core feature. Run `/evaluate-setup` in Claude Code and it evaluates your entire setup:

### Layer 1: Static Analysis (automated)
A rule engine with 15 pluggable rules scans your files for mechanical issues:
- Missing descriptions, broken file references, token budget violations
- Prompt injection patterns, credential access attempts
- Duplicate content detection across skills
- Command script integrity, CLAUDE.md bloat, dangerous hook patterns

### Layer 2: AI-Powered Review (Claude as judge)
Claude scores each item on a structured rubric (5 dimensions, 1-5 scale):
- **Skills**: specificity, redundancy, trigger quality, token efficiency, content quality
- **Commands**: description quality, instruction clarity, script integrity, scope, efficiency
- **CLAUDE.md**: conciseness, signal-to-noise, skill separation, structure, conflicts
- Cross-type optimization suggestions (e.g., "this skill should be a hook")

### Layer 3: A/B Testing (optional, `--deep`)
Tests whether your skills actually change Claude's behavior:
- Generates tasks, runs Claude with and without each skill, judges the difference
- Repeat-and-vote: 3 judge calls per comparison for reliability
- Red-team mode (`--deep --red-team`): adversarial testing for preventive skills

## Quick Start

```bash
# Clone the workspace
git clone https://github.com/redhat-community-ai-tools/claude-code-setup-evaluator.git
cd claude-code-setup-evaluator

# Install dependencies and set up hooks
uv sync
uv run .ai-workspace/scripts/setup.py

# Clone your repos into the workspace
cd repositories/
git clone <your-repo-url>
cd ..

# Start Claude Code
claude
```

Then run `/evaluate-setup` to evaluate your setup, or start working with the built-in commands.

## Commands

| Command | What it does |
|---------|-------------|
| `/evaluate-setup` | Evaluate your Claude Code setup (skills, commands, CLAUDE.md, hooks) |
| `/plan` | Design approach before coding, wait for approval |
| `/verify` | Check types, lint, and tests |
| `/review` | Code review with security checks |
| `/quality-gate` | Pre-push safety check (tests + secret scan) |
| `/commit` | Generate commit message, preview, approve |
| `/refactor-safe` | Refactor internals without changing public API |
| `/test-coverage` | Find untested code, generate missing tests |
| `/diff-explain` | Explain changes by intent, not file count |
| `/explain-code` | Layered code explanation scaled to complexity |
| `/explain-simple` | Explain code in plain language |
| `/prompt-test` | Test LLM prompts against sample inputs |
| `/ai-engineer-review` | Brutally honest architecture review |
| `/architecture-docs` | Generate architecture docs with Mermaid diagrams |
| `/env-check` | Validate local environment setup |
| `/recap` | Summarize session for standup |
| `/focus` | Switch repo focus mid-session |
| `/toolkit` | Show available capabilities |

## Skills (activate automatically)

| Skill | What it does |
|-------|-------------|
| `security-check` | Detects credential leaks, insecure patterns, LLM-specific risks |
| `python-conventions` | Dotenv conventions, API client rules, TDD workflow |
| `data-pipeline-patterns` | Pipeline stage design, validation, circuit breakers |
| `verification-loop` | Powers `/verify`, `/review`, `/quality-gate` |
| `brainstorming` | Design exploration before implementation |
| `writing-plans` | Creates implementation plans from approved specs |

> **Note:** `skills/clean-code-guide` and `commands/check-code` are intentionally low-quality examples included for testing the evaluator. Run `/evaluate-setup` to see how they get flagged.

## Project Structure

```
claude-code-setup-evaluator/
  .claude/                    # Claude Code hooks and distributed commands
  skills/                     # AI skills (auto-activate when relevant)
  commands/                   # Slash commands (user-triggered)
  agent-docs/                 # On-demand documentation
  scripts/
    evaluate-setup/           # The evaluator engine (Layer 1 + Layer 3)
  docs/
    spec.md                   # Full evaluator specification
  tests/                      # Test suite
  repositories/               # Your repos go here (gitignored)
```

## How It Works

This is a **meta-workspace** — you clone your project repos into the `repositories/` folder and run Claude Code from the workspace root. Claude gets access to all skills and commands automatically. Your repos push to their own remotes; the workspace is never involved.

```
$ claude

You: /evaluate-setup

Claude: Where do you want the full review?
        > Terminal / File

        What do you want to evaluate?
        > Everything / Skills only / A specific item

        [runs Layer 1 static analysis]
        [reads all files, scores each on rubric]
        [suggests cross-type optimizations]

        ## Evaluation Summary
        Your setup is solid. Found 1 issue that needs attention.
        Reviewed 6 skills, 17 commands, CLAUDE.md. Total: 8,234 tokens (4%).

        Suggestions:
          1. Remove clean-code-guide skill (100% redundant with Claude defaults)

        Full review: printed above
```

## Multi-Tool Support

The `main` branch is Claude Code only. For Cursor + Gemini + OpenCode support, see the [`multi-tool`](../../tree/multi-tool) branch.

## Contributing

- **Add a skill** — Add it to `skills/` following the [Agent Skills spec](https://agentskills.io/specification)
- **Add a command** — Add it to `commands/`
- **Add a rule** — Extend the evaluator in `scripts/evaluate-setup/src/the_evaluator/rules/`
- **Run `/evaluate-setup`** on your changes to make sure they pass

## Learn More

- [`GUIDE.md`](GUIDE.md) — Full guide with all skills, commands, hooks, and how each one works
- [`CLAUDE.md`](CLAUDE.md) — What Claude reads at session start
- [`docs/spec.md`](docs/spec.md) — Full evaluator specification

## Credits

Built on top of [ai-workspace-template](https://github.com/MichaelYochpaz/ai-workspace-template) by Michael Yochpaz.
