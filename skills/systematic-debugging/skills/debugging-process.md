# Debugging Process

## Phase 1: Reproduce

Before investigating, make the bug happen reliably.

1. Run the failing command/test exactly as reported
2. Note the exact error message, stack trace, and exit code
3. Create a minimal reproduction — strip away unrelated code until you have the smallest case that still fails
4. If the bug is intermittent, run 5 times and note the failure rate

**Output:** A command that reproduces the bug 100% of the time (or a documented failure rate).

## Phase 2: Isolate

Narrow down where the bug lives.

1. Read the stack trace bottom-up — the deepest frame is where the error surfaces, but the cause is usually higher
2. Add diagnostic logging at boundaries (function entry/exit, data transformations, API calls)
3. Use binary search: comment out half the logic, does it still fail?
4. Check recent changes: `git log --oneline -10` and `git diff HEAD~3` — did something change near the failure?
5. Verify assumptions: print the actual values of variables you think you know

**Instrumentation patterns:**

```python
# At function boundaries
import logging
logger = logging.getLogger(__name__)

def process_data(df):
    logger.debug(f"process_data called: shape={df.shape}, columns={list(df.columns)}")
    logger.debug(f"dtypes: {df.dtypes.to_dict()}")
    # ... processing ...
    logger.debug(f"process_data result: shape={result.shape}")
    return result
```

```python
# At data transformation points
logger.debug(f"Before transform: nulls={df.isnull().sum().to_dict()}")
result = transform(df)
logger.debug(f"After transform: nulls={result.isnull().sum().to_dict()}")
```

**Output:** The specific function/line where the bug originates (not just where it surfaces).

## Phase 3: Hypothesize

Form ONE explicit hypothesis. Not "maybe it's X or Y" — one specific claim.

1. State the hypothesis clearly: "The bug is because [specific cause] when [specific condition]"
2. Identify what evidence would confirm it and what would refute it
3. Design a minimal test: change ONE variable to test the hypothesis
4. If the hypothesis involves data: inspect the actual data at the point of failure

**Bad hypotheses (too vague):**
- "Something is wrong with the data"
- "There might be a race condition"
- "The API might be returning bad data"

**Good hypotheses (testable):**
- "The `price` column contains NaN values that cause the mean calculation to return NaN"
- "The API returns a 429 after 10 requests/second, and our batch sends 15"
- "The DataFrame index is not reset after filtering, causing iloc to miss rows"

## Phase 4: Verify

Test the hypothesis directly.

1. Write a test that captures the bug (this becomes a regression test)
2. If the hypothesis is correct: implement the minimal fix
3. If the hypothesis is wrong: go back to Phase 2 with what you learned
4. After fixing, run the full test suite — the fix must not break anything else

## The 3-Strikes Rule

If 3 consecutive hypotheses fail:

**STOP.** Do not attempt a 4th fix. Instead:
1. Question your mental model of the system — what assumption are you making that's wrong?
2. Re-read the code path from scratch (don't skim — read every line)
3. Check if the bug is in a dependency, not in your code
4. Consider: is the architecture itself the problem? (wrong abstraction, missing layer, incorrect data flow)

## Common Root Cause Patterns

| Symptom | Likely root cause | Where to look |
|---------|------------------|---------------|
| NaN/None in output | Missing data not handled upstream | Data loading/transformation |
| KeyError on DataFrame | Column renamed or dropped earlier in pipeline | Previous stage's output |
| Index out of bounds | Off-by-one or stale index after filter | Filter/merge operations |
| "Works on my machine" | Environment difference | .env, Python version, package versions |
| Intermittent failure | Race condition or external dependency | Async code, API calls, file I/O |
| Wrong results (no error) | Logic error in transformation | Unit test each transformation step |
| Import error | Circular import or missing dependency | Module dependency graph |
