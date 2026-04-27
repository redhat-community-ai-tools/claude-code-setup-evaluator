#!/bin/bash
# Auto-skill suggestion hook
# Reads the tool input from CLAUDE_TOOL_INPUT and suggests relevant skills
# based on what files are being touched or what commands are being run.

INPUT="${CLAUDE_TOOL_INPUT:-}"

# Extract the command or file path from the tool input
CMD=$(echo "$INPUT" | grep -oP '"command"\s*:\s*"\K[^"]+' 2>/dev/null)
FILE=$(echo "$INPUT" | grep -oP '"file_path"\s*:\s*"\K[^"]+' 2>/dev/null)
CONTENT=$(echo "$INPUT" | grep -oP '"content"\s*:\s*"\K[^"]{0,200}' 2>/dev/null)

SKILLS=""

# Check file extensions and paths
if echo "$FILE" | grep -qiE 'test_|_test\.py|tests/|\.py$'; then
    SKILLS="$SKILLS python-conventions"
fi

if echo "$FILE" | grep -qiE '\.env|\.gitignore|secret|credential|token'; then
    SKILLS="$SKILLS security-check"
fi

if echo "$FILE" | grep -qiE 'pipeline|fetch_|group_|filter_|summarize_|categorize_'; then
    SKILLS="$SKILLS data-pipeline-patterns"
fi

if echo "$FILE" | grep -qiE 'api|client|request|fetch'; then
    SKILLS="$SKILLS python-conventions"
fi

# Check command content
if echo "$CMD" | grep -qiE 'pytest|test|coverage'; then
    SKILLS="$SKILLS python-conventions"
fi

if echo "$CMD" | grep -qiE 'git (commit|push|merge|rebase)'; then
    SKILLS="$SKILLS security-check"
fi

# Deduplicate and output
if [ -n "$SKILLS" ]; then
    UNIQUE=$(echo "$SKILLS" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ', ' | sed 's/,$//')
    echo "Relevant skills: $UNIQUE" >&2
fi

exit 0
