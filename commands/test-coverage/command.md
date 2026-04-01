---
description: "Analyze test coverage, identify gaps, and generate missing tests to reach 80%+ coverage."
---

# Test Coverage Command

Analyze test coverage, identify gaps, and generate missing tests.

## Instructions

### Step 1: Run Coverage

```bash
pytest --cov --cov-report=term-missing -q
```

If pytest is not configured, check for `pyproject.toml`, `setup.cfg`, or `pytest.ini` for test configuration.

### Step 2: Analyze Coverage Report

1. Parse the coverage output
2. List files **below 80% coverage**, sorted worst-first
3. For each under-covered file, identify:
   - Untested functions or methods
   - Missing branch coverage (if/else, try/except, early returns)
   - Dead code that inflates the denominator

If pytest/coverage is not available, perform **static analysis** instead:
1. List all source files and their corresponding test files
2. Flag source files with NO test file
3. For files with tests, list public functions/methods that have no test
4. Estimate coverage percentage based on tested vs untested functions

**Testing Priority Classification:**
- **HIGH**: Core business logic, security-sensitive functions, public APIs, complex algorithms, data pipeline stages
- **MEDIUM**: Utility functions, configuration loading, error handling paths
- **LOW**: Simple getters/setters, trivial wrappers, logging-only code

### Step 3: Generate Missing Tests

For each under-covered file, generate tests following this priority:

1. **Happy path** — Core functionality with valid inputs
2. **Error handling** — Invalid inputs, missing data, API failures
3. **Edge cases** — Empty DataFrames, None/NaN, boundary values (0, -1, MAX)
4. **Branch coverage** — Each if/else, try/except, match/case

#### Test Generation Rules

- Place tests following project convention (typically `tests/test_<module>.py`)
- Use existing test patterns from the project (fixtures, conftest, assertion style)
- Mock external dependencies (databases, APIs, file system)
- Each test should be independent — no shared mutable state
- Name tests descriptively: `test_validate_dataframe_with_missing_columns_returns_error`
- Set `random_state` / seeds in all tests involving randomness

### Step 4: Verify

1. Run the full test suite — all tests must pass
2. Re-run coverage — verify improvement
3. If still below 80%, repeat Step 3 for remaining gaps

### Step 5: Report

```
TEST COVERAGE REPORT
══════════════════════════════════════════════

COVERAGE SUMMARY:
  Total Source Files:    12
  Files With Tests:      8 (67%)
  Files Without Tests:   4 (33%)
  Estimated Coverage:    72%

FILE COVERAGE:
  File                            Coverage  Status
  ──────────────────────────────────────────────────
  scripts/group_issues.py           85%     PASS
  scripts/summarize_epics.py        45%     FAIL
  scripts/filter_standalone_tasks.py 0%     FAIL (no tests)
  utils/constants.py                90%     PASS

FILES MISSING TESTS:
  scripts/filter_standalone_tasks.py — AI task filtering (HIGH priority)
  scripts/categorize_ai_work.py — AI categorization (HIGH priority)

FUNCTIONS NEEDING TESTS:
  summarize_epics.py:parse_ai_response — Complex parsing logic
  summarize_epics.py:quick_ai_check_epic — LLM interaction

PRIORITY RECOMMENDATIONS:
  1. [HIGH] Add tests for filter_standalone_tasks.py — core pipeline step
  2. [HIGH] Add tests for parse_ai_response — complex regex parsing
  3. [MEDIUM] Add edge case tests for group_issues with closed issues
```

## Focus Areas

- Functions with complex branching (high cyclomatic complexity)
- Error handlers and except blocks
- Utility functions used across the codebase
- Data pipeline stages (extract, transform, load)
- Edge cases: None, NaN, empty DataFrame, empty string, zero, negative numbers

## Arguments

$ARGUMENTS can specify a module or file to focus on (default: entire project).
