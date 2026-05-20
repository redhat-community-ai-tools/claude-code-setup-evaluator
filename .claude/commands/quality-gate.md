---
description: "Safe to push? Runs verification-loop phases 1-4 + phase 6 (tests + secret scan + pre-commit). Use after review, right before git push."
---

# Quality Gate Command

Use the Skill tool to invoke `verification-loop` explicitly, then run **Phases 1-4 + Phase 6**.

If the Skill tool is not available or the skill is not found, run the checks directly (see the verification-loop skill for exact commands per phase).

Phases:
1. Environment check
2. Type check
3. Lint check
4. Test suite
5. *(skip Phase 5 — code review is separate)*
6. Pre-push security scan + .gitignore audit + pre-commit hooks

Produces a verdict: **READY TO PUSH** or **BLOCKED** with reasons.
