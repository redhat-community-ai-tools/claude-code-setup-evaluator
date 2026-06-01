#!/usr/bin/env python3
"""One-time workspace setup for new projects created from the template.

Usage:
    uv run .ai-workspace/scripts/setup.py

Handles initial workspace configuration. Safe to re-run - all steps are
idempotent.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# Task infrastructure
# ---------------------------------------------------------------------------


@dataclass
class TaskResult:
    """Outcome of a setup task."""

    status: Literal["ok", "skip", "warn"]
    message: str


# Type alias for task functions: receive the repo root, return a result.
TaskFn = Callable[[Path], TaskResult]

# Status indicators for terminal output.
STATUS_ICONS = {"ok": "+", "skip": "-", "warn": "!"}


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process (never raises)."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# Tasks
#
# Each task is a function that takes the repo root and returns a TaskResult.
# To add a new setup step, define a function here and add it to TASKS below.
# ---------------------------------------------------------------------------


def init_submodules(base_dir: Path) -> TaskResult:
    """Initialize git submodules if any are configured."""
    if not (base_dir / ".gitmodules").exists():
        return TaskResult("skip", "No submodules configured")

    result = _run(
        ["git", "submodule", "update", "--init", "--recursive"],
        cwd=base_dir,
    )
    if result.returncode == 0:
        return TaskResult("ok", "Initialized submodules")
    return TaskResult("warn", f"Submodule init failed: {result.stderr.strip()}")


def install_precommit_hooks(base_dir: Path) -> TaskResult:
    """Install pre-commit hooks."""
    result = _run(["uv", "run", "pre-commit", "install"], cwd=base_dir)
    if result.returncode == 0:
        return TaskResult("ok", "Installed pre-commit hooks")
    return TaskResult("warn", f"pre-commit install failed: {result.stderr.strip()}")


def validate_workspace(base_dir: Path) -> TaskResult:
    """Run pre-commit to align workspace and validate configuration."""
    result = _run(
        ["uv", "run", "pre-commit", "run", "--all-files"],
        cwd=base_dir,
    )
    # pre-commit exits non-zero when hooks modify files (expected on first run).
    # Re-run to confirm everything is clean.
    if result.returncode != 0:
        result = _run(
            ["uv", "run", "pre-commit", "run", "--all-files"],
            cwd=base_dir,
        )
    if result.returncode == 0:
        return TaskResult("ok", "Workspace validated (AGENTS.md generated)")
    return TaskResult("warn", f"Workspace validation failed: {result.stderr.strip()}")


# ---------------------------------------------------------------------------
# Task registry - add new steps here
# ---------------------------------------------------------------------------

TASKS: list[tuple[str, TaskFn]] = [
    ("Initialize submodules", init_submodules),
    ("Install pre-commit hooks", install_precommit_hooks),
    ("Validate workspace", validate_workspace),
]

NEXT_STEPS = """
Setup complete! Next steps:

  1. Clone your repos:
     cd repositories/ && git clone <your-repo-url>

  2. Start your AI tool from the workspace root:
     claude  (or open in Cursor)

  3. Tell the AI which repo to focus on, or type /focus

  See instructions.md for the full guide."""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_prerequisites() -> None:
    """Verify required tools are available."""
    if not shutil.which("git"):
        print("Error: git is not installed or not in PATH.")
        sys.exit(1)

    result = _run(["git", "rev-parse", "--git-dir"])
    if result.returncode != 0:
        print("Error: Not inside a git repository.")
        sys.exit(1)


def main() -> None:
    """Run all setup tasks."""
    # Scripts are in .ai-workspace/scripts/, so go up two levels.
    base_dir = Path(__file__).parent.parent.parent

    print("Setting up workspace...\n")
    check_prerequisites()

    for _name, task_fn in TASKS:
        result = task_fn(base_dir)
        icon = STATUS_ICONS[result.status]
        print(f"  [{icon}] {result.message}")

    print(NEXT_STEPS)


if __name__ == "__main__":
    main()
