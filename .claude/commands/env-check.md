---
description: "Validate local development environment setup. Checks Python version, dependencies, env vars, config files, and unapplied migrations in one pass."
---

# Environment Check

The first thing you do when you clone a project (or revisit one after a few weeks) is make sure your local setup actually works. It could be a wrong runtime version, missing environment variables, or unapplied migrations.

This command validates the entire local setup in one pass.

## Instructions

### 0. Detect Project Type

Before running any checks, detect what kind of project this is:

```bash
# Check for project markers
ls pyproject.toml setup.cfg setup.py requirements.txt .python-version 2>/dev/null  # Python
ls package.json 2>/dev/null  # Node.js
ls go.mod 2>/dev/null  # Go
ls Cargo.toml 2>/dev/null  # Rust
ls pom.xml build.gradle 2>/dev/null  # Java
```

If no project markers are found, ask the user: "couldn't detect the project type — what stack is this?"

Run only the checks relevant to the detected stack. The sections below use Python as the example, but adapt to the detected stack (e.g., `node_modules` for Node, `go mod tidy` for Go).

Check this project's development environment is properly configured:

### 1. Runtime Version

- Look for configuration files that specify the required runtime version for the detected stack
- For Python: `pyproject.toml`, `.python-version`, `setup.cfg`, `runtime.txt`
- For Node: `package.json` engines field, `.nvmrc`, `.node-version`
- For Go: `go.mod` go directive
- For Rust: `rust-toolchain.toml`
- Check the installed version matches the project's requirement
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
- A repo path (e.g., `repositories/backend-api`) — check that repo specifically
- Empty — check the current working directory or the repo the user is focused on
