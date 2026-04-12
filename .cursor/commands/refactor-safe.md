# Safe Refactor

At this point, you've reviewed the code, tested it, and documented it. If it still has flagged structural problems (like a 65-line handler doing validation, inference, logging, and response formatting in one block), this is the command to fix it.

Refactoring with AI is risky because Claude tends to "improve" things you didn't ask it to touch. This command has an explicit constraint: **the public API must not change.** It focuses on internal structure only.

## Instructions

### 1. Identify Scope

- Read the target file(s) specified in $ARGUMENTS
- Identify the **public API**: exported functions, class interfaces, function signatures, return types
- Document the public API before making any changes

### 2. Identify Refactoring Opportunities

Look for these internal problems:
- **Long functions** (50+ lines doing multiple things)
- **Duplicated logic** (same pattern in multiple places)
- **Deep nesting** (3+ levels of if/for/try)
- **Poor naming** (single-letter variables, misleading names)
- **Mixed concerns** (validation + business logic + formatting in one function)
- **Dead code** (unused imports, unreachable branches)

### 3. Apply Refactoring

For each change:
- Extract helper functions for distinct responsibilities
- Simplify nested conditionals (early returns, guard clauses)
- Rename variables/functions for clarity
- Remove dead code
- Consolidate duplicated logic

### 4. Verify

After refactoring:
- Confirm the public API is unchanged — same function signatures, same return types, same behavior
- Run tests if they exist (`uv run python -m pytest`)
- If no tests exist, warn the user

### 5. Present Changes

Show what was refactored:
```
Safe Refactor Summary
=====================
File: scripts/summarize_people.py

PUBLIC API: Unchanged
  - main(argv) — same signature, same behavior
  - compute_person_stats(issues) — same signature, same return type

INTERNAL CHANGES:
  - Extracted _parse_date() from compute_person_stats (was inline, 8 lines)
  - Extracted _count_collaborators() from compute_person_stats (was inline, 12 lines)
  - Renamed 'ps' → 'person_summary' in main loop
  - Removed unused import: 'json'

Tests: 70 passed, 0 failed
```

## Critical Rules

- **NEVER change function signatures** (name, parameters, return type)
- **NEVER change behavior** — the output must be identical for the same input
- **NEVER add new features** — no new parameters, no new error handling, no new logging
- **NEVER change exports** — if other files import from this module, those imports must still work
- If you're unsure whether a change is safe, don't make it — list it as a suggestion instead

## Arguments

$ARGUMENTS can be:
- A file path (e.g., `scripts/summarize_people.py`) — refactor that file
- A directory (e.g., `utils/`) — refactor all files in the directory
- Empty — ask the user what to refactor