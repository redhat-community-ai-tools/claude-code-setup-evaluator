#!/usr/bin/env python3
"""Session-start orchestrator for AI tool hooks.

Runs at the start of AI tool sessions and collects context from multiple
sources into a unified output.

Supports two output modes:
  - Plain text (default): For tools that capture stdout directly
  - JSON (--tool <name>): For tools that require a JSON hook protocol
    Each tool's JSON schema is defined in FORMATTERS.

Adding a new tool: add an entry to FORMATTERS and create the tool's config file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# Import session-start tasks
from repository_status import run_repository_status
from session_context import SessionContext

FORMATTERS: dict[str, Any] = {}


def collect_context() -> str:
    """Run all session-start tasks and return the rendered context."""
    ctx = SessionContext()

    # Get repository root (scripts are in .ai-workspace/scripts/)
    repo_root = Path(__file__).parent.parent.parent

    # Gather repository status for agent context
    run_repository_status(ctx, repo_root)

    return ctx.render()


def main() -> None:
    """Run session-start tasks and output context in the requested format."""
    parser = argparse.ArgumentParser(description="Session-start context collector")
    parser.add_argument(
        "--tool",
        choices=FORMATTERS,
        help="Output JSON in the specified tool's hook format. Without this flag, outputs plain text.",
    )
    args = parser.parse_args()

    # Tools with JSON protocols send input on stdin; consume it so the
    # process doesn't hang.
    if args.tool:
        sys.stdin.read()

    output = collect_context()

    if args.tool:
        response = FORMATTERS[args.tool](output) if output else {}
        json.dump(response, sys.stdout)
    else:
        if output:
            print(output)


if __name__ == "__main__":
    main()
