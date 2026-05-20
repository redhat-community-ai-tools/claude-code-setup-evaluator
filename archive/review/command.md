---
description: "Is my code good? Runs verification-loop phase 5 (code review with DS anti-patterns). Use after verify, before quality-gate."
---

# Review Command

Use the Skill tool to invoke `verification-loop` explicitly, then run **Phase 5** only.

If the Skill tool is not available or the skill is not found, run the review checks directly (see the verification-loop skill for Phase 5 criteria).

Phase 5 checks:
- Security issues (CRITICAL)
- Code quality (HIGH)
- Data science anti-patterns (HIGH)
- Best practices (MEDIUM)

Produces a verdict: APPROVE or REQUEST CHANGES.

## Arguments

$ARGUMENTS can specify files to review (default: all uncommitted changes).
