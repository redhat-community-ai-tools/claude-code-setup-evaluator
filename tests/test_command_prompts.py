"""Structural validation tests for command.md and SKILL.md files.

Catches real issues: oversized prompts, missing frontmatter, coercive
trigger language, and orphan file references.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
COMMANDS_DIR = ROOT / "commands"
SKILLS_DIR = ROOT / "skills"

# Thresholds
COMMAND_SIZE_WARNING_KB = 15
COMMAND_SIZE_ERROR_KB = 30
SKILL_MAX_LINES = 500

# Patterns that override user autonomy in skill descriptions
COERCIVE_PATTERNS = [
    re.compile(r"\bYou MUST\b", re.IGNORECASE),
    re.compile(r"\bALWAYS use this\b", re.IGNORECASE),
    re.compile(r"\bNEVER skip\b", re.IGNORECASE),
    re.compile(r"\bMUST use this before\b", re.IGNORECASE),
    re.compile(r"\bMUST be used\b", re.IGNORECASE),
]


def _parse_frontmatter(path: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file."""
    text = path.read_text()
    if not text.startswith("---"):
        return None
    end = text.index("---", 3)
    return yaml.safe_load(text[3:end])


def _get_command_files() -> list[Path]:
    return sorted(COMMANDS_DIR.glob("*/command.md"))


def _get_skill_files() -> list[Path]:
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


# ---------------------------------------------------------------------------
# Command prompt tests
# ---------------------------------------------------------------------------

class TestCommandPromptStructure:

    def test_commands_exist(self):
        commands = _get_command_files()
        assert len(commands) > 0, "No command.md files found"

    @pytest.mark.parametrize("cmd_path", _get_command_files(), ids=lambda p: p.parent.name)
    def test_command_has_frontmatter(self, cmd_path: Path):
        content = cmd_path.read_text()
        assert content.startswith("---"), (
            f"{cmd_path.parent.name}/command.md missing YAML frontmatter"
        )

    @pytest.mark.parametrize("cmd_path", _get_command_files(), ids=lambda p: p.parent.name)
    def test_command_has_description(self, cmd_path: Path):
        fm = _parse_frontmatter(cmd_path)
        assert fm is not None, f"{cmd_path.parent.name}: no frontmatter"
        desc = fm.get("description", "")
        assert desc and len(str(desc).strip()) > 5, (
            f"{cmd_path.parent.name}: description missing or too short"
        )

    @pytest.mark.parametrize("cmd_path", _get_command_files(), ids=lambda p: p.parent.name)
    def test_command_size_warning(self, cmd_path: Path):
        size_kb = cmd_path.stat().st_size / 1024
        assert size_kb < COMMAND_SIZE_WARNING_KB, (
            f"{cmd_path.parent.name}/command.md is {size_kb:.1f}KB "
            f"(>{COMMAND_SIZE_WARNING_KB}KB) — consider splitting into "
            f"command.md + reference files"
        )

    @pytest.mark.parametrize("cmd_path", _get_command_files(), ids=lambda p: p.parent.name)
    def test_command_size_error(self, cmd_path: Path):
        size_kb = cmd_path.stat().st_size / 1024
        assert size_kb < COMMAND_SIZE_ERROR_KB, (
            f"{cmd_path.parent.name}/command.md is {size_kb:.1f}KB "
            f"(>{COMMAND_SIZE_ERROR_KB}KB) — strongly recommend splitting"
        )

    @pytest.mark.parametrize("cmd_path", _get_command_files(), ids=lambda p: p.parent.name)
    def test_no_orphan_script_references(self, cmd_path: Path):
        content = cmd_path.read_text()
        # Find .py script references that look like file paths (not inline code examples)
        script_refs = re.findall(r'(?:run|exec|python)\s+["\']?(\S+\.py)', content)
        cmd_dir = cmd_path.parent
        for ref in script_refs:
            ref_path = ref.strip("\"'")
            # Skip references with variables or absolute paths
            if "$" in ref_path or ref_path.startswith("/"):
                continue
            # Check relative to command dir
            if not (cmd_dir / ref_path).exists() and not (ROOT / ref_path).exists():
                # Skip if it looks like a generic example rather than a real reference
                if "example" in ref_path.lower() or "your-" in ref_path:
                    continue
                pytest.fail(
                    f"{cmd_path.parent.name}: references script '{ref_path}' "
                    f"that doesn't exist"
                )


