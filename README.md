# AI Workspace — Data Science Team

A shared workspace for using AI coding assistants (Claude Code, Cursor) consistently across our team's projects. One place for all our AI instructions, skills, commands, and conventions — so every team member gets the same quality of AI assistance from day one.

## Why This Exists

AI assistants work great in a single repo, but our team works across multiple projects with shared conventions. Without a shared setup, everyone reinvents the wheel — writing their own prompts, missing best practices, and getting inconsistent results. This workspace solves that by giving every team member:

- **Shared skills** — team knowledge baked into the AI (dotenv patterns, pipeline design, security checks, TDD workflows, and more)
- **Shared commands** — `/verify`, `/review`, `/quality-gate`, `/plan`, `/recap` — the same workflows everywhere
- **Cross-repo visibility** — all our repos as submodules, so the AI can see and work across project boundaries
- **Onboarding in minutes** — new team members (or new repos) get the full AI setup immediately

## Quick Start

```bash
# 1. Clone the workspace
git clone git@gitlab.cee.redhat.com:bkapner/ai-workspace-template-ds.git
cd ai-workspace-template-ds

# 2. Install dependencies
uv sync

# 3. Initialize submodules
git submodule update --init --recursive

# 4. Start your AI tool
claude                # Claude Code
# or open folder in Cursor

# 5. Type /toolkit to see what's available
```

To add your own repo:
```bash
git submodule add <repo-url> repositories/<repo-name>
```

## What's Inside

| Directory | What it is |
|---|---|
| `repositories/` | Team repos as git submodules |
| `skills/` | 15 AI skills — team patterns, security, testing, pipelines, and more |
| `commands/` | 13 slash commands — `/plan`, `/verify`, `/review`, `/quality-gate`, etc. |
| `agent-docs/` | Modular documentation the AI reads based on task relevance |
| `.cursor/rules/` | Same skills, formatted for Cursor |
| `.cursor/commands/` | Same commands, formatted for Cursor |
| `instructions.md` | Getting started guide for team members |

## Supported Tools

| Tool | Skills | Commands | Hooks |
|---|---|---|---|
| **Claude Code** | `skills/*/SKILL.md` | `.claude/commands/` | Session start, secret scan, skill suggestion |
| **Cursor** | `.cursor/rules/*.mdc` | `.cursor/commands/` | Session start |

See [`instructions.md`](instructions.md) for the full list of skills, commands, and how to use them.

## Contributing

This workspace gets better when the team contributes. You can:

- **Add a skill** — learned a pattern that would help others? Add it to `skills/`
- **Add a command** — have a workflow you repeat? Make it a `/command` in `commands/`
- **Add docs** — know something the AI should know? Add it to `agent-docs/`
- **Add your repo** — bring your project into the workspace as a submodule

After making changes, run the alignment script to keep everything in sync:
```bash
uv run .ai-workspace/scripts/align-workspace.py
```

## Learn More

- [`instructions.md`](instructions.md) — Full guide with all skills, commands, and workflows
- [`CLAUDE.md`](CLAUDE.md) — What the AI reads at session start
- [AI Workspace Template docs](https://michaelyochpaz.github.io/ai-workspace-template/) — Upstream project documentation
