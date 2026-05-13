---
description: "Explain code functionality — from high-level overview to line-by-line analysis. Useful for onboarding, knowledge transfer, and understanding unfamiliar code."
---

# Explain Code

Analyze and explain code functionality at multiple levels of detail.

## Instructions

Explain the code specified by $ARGUMENTS (a file path, function name, or module). If no argument given, ask what to explain.

### Step 1: Context

- Identify the file's role in the project
- Review imports and dependencies
- Check how it's called (grep for usage)

### Step 2: High-Level Overview

- What does this code do? (1-2 sentences)
- What problem does it solve?
- How does it fit into the larger system?

### Step 3: Structure Breakdown

- Break into logical sections
- Map data flow and control flow
- Identify key classes, functions, and their responsibilities

### Step 4: Detailed Analysis

For complex or non-obvious sections:

- Explain the algorithm or approach
- Clarify data transformations and processing steps
- Describe error handling and edge cases
- Explain Python-specific patterns (decorators, generators, context managers, comprehensions)

### Step 5: Practical Notes

- **Performance** — bottlenecks, complexity, scalability concerns
- **Dependencies** — external services, APIs, database operations
- **Testing** — how to test this code, what scenarios matter
- **Gotchas** — non-obvious behavior, implicit assumptions, known limitations

## Output Format

```
FILE: [path]
PURPOSE: [one sentence]

OVERVIEW:
  [2-3 sentence summary]

STRUCTURE:
  [section breakdown with line ranges]

DETAILED ANALYSIS:
  [section-by-section explanation, focused on non-obvious parts]

PRACTICAL NOTES:
  [performance, dependencies, testing, gotchas]
```

## Important

- **Scale depth to complexity.** A 10-line utility gets a short explanation. A 200-line pipeline stage gets a thorough one.
- **Focus on the "why" not just the "what".** Don't just describe what each line does — explain why it's done that way.
- **Use parallel agents** (Explore) to check how the code is used across the project.
- **Skip the obvious.** Don't explain `import os` or `x = 5`. Focus on logic that requires understanding.

## Arguments

$ARGUMENTS can specify:
- A file: `/explain-code src/pipeline/api_client.py`
- A function: `/explain-code fetch_tickets`
- A module: `/explain-code src/pipeline/`
- A concept: `/explain-code "how does the retry logic work"`
