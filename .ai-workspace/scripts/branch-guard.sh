#!/usr/bin/env bash
# PreToolUse hook: warn (not block) when editing files on a default branch.
# Extracts the file path from CLAUDE_TOOL_INPUT, checks if it's inside
# repositories/, and warns if that repo is on main/master.
# Exits 0 always — advisory only.

FILE=$(echo "$CLAUDE_TOOL_INPUT" | grep -oP '"file_path"\s*:\s*"\K[^"]+' 2>/dev/null)
[ -z "$FILE" ] && exit 0

# Only care about files under repositories/
echo "$FILE" | grep -q "repositories/" || exit 0

# Extract the repo directory (repositories/<name>)
REPO_DIR=$(echo "$FILE" | grep -oP 'repositories/[^/]+')
[ -z "$REPO_DIR" ] && exit 0
[ -d "$REPO_DIR/.git" ] || exit 0

BRANCH=$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)
[ -z "$BRANCH" ] && exit 0

if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "WARNING: $REPO_DIR is on '$BRANCH'. Consider creating a feature branch before making changes."
  echo "  Run: git -C $REPO_DIR checkout -b <branch-name>"
fi

exit 0
