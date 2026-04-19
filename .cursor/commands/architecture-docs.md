# Architecture Documentation

Generate architecture documentation for the project.

## Quick Mode

If $ARGUMENTS contains `--quick` or `quick`:

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

**Stop here for quick mode — do not produce full documentation.**

## Full Mode (default)

### Step 1: Discover Architecture

Use parallel agents to explore the codebase:

- Read README.md, CLAUDE.md, and any existing docs
- Map the directory structure and identify key modules
- Trace data flow: where does data enter, how is it processed, where does it go?
- Identify external integrations (APIs, databases, services)
- Review config files for infrastructure context

### Step 2: Generate Documentation

Produce the following sections, scaled to the project's complexity:

**System Overview**
- What the system does (1-2 paragraphs)
- Key stakeholders and users
- External systems it connects to

**Component Architecture**
- Mermaid diagram showing major components and their relationships
- Each component: responsibility, inputs, outputs, dependencies
- Clear boundaries between modules

**Data Flow**
- Mermaid diagram showing how data moves through the system
- Data sources, transformations, and destinations
- Data formats at each stage (raw JSON, DataFrames, cleaned output, etc.)

**Data Architecture** (if applicable)
- Data models and schemas
- Storage strategy (files, databases, APIs)
- Data validation and quality checks

**Key Design Decisions**
- For each non-obvious decision:
  - What was decided
  - Why (the motivation/constraint)
  - What alternatives were considered
  - Trade-offs accepted

**Security & Credentials**
- How secrets are managed
- External API authentication approach
- Data sensitivity and handling

### Step 3: Save

Save documentation to `docs/architecture.md` (or `docs/architecture/` if multiple files needed).

Use Mermaid syntax for all diagrams — renders natively in GitLab/GitHub.

## Output Format

```markdown
# [Project Name] Architecture

## System Overview
[what it does, who uses it, what it connects to]

## Component Architecture
[mermaid diagram + component descriptions]

## Data Flow
[mermaid diagram + stage descriptions]

## Data Architecture
[models, storage, validation]

## Key Design Decisions
[ADR-style entries]

## Security & Credentials
[secrets management, auth, data sensitivity]
```

## Important

- **Document what exists, not what should exist.** This is a snapshot of current architecture, not aspirational.
- **Use Mermaid diagrams.** They render in GitLab/GitHub and are easy to update.
- **Focus on data flow.** For DS projects, how data moves through the system matters more than class hierarchies.
- **Keep it maintainable.** A 2-page doc that stays updated beats a 20-page doc that rots.

## Arguments

$ARGUMENTS can specify:
- `--quick` or `quick`: Quick Mermaid diagram only (no full documentation)
- A specific repo: `/architecture-docs repositories/ai-initiatives-observer`
- A specific focus: `/architecture-docs data-flow` or `/architecture-docs decisions`
- Default: full documentation for the current workspace