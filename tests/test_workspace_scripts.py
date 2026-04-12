"""Tests for workspace infrastructure scripts.

Verifies that align-workspace, transpile-commands, and transpile-skills
produce correct output and don't silently lose content.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


def run_script(script_name: str) -> subprocess.CompletedProcess:
    """Run a workspace script and return the result."""
    script = ROOT / ".ai-workspace" / "scripts" / script_name
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


class TestAlignWorkspace:
    def test_runs_successfully(self):
        result = run_script("align-workspace.py")
        assert result.returncode == 0, f"align-workspace failed: {result.stderr}"

    def test_generates_agents_md(self):
        run_script("align-workspace.py")
        agents_md = ROOT / "AGENTS.md"
        assert agents_md.exists(), "AGENTS.md not generated"
        content = agents_md.read_text()
        assert len(content) > 100, "AGENTS.md is suspiciously short"

    def test_agents_md_contains_project_context(self):
        run_script("align-workspace.py")
        content = (ROOT / "AGENTS.md").read_text()
        assert "Data Science team" in content, "Project context missing from AGENTS.md"

    def test_agents_md_contains_critical_requirements(self):
        run_script("align-workspace.py")
        content = (ROOT / "AGENTS.md").read_text()
        assert "Critical Requirements" in content

    def test_claude_md_is_symlink_to_agents_md(self):
        claude_md = ROOT / "CLAUDE.md"
        assert claude_md.is_symlink(), "CLAUDE.md should be a symlink"
        assert claude_md.resolve() == (ROOT / "AGENTS.md").resolve()


class TestTranspileCommands:
    def test_runs_successfully(self):
        result = run_script("transpile-commands.py")
        assert result.returncode == 0, f"transpile-commands failed: {result.stderr}"

    def test_command_count_matches_across_tools(self):
        """All tool directories should have the same number of commands."""
        run_script("transpile-commands.py")

        source_commands = list((ROOT / "commands").glob("*/command.md"))
        claude_commands = list((ROOT / ".claude" / "commands").glob("*.md"))
        cursor_commands = list((ROOT / ".cursor" / "commands").glob("*.md"))

        assert len(source_commands) > 0, "No source commands found"
        assert len(claude_commands) == len(source_commands), (
            f"Claude commands ({len(claude_commands)}) != source ({len(source_commands)})"
        )
        assert len(cursor_commands) == len(source_commands), (
            f"Cursor commands ({len(cursor_commands)}) != source ({len(source_commands)})"
        )

    def test_no_command_lost(self):
        """Every source command should have a Claude and Cursor counterpart."""
        run_script("transpile-commands.py")

        source_names = {p.parent.name for p in (ROOT / "commands").glob("*/command.md")}
        claude_names = {p.stem for p in (ROOT / ".claude" / "commands").glob("*.md")}
        cursor_names = {p.stem for p in (ROOT / ".cursor" / "commands").glob("*.md")}

        missing_claude = source_names - claude_names
        missing_cursor = source_names - cursor_names

        assert not missing_claude, f"Commands missing from .claude/commands/: {missing_claude}"
        assert not missing_cursor, f"Commands missing from .cursor/commands/: {missing_cursor}"


class TestTranspileSkills:
    def test_runs_successfully(self):
        result = run_script("transpile-skills.py")
        assert result.returncode == 0, f"transpile-skills failed: {result.stderr}"

    def test_skill_count_matches(self):
        """Cursor rules should match source skills count."""
        run_script("transpile-skills.py")

        source_skills = list((ROOT / "skills").glob("*/SKILL.md"))
        cursor_rules = list((ROOT / ".cursor" / "rules").glob("*.mdc"))

        assert len(source_skills) > 0, "No source skills found"
        assert len(cursor_rules) == len(source_skills), (
            f"Cursor rules ({len(cursor_rules)}) != source skills ({len(source_skills)})"
        )

    def test_no_skill_lost(self):
        """Every source skill should have a Cursor rule counterpart."""
        run_script("transpile-skills.py")

        source_names = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
        cursor_names = {p.stem for p in (ROOT / ".cursor" / "rules").glob("*.mdc")}

        missing = source_names - cursor_names
        assert not missing, f"Skills missing from .cursor/rules/: {missing}"

    def test_no_stale_cursor_rules(self):
        """Cursor rules should not have entries for removed skills."""
        run_script("transpile-skills.py")

        source_names = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
        cursor_names = {p.stem for p in (ROOT / ".cursor" / "rules").glob("*.mdc")}

        stale = cursor_names - source_names
        assert not stale, f"Stale Cursor rules for removed skills: {stale}"
