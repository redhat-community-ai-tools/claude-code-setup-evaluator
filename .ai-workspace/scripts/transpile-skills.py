#!/usr/bin/env python3
"""
Validate and distribute skills to configured target directories.

Validates SKILL.md files following the Agent Skills specification
(https://agentskills.io/specification) and distributes skills to target
directories configured in ai-workspace.toml under distribution.skills_paths.

Usage:
  uv run .ai-workspace/scripts/transpile-skills.py             # Validate + distribute
  uv run .ai-workspace/scripts/transpile-skills.py --validate  # Validate only

Required fields in SKILL.md:
- name: 1-64 chars, lowercase alphanumeric + hyphens, must match directory name
- description: 1-1024 chars, describes what the skill does and when to use it
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

# Add lib directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from config import load_config

# Constants
SKILLS_DIR = "skills"
NAME_MAX_LENGTH = 64
DESCRIPTION_MAX_LENGTH = 1024
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Pattern for valid skill names: lowercase alphanumeric and hyphens
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass
class Skill:
    """A parsed skill with metadata."""

    name: str
    description: str
    source_path: Path  # Path to skill directory


def extract_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from SKILL.md content."""
    match = FRONTMATTER_PATTERN.match(content)

    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def validate_name(name: str, expected_name: str) -> list[str]:
    """Validate name field per Agent Skills spec."""
    errors = []

    if not name:
        return ["Missing required field: 'name'"]

    # Length check
    if len(name) > NAME_MAX_LENGTH:
        errors.append(f"'name' exceeds {NAME_MAX_LENGTH} characters (got {len(name)})")

    # Format check: lowercase alphanumeric and hyphens only
    if not NAME_PATTERN.match(name):
        errors.append(
            f"'name' must be lowercase alphanumeric with hyphens, "
            f"no leading/trailing/consecutive hyphens (got '{name}')"
        )

    # Must match directory name
    if name != expected_name:
        errors.append(
            f"'name' must match directory name: expected '{expected_name}', got '{name}'"
        )

    return errors


def validate_description(description: str) -> list[str]:
    """Validate description field per Agent Skills spec."""
    if not description:
        return ["Missing required field: 'description'"]

    if len(description) > DESCRIPTION_MAX_LENGTH:
        return [
            f"'description' exceeds {DESCRIPTION_MAX_LENGTH} characters (got {len(description)})"
        ]

    return []


def parse_skill(skill_dir: Path) -> tuple[Skill | None, list[str]]:
    """Parse and validate a skill directory. Returns (Skill, errors)."""
    errors = []
    expected_name = skill_dir.name
    skill_file = skill_dir / "SKILL.md"

    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError as e:
        return None, [f"Cannot read file: {e}"]

    # Check for frontmatter
    frontmatter = extract_frontmatter(content)
    if frontmatter is None:
        return None, [
            "Missing or invalid YAML frontmatter. Must start with '---', contain YAML, and end with '---'"
        ]

    # Validate name field
    name = frontmatter.get("name", "")
    if isinstance(name, str):
        name = name.strip()
    else:
        name = ""
    errors.extend(validate_name(name, expected_name))

    # Validate description field
    description = frontmatter.get("description", "")
    if isinstance(description, str):
        description = description.strip()
    else:
        description = ""
    errors.extend(validate_description(description))

    # Check for markdown body after frontmatter
    match = FRONTMATTER_PATTERN.match(content)
    if match:
        body = content[match.end() :].strip()
        if not body:
            errors.append(
                "Empty markdown body - SKILL.md should contain instructions after frontmatter"
            )

    if errors:
        return None, errors

    return Skill(name=name, description=description, source_path=skill_dir), []


def find_skills(base_dir: Path) -> list[Path]:
    """Find all skill directories (those containing SKILL.md)."""
    skills_dir = base_dir / SKILLS_DIR
    if not skills_dir.exists():
        return []

    return sorted(
        item
        for item in skills_dir.iterdir()
        if item.is_dir()
        and not item.name.startswith(".")
        and (item / "SKILL.md").exists()
    )


def validate_skills(base_dir: Path) -> tuple[list[Skill], list[str]]:
    """Parse and validate all skill files."""
    skills, all_errors = [], []

    for skill_dir in find_skills(base_dir):
        skill, errors = parse_skill(skill_dir)

        if errors:
            all_errors.extend(f"{skill_dir.name}: {e}" for e in errors)
            print(f"✗ {skill_dir.name}:")
            for error in errors:
                print(f"    - {error}")
        else:
            skills.append(skill)
            print(f"✓ {skill.name}")

    return skills, all_errors


def create_symlink(source: Path, target: Path) -> str:
    """Create or update a symlink using a relative path. Returns status."""
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_symlink():
        if target.resolve() == source.resolve():
            return "unchanged"
        target.unlink()
    elif target.exists():
        return "skipped (not a symlink)"

    rel_path = os.path.relpath(source, target.parent)
    target.symlink_to(rel_path)
    return "created"


def distribute(skills: list[Skill], target_paths: list[str], base_dir: Path) -> None:
    """Distribute skills to all configured target directories."""
    if not skills:
        print("No skills to distribute")
        return

    print("\nDistributing skills...")

    for skill in skills:
        for target_path in target_paths:
            target = base_dir / target_path / skill.name
            status = create_symlink(skill.source_path, target)
            print(f"  {target_path}/{skill.name}/ ({status})")

    print(f"\n✓ Distributed {len(skills)} skill(s) to {len(target_paths)} target(s)")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument(
        "--validate", action="store_true", help="Validate only, don't distribute"
    )
    args = parser.parse_args()

    # Scripts are in .ai-workspace/scripts/, so go up two levels
    base_dir = Path(__file__).parent.parent.parent

    # Load configuration
    config = load_config(base_dir / "ai-workspace.toml")
    target_paths = config.distribution.skills_paths

    print(
        "Validating skills..."
        if args.validate
        else "Validating and distributing skills..."
    )
    print(f"Skills directory: {base_dir / SKILLS_DIR}\n")

    skills, errors = validate_skills(base_dir)

    if not skills and not errors:
        print("No skills found")
        return

    print(f"\n✓ {len(skills)} skill(s) validated")

    if errors:
        print(f"\n{len(errors)} error(s)", file=sys.stderr)
        sys.exit(1)

    if not args.validate:
        distribute(skills, target_paths, base_dir)


if __name__ == "__main__":
    main()
