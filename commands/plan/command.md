---
description: "Restate requirements, assess risks, and create step-by-step implementation plan. WAIT for user confirmation before writing any code."
---

# Plan Command

Create a comprehensive implementation plan before writing any code.

## Instructions

1. **Restate Requirements** — Clarify what needs to be built in your own words
2. **Search First** — Before designing a custom solution:
   - Search the codebase for existing utilities, helpers, or patterns that already solve part of the problem
   - Check if a library or tool already does what's needed (don't reinvent the wheel)
   - Look for similar patterns in the project that can be reused or extended
   - Decision: **Adopt** (use existing), **Extend** (modify existing), or **Build** (create new)
3. **Identify Risks** — Surface potential issues, blockers, and data concerns
4. **Create Step Plan** — Break down implementation into phases
5. **Wait for Confirmation** — MUST receive user approval before proceeding

## When to Use

- Starting a new feature or data pipeline
- Making significant architectural changes
- Working on complex refactoring
- Multiple files/components will be affected
- Requirements are unclear or ambiguous

## Plan Format

```markdown
# Implementation Plan: [Feature Name]

## Requirements Restatement
[Clear restatement of what needs to be built]

## Implementation Phases

### Phase 1: [Name]
- Step 1: ...
- Step 2: ...

### Phase 2: [Name]
- Step 1: ...
- Step 2: ...

## Dependencies
- [External libraries, APIs, data sources needed]

## Risks
- HIGH: [Risk description]
- MEDIUM: [Risk description]
- LOW: [Risk description]

## Data Considerations
- Input data format and source
- Expected output format
- Edge cases in data (nulls, outliers, encoding)
- Estimated data volume

## Testing Strategy
- Unit tests for: [list]
- Integration tests for: [list]

## Estimated Complexity: [HIGH/MEDIUM/LOW]

**WAITING FOR CONFIRMATION**: Proceed with this plan? (yes/no/modify)
```

## Important

**CRITICAL**: Do NOT write any code until the user explicitly confirms the plan with "yes", "proceed", or similar.

If the user wants changes, they can say:
- "modify: [their changes]"
- "different approach: [alternative]"
- "skip phase 2"

## After Planning

After the user confirms, consider:
- Use the `tdd-workflow` skill to implement with tests first
- Use the `code-review` skill after implementation
- Use the `verification-loop` skill before creating a PR

## Arguments

$ARGUMENTS — describe the feature or task to plan.
