---
name: codebase-onboarding
version: "1.0"
description: Systematic onboarding to unfamiliar codebases. Analyzes project structure, tech stack, conventions, entry points, and data flow to produce an onboarding guide. Use when joining a new project or helping a team member get started.
---

# Codebase Onboarding Skill

Systematically analyze an unfamiliar codebase and produce an onboarding guide.

## When to Activate

- First time working in a new repository
- When a team member asks "how does this project work?"
- When setting up Claude Code for a new project (generating CLAUDE.md)
- After major refactors that change project structure

## Onboarding Process

### Phase 1: Reconnaissance

Quickly establish what the project is and how it's built:

```bash
# What is it?
cat README.md | head -50

# Tech stack
ls pyproject.toml setup.py setup.cfg requirements*.txt package.json Cargo.toml go.mod 2>/dev/null

# Project structure
find . -maxdepth 2 -type f -name "*.py" -o -name "*.js" -o -name "*.ts" | head -30

# Git basics
git log --oneline -10
git remote -v
```

**Capture:** Language, framework, package manager, repo age, team size (from git log).

### Phase 2: Architecture Mapping

Understand how the code is organized:

1. **Entry points** — What runs first? (`main.py`, `app.py`, `manage.py`, CLI scripts)
2. **Directory purpose** — What does each top-level directory do?
3. **Data flow** — How does data move through the system? (input → processing → output)
4. **External dependencies** — What APIs, databases, or services does it connect to?
5. **Configuration** — Where are settings? (env vars, config files, constants)

```bash
# Find entry points
grep -rn "if __name__" --include="*.py" | head -10
grep -rn "def main" --include="*.py" | head -10

# Find imports to understand dependencies
grep -rn "^import\|^from" --include="*.py" | grep -v __pycache__ | sort -u | head -30

# Find config patterns
grep -rn "os.getenv\|load_dotenv\|yaml.safe_load\|config" --include="*.py" | head -10
```

### Phase 3: Convention Detection

Learn how the team writes code:

1. **Naming** — snake_case? camelCase? File naming pattern?
2. **Testing** — pytest? unittest? Where are tests? How to run them?
3. **Git workflow** — Branch naming? Commit style? PR process?
4. **Code style** — Type hints? Docstrings? Linters configured?
5. **Error handling** — Custom exceptions? Logging patterns?

```bash
# Testing
ls tests/ test/ 2>/dev/null
grep -rn "def test_" --include="*.py" | wc -l
cat pytest.ini pyproject.toml 2>/dev/null | grep -A 5 "pytest\|testpaths"

# Git conventions
git log --oneline -20  # Commit message style
git branch -a | head -10  # Branch naming

# Linting/formatting
cat .pre-commit-config.yaml pyproject.toml 2>/dev/null | grep -A 3 "ruff\|black\|flake8\|mypy"
```

### Phase 4: Generate Onboarding Guide

Produce a structured guide with:

```
ONBOARDING GUIDE: [Project Name]
═══════════════════════════════════

WHAT IT DOES:
  [1-2 sentence description]

TECH STACK:
  Language:     Python 3.10+
  Framework:    [if any]
  Package mgr:  uv / pip
  Testing:      pytest (X tests)
  CI/CD:        [if configured]

HOW TO SET UP:
  1. [Clone/submodule command]
  2. [Install dependencies]
  3. [Configure environment]
  4. [Run tests to verify]

PROJECT STRUCTURE:
  scripts/     — Pipeline steps (independently runnable)
  utils/       — Shared utilities
  prompts/     — LLM prompt templates
  tests/       — Unit tests
  data/        — Generated output (gitignored)

HOW IT RUNS:
  [Data flow diagram: input → step 1 → step 2 → ... → output]

KEY FILES TO READ FIRST:
  1. [Most important file — why]
  2. [Second most important — why]
  3. [Third — why]

CONVENTIONS:
  - [Naming convention]
  - [Testing approach]
  - [Git workflow]

HOW TO RUN TESTS:
  [Exact command]

COMMON TASKS:
  - "Add a new pipeline step" → [how]
  - "Debug a failing stage" → [how]
  - "Update the report" → [how]
```

## Tips

- Read README.md and any CLAUDE.md/AGENTS.md first
- Run the test suite to verify your understanding
- Look at the most recent git commits to understand current work
- Check for `.env.example` to understand required credentials
- Don't try to understand everything — focus on the main data flow first
