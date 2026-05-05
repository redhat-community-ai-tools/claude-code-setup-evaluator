# Layer 3 Deep Evaluation Log

**Date:** 2026-05-05
**Skills tested:** clean-code-guide, data-pipeline-patterns, python-conventions, security-check
**Repositories used:** site-analysis, il-agent, ai-initiatives-observer
**Mode:** standard

## How This Evaluation Works

For each skill below, we ran 4 tasks: 1 knowledge question (can Claude recall the skill's rules?) and 3 tasks on your actual repositories (does the skill change how Claude reviews, writes, or debugs real code?).

Each task was run twice — once with the skill loaded, once without. The responses were sent to Gemini as a blind judge (it doesn't know which is which). Gemini voted 3 times per task; majority wins. If both responses follow the same conventions equally well, that means Claude already knows the content and the skill is redundant — the verdict is TIE regardless of minor quality differences.

No files were modified during testing — all repository access was read-only (verified post-test).

---

## clean-code-guide                                  NO IMPACT

### Task 1 (knowledge): Function line limit and pytest edge cases
- Vote 1: tie (redundant) — "Both responses correctly extracted the specific information"
- Vote 2: tie (redundant) — "Both responses perfectly applied the conventions"
- Vote 3: tie (redundant) — "Both responses retrieved the exact same information"
- **Verdict: TIE (HIGH confidence) | Redundancy: redundant**

### Task 2 (review on site-analysis): Function length, type hints, variable names
- Vote 1: tie (redundant) — "Both models used the specific numerical limit from the guide"
- Vote 2: tie (redundant) — "Both responses used the 50-line function limit"
- Vote 3: tie (redundant) — "Both strictly adhered to the 50-line function limit"
- **Verdict: TIE (HIGH confidence) | Redundancy: redundant**

### Task 3 (write on site-analysis): Refactor format_jira_issue
- Vote 1: tie (redundant) — "Both responses followed the Clean Code Guide conventions perfectly"
- Vote 2: tie (redundant) — "Both responses decomposed the monolithic function"
- Vote 3: tie (redundant) — "Both responses followed the provided conventions exceptionally well"
- **Verdict: TIE (HIGH confidence) | Redundancy: redundant**

### Task 4 (debug on site-analysis): Empty work history crash
- Vote 1: tie (redundant) — "Both responses follow the conventions outlined in the Clean Code Guide equally"
- Vote 2: tie (redundant) — "Both models utilized the skill equally well"
- Vote 3: tie (redundant) — "Both responses follow the clean code conventions equally well"
- **Verdict: TIE (HIGH confidence) | Redundancy: redundant**

### Skill Verdict: NO IMPACT (0 wins, 0 losses, 4 ties) | Redundancy: redundant
The skill contains only generic clean code advice that Claude already follows by default. All 12 judge votes were unanimous ties with "redundant" redundancy signals.

---

## data-pipeline-patterns                            KEEP

### Task 1 (knowledge): JSON output requirements and metadata fields
- Vote 1: with_skill (unique) — "Response 2 included formatting requirements (indent=2, ensure_ascii=False)"
- Vote 2: with_skill (unique) — "Response 2 applied the skill more thoroughly"
- Vote 3: with_skill (unique) — "Response 2 more accurately interpreted the count fields requirement"
- **Verdict: with_skill (HIGH confidence) | Redundancy: unique**

### Task 2 (review on site-analysis): Standard Stage Structure compliance
- Vote 1: tie (redundant) — "Both models used the specific terminology from the skill"
- Vote 2: without_skill (unique) — "Response 1 created a more structured compliance table"
- Vote 3: without_skill (redundant) — "Response 1 applied the conventions more effectively"
- **Verdict: without_skill (LOW confidence) | Redundancy: mixed**

### Task 3 (write on site-analysis): New post-processing stage
- Vote 1: with_skill (unique) — "Response 1 used 'data' key; Response 2 used 'people_summaries'"
- Vote 2: with_skill (unique) — "Response 1 strictly used the generic 'data' key"
- Vote 3: with_skill (unique) — "Response 2 used the key 'data' and 'items_processed' from the skill"
- **Verdict: with_skill (HIGH confidence) | Redundancy: unique**

### Task 4 (debug on site-analysis): KeyError: generated_at
- Vote 1: with_skill (unique) — "Response 2 used the key 'data' and included 'source_file'"
- Vote 2: with_skill (unique) — "Response 2 used correct naming and metadata requirements"
- Vote 3: with_skill (unique) — "Response 2 correctly used 'data' and cited Anti-patterns"
- **Verdict: with_skill (HIGH confidence) | Redundancy: unique**

### Skill Verdict: KEEP (3 wins, 1 loss, 0 ties) | Redundancy: unique
The skill teaches specific team conventions (metadata envelope with `data` key, `_` prefix for derived fields, specific metadata fields) that Claude does not follow by default. The one loss was a low-confidence edge case where the without-skill agent produced a slightly better-formatted review table.

---

## python-conventions                                KEEP

### Task 1 (knowledge): HTTP retry status codes and os.getenv rules
- Vote 1: tie (redundant) — "Both responses followed the provided conventions perfectly"
- Vote 2: tie (redundant) — "Both responses returned the exact same specific information"
- Vote 3: tie (redundant) — "Both Response 1 and Response 2 correctly identify the specific status codes"
- **Verdict: TIE (HIGH confidence) | Redundancy: redundant**

### Task 2 (review on site-analysis): API client timeout and logging review
- Vote 1: with_skill (unique) — "Response 2 checked for Credential Validation"
- Vote 2: with_skill (unique) — "Response 2 explicitly evaluates the Credential Management rules"
- Vote 3: with_skill (unique) — "Response 1 audits the Credential Validation rule"
- **Verdict: with_skill (HIGH confidence) | Redundancy: unique**

### Task 3 (write on il-agent): LLM response JSON parsing
- Vote 1: with_skill (unique) — "Response 2 followed the specific naming convention (clean_llm_response)"
- Vote 2: with_skill (unique) — "Response 1 followed the specific naming convention"
- Vote 3: with_skill (unique) — "Response 2 adopted the clean_llm_response naming convention"
- **Verdict: with_skill (HIGH confidence) | Redundancy: unique**

### Task 4 (debug on site-analysis): Intermittent test failure diagnosis
- Vote 1: tie (redundant) — "The skill is redundant for this specific task"
- Vote 2: with_skill (unique) — "Response 1 uses 'Testing Patterns' framework from skill"
- Vote 3: without_skill (unique) — "Response 1 provides better data-oriented testing patterns"
- **Verdict: TIE (LOW confidence) | Redundancy: mixed**

### Skill Verdict: KEEP (2 wins, 0 losses, 2 ties) | Redundancy: unique
The skill teaches team-specific patterns (clean_llm_response function name, credential validation rules, dotenv loading pattern) that Claude does not follow without guidance. Knowledge questions showed redundancy (Claude can read and repeat rules from either source), but repo-based tasks showed clear skill impact.

---

## security-check                                   NO IMPACT

### Task 1 (knowledge): os.getenv severity and Atlassian regex
- Vote 1: with_skill (unique) — "Response 2 used ATATT3x exact pattern from skill"
- Vote 2: with_skill (unique) — "Response 1 used exact regex defined in the skill"
- Vote 3: with_skill (unique) — "Response 2 used ATATT3x instead of generic ATATT"
- **Verdict: with_skill (HIGH confidence) | Redundancy: unique**

### Task 2 (review on il-agent): Insecure library scan and .gitignore
- Vote 1: without_skill (unique) — "Response 1 did nuanced multi-directory .gitignore audit"
- Vote 2: without_skill (unique) — "Response 1 found JWT and SSL issues with line numbers"
- Vote 3: without_skill (unique) — "Response 1 checked multiple directory levels"
- **Verdict: without_skill (HIGH confidence) | Redundancy: unique**

### Task 3 (write on site-analysis): PII sanitization for LLM
- Vote 1: without_skill (unique) — "Response 2 found plaintext credentials in .env"
- Vote 2: without_skill (unique) — "Response 2 identified GitHub/GitLab PATs"
- Vote 3: without_skill (unique) — "Response 1 found hardcoded secrets"
- **Verdict: without_skill (HIGH confidence) | Redundancy: unique**

### Task 4 (debug on ai-initiatives-observer): Leaked GitHub PAT
- Vote 1: with_skill (unique) — "Response 2 used exact regex length from skill"
- Vote 2: with_skill (unique) — "Response 1 used exact regex length and --exclude-dir"
- Vote 3: with_skill (unique) — "Response 1 used skill's directory exclusions"
- **Verdict: with_skill (HIGH confidence) | Redundancy: unique**

### Skill Verdict: NO IMPACT (2 wins, 2 losses, 0 ties) | Redundancy: mixed
The skill helps with specific patterns (regex formats, grep commands) but may constrain the agent on broader security reviews where Claude's general knowledge produces more thorough results. The skill won on tasks requiring specific regex patterns but lost on tasks requiring broader security auditing, suggesting the skill's checklist approach can be too narrow.