# ---------------------------------------------------------------------------
# Skill prompt tests
# ---------------------------------------------------------------------------

class TestSkillPromptStructure:

    def test_skills_exist(self):
        skills = _get_skill_files()
        assert len(skills) > 0, "No SKILL.md files found"

    @pytest.mark.parametrize("skill_path", _get_skill_files(), ids=lambda p: p.parent.name)
    def test_skill_has_frontmatter(self, skill_path: Path):
        content = skill_path.read_text()
        assert content.startswith("---"), (
            f"{skill_path.parent.name}/SKILL.md missing YAML frontmatter"
        )

    @pytest.mark.parametrize("skill_path", _get_skill_files(), ids=lambda p: p.parent.name)
    def test_skill_has_description(self, skill_path: Path):
        fm = _parse_frontmatter(skill_path)
        assert fm is not None, f"{skill_path.parent.name}: no frontmatter"
        desc = fm.get("description", "")
        assert desc and len(str(desc).strip()) > 10, (
            f"{skill_path.parent.name}: description missing or too short"
        )

    @pytest.mark.parametrize("skill_path", _get_skill_files(), ids=lambda p: p.parent.name)
    def test_no_coercive_trigger_language(self, skill_path: Path):
        """Skills should guide, not mandate. Coercive language in descriptions
        overrides user autonomy and makes skills behave like forced commands."""
        fm = _parse_frontmatter(skill_path)
        if fm is None:
            return
        desc = str(fm.get("description", ""))
        for pattern in COERCIVE_PATTERNS:
            match = pattern.search(desc)
            if match:
                pytest.fail(
                    f"{skill_path.parent.name}: description uses coercive language "
                    f"'{match.group()}' — skill descriptions should guide activation, "
                    f"not mandate it. Use 'Use when...' instead."
                )

    @pytest.mark.parametrize("skill_path", _get_skill_files(), ids=lambda p: p.parent.name)
    def test_skill_line_count(self, skill_path: Path):
        lines = skill_path.read_text().splitlines()
        assert len(lines) <= SKILL_MAX_LINES, (
            f"{skill_path.parent.name}/SKILL.md has {len(lines)} lines "
            f"(>{SKILL_MAX_LINES}) — split into SKILL.md + reference files"
        )

    @pytest.mark.parametrize("skill_path", _get_skill_files(), ids=lambda p: p.parent.name)
    def test_no_orphan_references(self, skill_path: Path):
        """If a SKILL.md references files in skills/ or guidelines.md,
        those files must exist."""
        content = skill_path.read_text()
        skill_dir = skill_path.parent

        # Check for references to skills/*.md
        skill_refs = re.findall(r'`skills/([^`]+\.md)`', content)
        # Also catch: Read `skills/foo.md` or Read skills/foo.md
        skill_refs += re.findall(r'Read\s+`?skills/([^\s`]+\.md)', content)

        for ref in set(skill_refs):
            ref_path = skill_dir / "skills" / ref
            assert ref_path.exists(), (
                f"{skill_path.parent.name}: references 'skills/{ref}' "
                f"but {ref_path} doesn't exist"
            )

        # Check for guidelines.md reference
        if "guidelines.md" in content:
            guidelines = skill_dir / "guidelines.md"
            assert guidelines.exists(), (
                f"{skill_path.parent.name}: references guidelines.md "
                f"but {guidelines} doesn't exist"
            )
