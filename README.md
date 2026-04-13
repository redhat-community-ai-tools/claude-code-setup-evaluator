# AI Workspace — Data Science Team

A shared workspace for using AI coding assistants (Claude Code, Cursor) consistently across our team's projects. One place for all our AI instructions, skills, commands, and conventions — so every team member gets the same quality of AI assistance from day one.

## Why This Exists

AI assistants work great in a single repo, but our team works across multiple projects with shared conventions. Without a shared setup, everyone reinvents the wheel — writing their own prompts, missing best practices, and getting inconsistent results. This workspace solves that by giving every team member:

- **Shared skills** — team knowledge baked into the AI (dotenv patterns, pipeline design, security checks, TDD workflows, and more)
- **Shared commands** — `/verify`, `/review`, `/quality-gate`, `/plan`, `/refactor-safe`, `/recap` and more — the same workflows everywhere
- **Cross-repo visibility** — all our repos in one workspace, so the AI can see and work across project boundaries
- **Onboarding in minutes** — new team members (or new repos) get the full AI setup immediately

## Setup (one time)

```bash
# Clone the workspace
git clone git@gitlab.cee.redhat.com:bkapner/ai-workspace-template-ds.git
cd ai-workspace-template-ds

# Install dependencies
uv sync

# Clone whatever repos you work on
cd repositories/
git clone git@gitlab.cee.redhat.com:bkapner/site-analysis.git
git clone git@gitlab.cee.redhat.com:bkapner/ai-initiatives-observer.git
cd ..
```

Your cloned repos are yours — the workspace doesn't track them. Other team members clone different repos into the same folder.

## Daily Workflow

**1. Start Claude Code from the workspace root:**
```bash
cd ai-workspace-template-ds
claude
```

Starting from the root loads all the skills and commands.

**2. Tell Claude which repo to focus on:**
> "I'm working on site-analysis today"

or just start asking about it:
> "Run the tests in site-analysis"

**3. Work normally.** Skills activate automatically in the background — you don't need to do anything. When you write Python, Claude already knows your team's dotenv conventions, testing patterns, security rules, and pipeline design patterns.

**4. Use commands as you work:**

| Command | When | What it does |
|---------|------|-------------|
| `/plan` | Before coding anything complex | Designs the approach, waits for your OK before writing code |
| `/verify` | After coding | Checks if your code works (types, lint, tests) |
| `/review` | Before pushing | Code review with security and DS anti-pattern checks |
| `/quality-gate` | Right before `git push` | Pre-push safety check (tests + secret scan) |
| `/commit` | When ready to commit | Generates a good commit message, shows preview, you approve |
| `/refactor-safe` | After review | Refactors internals without changing public API |
| `/test-coverage` | When adding tests | Finds untested code and generates missing tests |
| `/env-check` | First clone / something broke | Validates Python version, dependencies, env vars, config |
| `/recap` | End of session | Summarizes what you did — copy-paste for standup |
| `/diff-explain` | Reviewing changes | Explains a branch's changes by intent, not file count |
| `/explain-code` | Onboarding / unfamiliar code | Explains code at the right level of detail |
| `/explain-simple` | Non-technical audience | Explains a file or folder like you're 15 — no jargon |
| `/prompt-test` | After editing LLM prompts | Tests prompts against sample inputs, checks quality, catches regressions |
| `/ai-engineer-review` | Architecture check | Brutally honest architecture and code review |
| `/architecture-docs` | Documentation | Generates architecture docs with diagrams |
| `/toolkit` | First time / discovery | Shows everything available and recommends what to use |
| `/visualize` | Exploring a project | Interactive HTML map of the project structure |

**5. Push from inside the repo:**
```bash
cd repositories/site-analysis
git push origin my-branch
```

Pushes go to the repo's own remote. The workspace is never involved.

## What You DON'T Need To Do

- **Don't memorize skills.** There are 8 of them (security, pipelines, testing, etc.) — they activate automatically when relevant. You just get better results without thinking about it.
- **Don't configure anything per-repo.** The workspace handles it.
- **Don't worry about pushing to the wrong repo.** Your repos are independent clones. `git push` from inside a repo goes to that repo's remote.

## Example Session

```
$ cd ai-workspace-template-ds
$ claude

You: I'm working on site-analysis. Add retry logic to the Jira fetcher.

Claude: [reads the code, uses api-client-patterns skill automatically]
        Let me plan this first...
        [proposes approach with exponential backoff]

You: /plan looks good, go ahead

Claude: [implements, uses python-testing skill to write tests first]

You: /verify

Claude: Types OK, Lint OK, 72 tests pass

You: /commit

Claude: "Add exponential backoff retry to Jira API client"
        Files: scripts/fetch_jira_data.py, tests/test_fetch_jira.py
        Proceed? [y/n]

You: y

You: /recap

Claude: ## What was done
        - Added retry with exponential backoff to Jira fetcher
        - Handles 429/500/502/503 with Retry-After header support
        - Added 4 tests covering retry, backoff, and rate limit scenarios

        ## Ready To Share
        Added retry logic to Jira API client - handles rate limits
        and transient failures with exponential backoff. 4 new tests.
        commit abc1234
```

## What's Inside

| Directory | What it is |
|---|---|
| `repositories/` | Your repos — clone what you need here |
| `skills/` | 8 AI skills — team patterns, security, testing, pipelines, and more |
| `commands/` | 17 slash commands — `/plan`, `/verify`, `/review`, `/quality-gate`, etc. |
| `agent-docs/` | On-demand documentation the AI reads when relevant (writing skills guide, subagent development, etc.) |
| `.cursor/rules/` | Same skills, formatted for Cursor |
| `.cursor/commands/` | Same commands, formatted for Cursor |

See [`instructions.md`](instructions.md) for the full list of skills, commands, and how each one works.

## Supported Tools

| Tool | Skills | Commands | Hooks |
|---|---|---|---|
| **Claude Code** | `skills/*/SKILL.md` | `.claude/commands/` | Session start, secret scan, skill suggestion |
| **Cursor** | `.cursor/rules/*.mdc` | `.cursor/commands/` | Session start |

## Contributing

This workspace gets better when the team contributes. You can:

- **Add a skill** — learned a pattern that would help others? Add it to `skills/`
- **Add a command** — have a workflow you repeat? Make it a `/command` in `commands/`
- **Add docs** — know something the AI should know? Add it to `agent-docs/`
- **Add your repo** — clone it into `repositories/`

After making changes, run the alignment script to keep everything in sync:
```bash
uv run .ai-workspace/scripts/align-workspace.py
```

## Learn More

- [`instructions.md`](instructions.md) — Full guide with all skills, commands, and workflows
- [`CLAUDE.md`](CLAUDE.md) — What the AI reads at session start
- [AI Workspace Template docs](https://michaelyochpaz.github.io/ai-workspace-template/) — Upstream project documentation
