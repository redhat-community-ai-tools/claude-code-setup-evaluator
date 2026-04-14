# Visualize Command

Generate a Mermaid flow diagram of a project's architecture.

## Instructions

1. **Read the project** — README, entry points, directory structure. Understand what the system does and how data/control flows through it.

2. **Write a Mermaid flowchart** showing the main flow. Keep it simple:
   - Use `flowchart LR` (left-to-right) for pipelines, `flowchart TD` (top-down) if it fits better
   - 5-12 nodes max — major components only, not individual files
   - Label arrows with what moves between components (data, events, etc.)
   - Use subgraphs sparingly — only if there's a clear grouping
   - Name nodes by what they do, not filenames

3. **Save as a self-contained HTML file** that renders the diagram using Mermaid CDN:
   ```bash
   uv run .ai-workspace/scripts/mktmpdir.py visualize 2>/dev/null || mkdir -p .tmp/visualize
   ```
   Save to `.tmp/visualize/architecture.html`. The HTML is just a minimal page that loads `https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js` and renders the diagram — no extra UI.

4. **Show the user** the Mermaid source inline and tell them the file path.

## Arguments

$ARGUMENTS can specify a target directory or repo:
- `/visualize repositories/ai-initiatives-observer`
- Default: current working directory