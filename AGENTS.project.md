## Team

Data Science team at Red Hat. This workspace standardizes how we use AI coding assistants across the team.

## Repositories

Each team member clones the repos they work on into `repositories/`. This folder is gitignored — repos are personal, not shared. Common team repos include:

- `ai-initiatives-observer` — Pipeline that discovers AI-related work across the org by analyzing Jira tickets. Python, Gemini API.
- `site-analysis` — People & expertise discovery pipeline for geographic sites. Analyzes Jira activity to generate per-person work profiles. Python, Gemini API.
- `igloo-mcp` — MCP server for The Source (Igloo) intranet integration. Python.
- `il-agent` — Israel site agent service. Python.

Use `/focus` to select which repo(s) to work on in a session.

## Conventions (all repos)

- **Language**: Python 3.11+ (workspace), Python 3.10+ minimum (repos)
- **Testing**: pytest. Run tests before committing.
- **Secrets**: Never commit `.env` files, API keys, or tokens. Use environment variables.
- **Branches**: Work on feature branches, not main. Open MRs for code review.
- **Issue tracking**: Jira
- **Never push unless told**: Do not run `git push` unless the user explicitly asks. After committing, stop and report what was committed.

## Available Skills

Skills activate automatically. See `instructions.md` for full details.

- `verification-loop` — Unified verification engine (used by /verify, /review, /quality-gate)
- `security-check` — Credential leaks, LLM security, insecure patterns
- `data-pipeline-patterns` — Pipeline stage design, validation, debugging
- `python-conventions` — Team dotenv conventions, API client rules, LLM response parsing, TDD workflow
- `brainstorming` — Collaborative design exploration before implementation
- `writing-plans` — Creates detailed implementation plans from approved specs
