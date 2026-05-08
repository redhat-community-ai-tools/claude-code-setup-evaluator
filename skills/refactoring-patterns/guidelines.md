# Guidelines

## Measurement Requirements

- **Always measure before AND after.** No exceptions. If you can't measure, the refactoring is speculative.
- **Record baseline numbers** before making any changes.
- **Same metrics before and after** — don't switch what you're measuring mid-refactoring.

## Scope Limits

- **One refactoring target per pass.** Don't "clean up the whole file" — pick one thing.
- **Don't refactor code you're passing by.** If you're fixing a bug in function A, don't also refactor function B.
- **Don't introduce new abstractions with only one user.** If the extracted function/class is only called once, the extraction probably wasn't justified.

## Revert Criteria

- If metrics don't improve, revert. "Looks cleaner" is not a measurement.
- If tests break and the fix isn't obvious within 5 minutes, revert.
- If the refactoring creates more files/classes than it simplifies, reconsider.

## Bulk Refactoring Rules

- Only use bulk mode for purely mechanical changes (rename, pattern replacement)
- Verify the transformation is context-independent before applying at scale
- Run full test suite after bulk changes — not just the files you touched
- One commit per bulk operation with a descriptive message
