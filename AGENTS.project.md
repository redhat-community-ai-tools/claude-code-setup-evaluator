## Team

Data Science team at Red Hat. This workspace is a pilot for standardizing how we use Claude Code across the team.

## Repositories

- `repositories/ai-initiatives-observer/` — Pipeline that discovers AI-related work across the org by analyzing Jira tickets. Python, Gemini API.

## Conventions (all repos)

- **Language**: Python 3.10+
- **Testing**: pytest. Run tests before committing.
- **Secrets**: Never commit `.env` files, API keys, or tokens. Use environment variables.
- **Branches**: Work on feature branches, not main. Open MRs for code review.
- **Issue tracking**: Jira

## Available Skills

Skills activate automatically. See `instructions.md` for full details.

- `verification-loop` — Unified verification engine (used by /verify, /review, /quality-gate)
- `security-check` — Credential leaks, LLM security, insecure patterns
- `data-pipeline-patterns` — Pipeline stage design, validation, debugging
- `api-client-patterns` — Retry logic, rate limiting, API integration
- `python-testing` — TDD workflow + data science testing patterns
- `python-patterns` — Team dotenv conventions
- `git-workflow` — GitLab/GitHub, submodule workflow
- `mcp-patterns` — Building and securing MCP servers
- `deep-research` — Multi-source research and analysis
- `codebase-onboarding` — Systematic onboarding to unfamiliar codebases
- `compound-engineering` — Captures session patterns as persistent memories
- `brainstorming` — Collaborative design exploration before implementation
- `writing-plans` — Creates detailed implementation plans from approved specs
- `subagent-driven-development` — Executes plans by dispatching a subagent per task with two-stage review
- `writing-skills` — Creates new AI skills using TDD for documentation
