## Team

Data Science team at Red Hat. This workspace is a pilot for standardizing how we use Claude Code across the team.

## Repositories

- `repositories/ai-initiatives-observer/` — Pipeline that discovers AI-related work across the org by analyzing Jira tickets. Python, Gemini API.
- `repositories/site-analysis/` — People & expertise discovery pipeline for geographic sites. Analyzes Jira activity to generate per-person work profiles. Python, Gemini API.

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
- `api-client-patterns` — Retry logic, rate limiting, API integration
- `python-conventions` — Team dotenv conventions + TDD workflow + testing patterns
- `git-workflow` — GitLab/GitHub conventions, branch workflow
- `brainstorming` — Collaborative design exploration before implementation
- `writing-plans` — Creates detailed implementation plans from approved specs
