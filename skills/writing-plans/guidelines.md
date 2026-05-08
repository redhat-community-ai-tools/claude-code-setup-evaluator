# Guidelines

## Hard Limits — No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Principles

- **DRY** — don't repeat yourself across tasks
- **YAGNI** — don't add features that aren't in the spec
- **TDD** — write failing test first, then minimal implementation
- **Frequent commits** — commit after each task passes

## Quality Standards

- Exact file paths in every task
- Complete code in every code step
- Exact commands with expected output
- Each task should produce self-contained changes that make sense independently
