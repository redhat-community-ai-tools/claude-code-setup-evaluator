# Guidelines

## Hard Limits

- **NO FIX ATTEMPTS without root cause investigation.** Do not change code to "see if this helps." First find the root cause, then fix it.
- **One hypothesis at a time.** Never test multiple theories simultaneously — you won't know which one was right.
- **One variable per test.** When testing a hypothesis, change exactly one thing. Multiple changes confound the diagnosis.

## 3-Strikes Escalation

- If 3 hypotheses fail without resolution, STOP and re-examine your mental model
- Do not continue patching — question the architecture
- Report to the user what you tried and what you learned

## Anti-Patterns (never do these)

- Fixing where the error appears rather than where it originates
- "Quick fix for now" — every fix must address root cause
- Skipping test creation before implementing a fix
- Removing error handling to make the error go away
- Adding try/except to suppress an exception without understanding it

## Instrumentation Rules

- Use `logging.debug()` for diagnostic output, not `print()`
- Log BEFORE the operation that might fail, not after
- Include actual values in diagnostic output (shapes, types, lengths) — not just "entering function X"
- Remove all diagnostic instrumentation after the bug is fixed
