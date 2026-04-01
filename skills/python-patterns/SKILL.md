---
name: python-patterns
version: "1.0"
description: Team-specific Python conventions for credential management with dotenv. Covers .env file structure, loading patterns, and secure defaults.
---

# Python Patterns — Team Conventions

Team-specific conventions that go beyond what Claude knows by default.

## When to Activate

- When writing code that uses environment variables or credentials
- When creating or modifying `.env` files
- When setting up a new project or script that needs API keys

## Credential Management with dotenv

### .env File Structure

```bash
# Required credentials
JIRA_URL=https://issues.redhat.com
JIRA_TOKEN=your_jira_token_here
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional overrides
GEMINI_MODEL=gemini-3-flash-preview
JIRA_MAX_RESULTS=250
```

### Loading Pattern

```python
from pathlib import Path
from dotenv import load_dotenv

# Load from project root (not current directory)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Access with no default for secrets (fail if missing)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not set in .env file")
    sys.exit(1)

# Optional values can have defaults
model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
```

### Rules

- **Never** use real values as defaults: `os.getenv("KEY", "AIza...")` exposes the key in code
- **Always** create `.env.example` with placeholder values for team distribution
- **Always** add `.env` to `.gitignore`
- **Never** commit `.env` files — only `.env.example`
- **Load early** — call `load_dotenv()` at the top of entry points, not deep in utility code
- **Validate required vars** — fail fast if a required credential is missing, don't let it fail later with a confusing error

### .env.example Template

```bash
# Copy this file to .env and fill in your credentials:
#   cp .env.example .env

# Required
JIRA_URL=https://issues.redhat.com
JIRA_TOKEN=your_jira_personal_access_token_here
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional
GEMINI_MODEL=gemini-3-flash-preview
JIRA_MAX_RESULTS=250
```
