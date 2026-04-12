# Environment Check

The first thing you do when you clone a project (or revisit one after a few weeks) is make sure your local setup actually works. It could be a wrong runtime version, missing environment variables, or unapplied migrations.

This command validates the entire local setup in one pass.

## Instructions

Check this project's development environment is properly configured:

### 1. Runtime Version

- Look for configuration files that specify requirements: `pyproject.toml`, `.python-version`, `setup.cfg`, `runtime.txt`
- Check the installed Python version matches the project's requirement
- Report: version required vs version found

### 2. Package Dependencies

- Check if `uv` is installed and available
- Check if `.venv` exists and is up to date
- If `pyproject.toml` exists, verify packages are synced (`uv sync --check` or equivalent)
- If `requirements.txt` exists, check packages are installed
- Report: any missing or outdated packages

### 3. Environment Variables

- Look for `.env.example` or `.env.template` files
- Compare against the actual `.env` file (if it exists)
- Report: which required env vars are missing or empty
- Do NOT print the actual values — just report presence/absence

### 4. Configuration Files

- Check if config files exist that are expected (e.g., `config.yaml` from `config.yaml.example`)
- Check if required config values are set
- Report: missing config files or values

### 5. Pre-commit Hooks

- Check if `pre-commit` is installed (`uv run pre-commit --version`)
- Check if hooks are installed (`.git/hooks/pre-commit` exists)
- If not installed, report the install command

### 6. Summary

Present a clear pass/fail summary:

```
Environment Check
=================
Python version:     PASS (3.12 >= 3.10 required)
Dependencies:       PASS (all synced)
Environment vars:   FAIL (GOOGLE_API_KEY missing)
Config files:       PASS (config.yaml exists)
Pre-commit hooks:   WARN (not installed — run: uv run pre-commit install)

Result: 1 FAIL, 1 WARN — fix before proceeding
```

## Important

- Never print secret values — only report if they exist or not
- Run each check even if a previous one fails
- Be specific about how to fix each issue
- If this is a repo inside `repositories/`, check that repo's setup, not the workspace root

## Arguments

$ARGUMENTS can be:
- A repo path (e.g., `repositories/site-analysis`) — check that repo specifically
- Empty — check the current working directory or the repo the user is focused on