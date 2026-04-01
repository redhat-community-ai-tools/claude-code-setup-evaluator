---
description: "Does my code work? Runs verification-loop phases 1-4 (environment, types, lint, tests). Use after coding, before review."
---

# Verify Command

Activate the `verification-loop` skill and run **Phases 1-4** only:
1. Environment check
2. Type check
3. Lint check
4. Test suite

Report results. Do NOT run code review (Phase 5) or security scan (Phase 6) — those are for `/review` and `/quality-gate`.

## Arguments

$ARGUMENTS can be:
- `quick` — Only phases 2-3 (types + lint, skip tests)
- `full` — Phases 1-4 (default)
