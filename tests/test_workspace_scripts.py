"""Tests for workspace infrastructure scripts.

Verifies that transpile-commands and transpile-skills
produce correct output and don't silently lose content.
"""

import importlib.util
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


def _import_script(name: str):
    """Import a script from .ai-workspace/scripts/ by filename."""
    lib_path = str(ROOT / ".ai-workspace" / "lib")
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)

    script_path = ROOT / ".ai-workspace" / "scripts" / name
    module_name = name.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_skills_mod = _import_script("transpile-skills.py")
_commands_mod = _import_script("transpile-commands.py")


class TestCLAUDEmd:
    def test_claude_md_exists(self):
        claude_md = ROOT / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md not found"

    def test_claude_md_contains_critical_requirements(self):
        content = (ROOT / "CLAUDE.md").read_text()
        assert "Critical Requirements" in content


class TestTranspileCommands:
    def test_runs_successfully(self):
        result = run_script("transpile-commands.py")
        assert result.returncode == 0, f"transpile-commands failed: {result.stderr}"

    def test_command_count_matches(self):
        """Claude commands directory should have same count as source."""
        run_script("transpile-commands.py")

        source_commands = list((ROOT / "commands").glob("*/command.md"))
        claude_commands = list((ROOT / ".claude" / "commands").glob("*.md"))

        assert len(source_commands) > 0, "No source commands found"
        assert len(claude_commands) == len(source_commands), (
            f"Claude commands ({len(claude_commands)}) != source ({len(source_commands)})"
        )

    def test_no_command_lost(self):
        """Every source command should have a Claude counterpart."""
        run_script("transpile-commands.py")

        source_names = {p.parent.name for p in (ROOT / "commands").glob("*/command.md")}
        claude_names = {p.stem for p in (ROOT / ".claude" / "commands").glob("*.md")}

        missing_claude = source_names - claude_names
        assert not missing_claude, f"Commands missing from .claude/commands/: {missing_claude}"


class TestTranspileSkills:
    def test_runs_successfully(self):
        result = run_script("transpile-skills.py")
        assert result.returncode == 0, f"transpile-skills failed: {result.stderr}"


class TestSkillValidationErrors:
    """Error-case tests for skill validation logic."""

    def test_missing_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter\nJust content.")

        skill, errors = _skills_mod.parse_skill(skill_dir)
        assert skill is None
        assert any("frontmatter" in e.lower() for e in errors)

    def test_invalid_yaml_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n: [invalid yaml\n---\n# Body")

        skill, errors = _skills_mod.parse_skill(skill_dir)
        assert skill is None
        assert any("frontmatter" in e.lower() for e in errors)

    def test_missing_name_field(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            '---\ndescription: "A skill"\n---\n# Body\nContent here.'
        )

        skill, errors = _skills_mod.parse_skill(skill_dir)
        assert skill is None
        assert any("name" in e.lower() for e in errors)

    def test_missing_description_field(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\n---\n# Body\nContent here."
        )

        skill, errors = _skills_mod.parse_skill(skill_dir)
        assert skill is None
        assert any("description" in e.lower() for e in errors)

    def test_invalid_name_format(self, tmp_path):
        skill_dir = tmp_path / "My_Skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            '---\nname: My_Skill\ndescription: "A skill"\n---\n# Body\nContent.'
        )

        skill, errors = _skills_mod.parse_skill(skill_dir)
        assert skill is None
        assert any("lowercase" in e.lower() or "alphanumeric" in e.lower() for e in errors)

    def test_name_doesnt_match_directory(self, tmp_path):
        skill_dir = tmp_path / "actual-name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            '---\nname: wrong-name\ndescription: "A skill"\n---\n# Body\nContent.'
        )

        skill, errors = _skills_mod.parse_skill(skill_dir)
        assert skill is None
        assert any("match directory" in e.lower() for e in errors)

    def test_empty_markdown_body(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            '---\nname: my-skill\ndescription: "A skill"\n---\n'
        )

        skill, errors = _skills_mod.parse_skill(skill_dir)
        assert skill is None
        assert any("empty" in e.lower() and "body" in e.lower() for e in errors)


class TestSkillSuggestHook:
    """Validate that skill-suggest.sh only references skills that actually exist."""

    def test_all_suggested_skills_exist(self):
        hook_path = ROOT / ".ai-workspace" / "scripts" / "skill-suggest.sh"
        hook_content = hook_path.read_text()

        existing_skills = {
            p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")
        }

        import re

        suggested = set(re.findall(r'SKILLS="\$SKILLS\s+([a-z0-9-]+)"', hook_content))
        ghost_skills = suggested - existing_skills
        assert not ghost_skills, (
            f"skill-suggest.sh references non-existent skills: {ghost_skills}. "
            f"Existing skills: {existing_skills}"
        )


class TestCommandValidationErrors:
    """Error-case tests for command validation logic."""

    def test_missing_frontmatter(self, tmp_path):
        cmd_file = tmp_path / "command.md"
        cmd_file.write_text("# No frontmatter\nJust content.")

        with pytest.raises(ValueError, match="frontmatter"):
            _commands_mod.parse_command(cmd_file)

    def test_invalid_yaml(self, tmp_path):
        cmd_file = tmp_path / "command.md"
        cmd_file.write_text("---\n: [broken yaml\n---\n# Body")

        with pytest.raises(ValueError, match="[Yy]AML"):
            _commands_mod.parse_command(cmd_file)

    def test_missing_description(self, tmp_path):
        cmd_file = tmp_path / "command.md"
        cmd_file.write_text("---\ntitle: something\n---\n# Body\nContent.")

        with pytest.raises(ValueError, match="description"):
            _commands_mod.parse_command(cmd_file)

    def test_frontmatter_not_a_mapping(self, tmp_path):
        cmd_file = tmp_path / "command.md"
        cmd_file.write_text("---\n- a list item\n- another\n---\n# Body")

        with pytest.raises(ValueError, match="mapping"):
            _commands_mod.parse_command(cmd_file)
