---
description: "Safe to push? Runs verification-loop phases 1-4 + phase 6 (tests + secret scan + pre-commit). Use after review, right before git push."
---

# Quality Gate Command

Activate the `verification-loop` skill and run **Phases 1-4 + Phase 6**:
1. Environment check
2. Type check
3. Lint check
4. Test suite
5. *(skip Phase 5 — that's /review)*
6. Pre-push security scan + .gitignore audit + pre-commit hooks

Produces a verdict: **READY TO PUSH** or **BLOCKED** with reasons.
