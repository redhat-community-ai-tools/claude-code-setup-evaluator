---
description: "Generate an interactive HTML visualization of the project structure — collapsible file tree, color-coded by language, with file sizes and language breakdown chart."
---

# Visualize Command

Generate a visual map of the current project as an interactive HTML file.

## Instructions

### Step 1: Scan the Project

Collect file metadata for the current repository:

```bash
# Get all tracked + untracked files (exclude git internals and caches)
find . -type f \
  -not -path './.git/*' \
  -not -path './__pycache__/*' \
  -not -path './.venv/*' \
  -not -path './node_modules/*' \
  -not -path './.mypy_cache/*' \
  -not -path './data/*' \
  -not -path './.tmp/*' \
  -not -name '*.pyc' \
  | head -500
```

For each file, collect:
- Path (relative to project root)
- Size in bytes
- Line count (for text files)
- Language (from extension)

### Step 2: Generate the HTML

Create a self-contained HTML file with:

1. **Collapsible directory tree** — click to expand/collapse folders
2. **Color coding by language:**
   - Python (.py) → blue
   - Markdown (.md) → green
   - YAML/JSON (.yaml, .yml, .json) → orange
   - HTML (.html) → purple
   - Shell (.sh) → gray
   - Other → light gray
3. **File metadata** — show size and line count next to each file
4. **Summary bar at the top** — total files, total lines, language breakdown
5. **Pie chart** — language distribution by file count or line count

### Step 3: Save and Report

```bash
# Create tmp directory for output
uv run .ai-workspace/scripts/mktmpdir.py visualize 2>/dev/null || mkdir -p .tmp/visualize
```

Save the HTML file to `.tmp/visualize/project-map.html`

Tell the user:
```
Project map generated: .tmp/visualize/project-map.html
Open it in your browser to explore the project structure.

Quick stats:
  Files:      [count]
  Lines:      [count]
  Languages:  Python ([N]%), Markdown ([N]%), YAML ([N]%), ...
  Largest:    [filename] ([size])
```

### HTML Template Structure

The HTML should be **self-contained** (no external dependencies) using:
- Vanilla JavaScript for tree expand/collapse
- Inline CSS for styling and colors
- SVG or CSS for the pie chart (no Chart.js or Plotly needed)
- Clean, modern design with a dark sidebar for the tree and light main area

Key interactions:
- Click folder → expand/collapse children
- Hover file → show full path and size
- Folders show aggregated line count and file count
- Sort files by size or name

## Arguments

$ARGUMENTS can specify:
- A subdirectory to focus on: `/visualize scripts/`
- A submodule: `/visualize repositories/ai-initiatives-observer`
- Default: current directory
