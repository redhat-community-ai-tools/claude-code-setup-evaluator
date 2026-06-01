#!/usr/bin/env python3
"""
Transpile and distribute commands to tool-specific directories.

Scans commands/*/command.md files, validates YAML frontmatter, and distributes
to configured target directories using symlinks (default) or frontmatter
stripping. Distribution targets and method overrides are configured in
ai-workspace.toml under [distribution].

Usage:
  uv run .ai-workspace/scripts/transpile-commands.py             # Validate + distribute
  uv run .ai-workspace/scripts/transpile-commands.py --validate  # Validate only
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import yaml

# Add lib directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from config import load_config

VALID_METHODS = {"symlink", "strip_frontmatter"}


class DistMethod(Enum):
    """How to distribute a command to a target directory."""

    SYMLINK = auto()  # Symlink to source (for tools that ignore unknown frontmatter)
    STRIP_FRONTMATTER = auto()  # Write content with frontmatter stripped


@dataclass
class TargetConfig:
    """Configuration for a distribution target."""

    path: str  # Relative to workspace root
    method: DistMethod


COMMANDS_DIR = "commands"
COMMAND_FILENAME = "command.md"
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class Command:
    """A parsed command with metadata and content."""

    name: str
    description: str
    content: str  # Markdown content after frontmatter
    source_path: Path


def _resolve_method(path: str, overrides: dict[str, str]) -> DistMethod:
    """Determine distribution method for a path.

    Checks commands_overrides for an explicit method, otherwise defaults to symlink.
    """
    if path in overrides:
        method_str = overrides[path]
        if method_str == "strip_frontmatter":
            return DistMethod.STRIP_FRONTMATTER
        return DistMethod.SYMLINK

    return DistMethod.SYMLINK


def _build_targets(paths: list[str], overrides: dict[str, str]) -> tuple[list[TargetConfig], list[str]]:
    """Build target configs from paths and overrides. Returns (targets, errors)."""
    errors = []

    # Warn about override keys that don't reference any configured path
    for override_path in overrides:
        if override_path not in paths:
            print(f"  ⚠ Override '{override_path}' has no matching path in commands_paths (ignored)")

    # Validate override values are valid methods
    for override_path, method in overrides.items():
        if method not in VALID_METHODS:
            errors.append(
                f"Invalid method '{method}' for '{override_path}'. Valid methods: {', '.join(sorted(VALID_METHODS))}"
            )

    if errors:
        return [], errors

    targets = [TargetConfig(path=p, method=_resolve_method(p, overrides)) for p in paths]
    return targets, []


def parse_command(path: Path) -> Command:
    """Parse a command.md file, extracting frontmatter and content."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"Cannot read {path}: {e}") from e

    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        raise ValueError(f"No valid YAML frontmatter in {path}")

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error in {path}: {e}") from e

    if not isinstance(frontmatter, dict):
        raise ValueError(f"Frontmatter must be a YAML mapping in {path}")

    description = frontmatter.get("description", "").strip()
    if not description:
        raise ValueError(f"Missing required 'description' field in {path}")

    return Command(
        name=path.parent.name,
        description=description,
        content=text[match.end() :].strip(),
        source_path=path,
    )


def find_commands(base_dir: Path) -> list[Path]:
    """Find all command.md files in commands subdirectories."""
    commands_dir = base_dir / COMMANDS_DIR
    if not commands_dir.exists():
        return []

    return sorted(
        item / COMMAND_FILENAME
        for item in commands_dir.iterdir()
        if item.is_dir() and not item.name.startswith(".") and (item / COMMAND_FILENAME).exists()
    )


def validate_commands(base_dir: Path) -> tuple[list[Command], list[str]]:
    """Parse and validate all command files."""
    commands, errors = [], []

    for path in find_commands(base_dir):
        try:
            cmd = parse_command(path)
            commands.append(cmd)
            print(f"✓ {cmd.name}")
        except ValueError as e:
            errors.append(str(e))
            print(f"✗ {e}", file=sys.stderr)

    return commands, errors


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


def write_file(content: str, target: Path) -> str:
    """Write content to file. Returns status."""
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and target.read_text(encoding="utf-8") == content:
        return "unchanged"

    target.write_text(content, encoding="utf-8")
    return "written"


def distribute(commands: list[Command], targets: list[TargetConfig], base_dir: Path) -> None:
    """Distribute commands to all configured target directories."""
    if not commands:
        print("No commands to distribute")
        return

    print("\nDistributing commands...")

    for cmd in commands:
        for target_cfg in targets:
            target = base_dir / target_cfg.path / f"{cmd.name}.md"

            if target_cfg.method == DistMethod.STRIP_FRONTMATTER:
                status = write_file(cmd.content, target)
                method_label = "strip_frontmatter"
            else:
                status = create_symlink(cmd.source_path, target)
                method_label = "symlink"

            print(f"  {target_cfg.path}/{cmd.name}.md [{method_label}] ({status})")

    print(f"\n✓ Distributed {len(commands)} command(s) to {len(targets)} target(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--validate", action="store_true", help="Validate only, don't distribute")
    args = parser.parse_args()

    # Scripts are in .ai-workspace/scripts/, so go up two levels
    base_dir = Path(__file__).parent.parent.parent

    # Load configuration
    config = load_config(base_dir / "ai-workspace.toml")
    targets, config_errors = _build_targets(
        config.distribution.commands_paths,
        config.distribution.commands_overrides,
    )

    if config_errors:
        print("Configuration errors:", file=sys.stderr)
        for err in config_errors:
            print(f"  ✗ {err}", file=sys.stderr)
        sys.exit(1)

    print("Validating commands..." if args.validate else "Validating and distributing...")
    print(f"Base: {base_dir}\n")

    commands, errors = validate_commands(base_dir)

    if errors:
        print(f"\n{len(errors)} error(s)", file=sys.stderr)
        sys.exit(1)

    if not commands:
        print("No commands found")
        return

    print(f"\n✓ {len(commands)} command(s) validated")

    if not args.validate:
        distribute(commands, targets, base_dir)


if __name__ == "__main__":
    main()
