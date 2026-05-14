---
description: "Check code quality and run linting"
---

# Check Code

Look at the code in the current directory or the path provided by the user.

Run these checks:
1. Run `ruff check .` to find linting issues
2. Run `ruff format --check .` to check formatting
3. Run `mypy . --ignore-missing-imports` for type checking
4. Run `pytest --cov -q` to check test coverage

For each check, report:
- What passed
- What failed
- How to fix the failures

If all checks pass, tell the user the code looks good.

If there are failures, prioritize them:
- Security issues first
- Type errors second
- Lint issues third
- Formatting last

Also check if functions are too long (over 50 lines) and if there's code duplication.

At the end, give an overall verdict: READY or NEEDS WORK.
