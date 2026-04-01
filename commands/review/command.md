---
description: "Is my code good? Runs verification-loop phase 5 (code review with DS anti-patterns). Use after verify, before quality-gate."
---

# Review Command

Activate the `verification-loop` skill and run **Phase 5** only:
- Security issues (CRITICAL)
- Code quality (HIGH)
- Data science anti-patterns (HIGH)
- Best practices (MEDIUM)

Produces a verdict: APPROVE or REQUEST CHANGES.

## Arguments

$ARGUMENTS can specify files to review (default: all uncommitted changes).
