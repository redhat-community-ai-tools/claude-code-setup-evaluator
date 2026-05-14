# Guidelines

## Severity Classifications

- **CRITICAL** — blocks push: hardcoded API keys, eval/exec on untrusted input, credentials with real defaults
- **HIGH** — should fix before push: SSL verification disabled, PII sent to external LLM, unsafe deserialization
- **MEDIUM** — fix soon: weak cryptography, predictable randomness, race conditions

## Hard Limits

- Never skip the .gitignore verification step
- Always check git history for previously committed secrets
- If CRITICAL issues found, verdict MUST be "NEEDS FIXES" — no exceptions
- Report ALL findings, not just the first one found

## Remediation Requirements

- Every finding must include the file, line number, and a concrete fix
- For hardcoded secrets: recommend moving to `.env` + `python-dotenv`
- For committed secrets: recommend immediate key rotation
- For LLM PII issues: recommend sanitization before API calls

## Escalation

- If secrets were previously committed to git history, warn about key rotation urgency
- If .gitignore is missing entirely, flag as CRITICAL (not just HIGH)
