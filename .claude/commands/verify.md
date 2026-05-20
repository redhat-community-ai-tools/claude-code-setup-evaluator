---
description: "Does my code work? Runs verification-loop phases 1-4 (environment, types, lint, tests). Use after coding, before review."
---

# Verify Command

Use the Skill tool to invoke `verification-loop` explicitly, then run **Phases 1-4** only:
1. Environment check
2. Type check
3. Lint check
4. Test suite

If the Skill tool is not available or the skill is not found, run the checks directly using the commands from each phase (see the verification-loop skill for exact commands).

Report results. Do NOT run code review (Phase 5) or security scan (Phase 6) — Phase 6 is for `/quality-gate`.

## Arguments

$ARGUMENTS can be:
- `quick` — Only phases 2-3 (types + lint, skip tests)
- `full` — Phases 1-4 (default)
