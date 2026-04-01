---
name: verification-loop
version: "1.0"
description: Unified verification engine for Python data science projects. Covers environment checks, type checking, linting, tests, security scans, code review with DS anti-patterns, and notebook checks. Commands (/verify, /review, /quality-gate) invoke different subsets of this skill.
---

# Verification Loop

The single source of truth for all code checks. Commands invoke specific phases:
- `/verify` → Phases 1-4 (does my code work?)
- `/review` → Phase 5 (is the code good?)
- `/quality-gate` → Phases 1-4 + Phase 6 (safe to push?)

## When to Activate

- After completing a feature or significant code change
- Before creating an MR/PR
- After refactoring
- When the user says "verify", "review", "check", or "quality gate"

## Phases

### Phase 1: Environment

```bash
uv sync --check 2>&1 || pip check 2>&1
```

If dependencies are out of sync, STOP and fix.

### Phase 2: Type Check

```bash
mypy . --ignore-missing-imports 2>&1 | head -30
```

### Phase 3: Lint

```bash
ruff check . 2>&1 | head -30
ruff format --check . 2>&1
```

### Phase 4: Tests

```bash
pytest --cov --cov-report=term-missing -q 2>&1 | tail -50
```

Target: 80% minimum coverage.

### Phase 5: Code Review

For each changed file (`git diff --name-only HEAD`), check:

**Security (CRITICAL — must fix):**
- Hardcoded credentials, API keys, tokens
- Credentials in Jupyter notebook outputs
- SQL injection (string concatenation in queries)
- Pickle/unsafe deserialization of untrusted data
- Missing input validation
- Sensitive data in logs

**Code Quality (HIGH — should fix):**
- Functions > 50 lines, files > 500 lines, classes > 300 lines
- Functions > 5 parameters
- Deep nesting > 3 levels, cyclomatic complexity > 10
- Missing type hints on public functions
- Missing docstrings with Args/Returns/Raises
- Bare `except`, mutable default arguments, global state mutation

**Data Science Anti-Patterns (HIGH — should fix):**
- Data leakage (fitting transformers before train/test split)
- Missing random seeds for reproducibility
- Hardcoded file paths
- Magic numbers without named constants
- No DataFrame validation (schema checks, null handling)
- Giant notebooks (100+ cells — extract to .py modules)
- Copy-paste feature engineering

**Best Practices (MEDIUM — nice to fix):**
- Missing tests for new code
- Poor variable names (`df2`, `temp`, `x`)
- Print statements instead of logging

**Verdict rules:**
- Any CRITICAL → REQUEST CHANGES
- 3+ HIGH → REQUEST CHANGES
- Only MEDIUM → APPROVE with suggestions

### Phase 6: Pre-Push Security

```bash
# Secret patterns
grep -rn --include="*.py" --include="*.yaml" --include="*.json" \
  -E "(AIzaSy|sk-[a-zA-Z0-9]{20,}|sk-ant-|ATATT3x|AKIA|ghp_|hf_)" \
  --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv \
  --exclude=".env*" . 2>/dev/null

# .gitignore check
git ls-files | grep -E "\.env|credentials|secret|\.key|\.pem"

# Pre-commit hooks
uv run pre-commit run --all-files 2>/dev/null
```

### Phase 7: Notebook Check (if applicable)

```bash
grep -rn "api_key\|password\|secret\|token" --include="*.ipynb" . 2>/dev/null
```

## Output Format

```
VERIFICATION REPORT
====================
Environment: [PASS/FAIL]
Types:       [PASS/FAIL] (X errors)
Lint:        [PASS/FAIL] (X warnings)
Tests:       [PASS/FAIL] (X/Y passed, Z% coverage)
Review:      [APPROVE/REQUEST CHANGES] (X critical, Y high, Z medium)
Security:    [PASS/FAIL] (X issues)

Verdict:     [READY / NOT READY]
```
