#!/usr/bin/env python3
"""Align workspace configuration with ai-workspace.toml."""

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from config import AIWorkspaceConfig, load_config

PLACEHOLDER_TAG = "<placeholder>"
FIX_COMMAND = "uv run .ai-workspace/scripts/align-workspace.py"


@dataclass
class AgentDoc:
    """Represents an agent documentation resource."""

    display_name: str
    description: str
    when_to_read: str
    doc_path: str


def is_safe_to_remove(dir_path: Path, readme_name: str = "README.md") -> bool:
    """Check if directory can be safely removed (only has template files)."""
    if not dir_path.exists():
        return True
    contents = list(dir_path.iterdir())
    if not contents:
        return True
    return len(contents) == 1 and contents[0].name == readme_name


def manage_features(config: AIWorkspaceConfig, base_dir: Path, *, check: bool = False) -> list[str]:
    """Ensure feature directories match config.

    In check mode, returns a list of issues found without modifying anything.
    In normal mode, applies changes and returns an empty list.
    """
    features = [
        ("skills", config.features.skills, "skills-readme.md"),
        ("commands", config.features.commands, "commands-readme.md"),
        ("agent-docs", config.features.agent_docs, "agent-docs-readme.md"),
    ]

    template_dir = base_dir / ".ai-workspace/templates"
    issues = []

    for dir_name, enabled, template_name in features:
        dir_path = base_dir / dir_name
        template_path = template_dir / template_name
        readme_path = dir_path / "README.md"

        if enabled:
            if check:
                if not dir_path.exists():
                    issues.append(f"Feature directory '{dir_name}/' is missing")
            else:
                dir_path.mkdir(exist_ok=True)
                if not readme_path.exists() and template_path.exists():
                    shutil.copy(template_path, readme_path)
                    print(f"Created {readme_path}")
        else:
            if dir_path.exists():
                if is_safe_to_remove(dir_path):
                    if check:
                        issues.append(f"Feature directory '{dir_name}/' should be removed (feature disabled)")
                    else:
                        shutil.rmtree(dir_path)
                        print(f"Removed {dir_path}/ (feature disabled)")
                else:
                    raise ValueError(
                        f"Cannot disable {dir_name}: directory has user content. "
                        f"Remove contents manually or keep feature enabled."
                    )

    return issues


def normalize_text(text: str) -> str:
    """Normalize multi-line text by joining lines within paragraphs."""
    if not text:
        return text

    result = []
    current_paragraph = []

    for line in text.split("\n"):
        stripped = line.strip()

        if not stripped:
            if current_paragraph:
                result.append(" ".join(current_paragraph))
                current_paragraph = []
            result.append("")
        else:
            current_paragraph.append(stripped)

    if current_paragraph:
        result.append(" ".join(current_paragraph))

    return "\n".join(result).strip()


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Returns:
        Tuple of (frontmatter_dict, remaining_content).
        Returns ({}, content) if no valid frontmatter found.
    """
    if not content.startswith("---"):
        return {}, content

    # Find the closing ---
    lines = content.split("\n")
    end_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index is None:
        return {}, content

    # Extract frontmatter YAML
    frontmatter_lines = lines[1:end_index]
    frontmatter_yaml = "\n".join(frontmatter_lines)

    try:
        data = yaml.safe_load(frontmatter_yaml)
        if not isinstance(data, dict):
            return {}, content
    except yaml.YAMLError:
        return {}, content

    # Remaining content after frontmatter
    remaining = "\n".join(lines[end_index + 1 :])
    return data, remaining


def load_agent_docs(base_dir: Path) -> list[AgentDoc]:
    """Load agent documentation from markdown files with frontmatter.

    Supports both flat files (agent-docs/doc.md) and nested directories
    (agent-docs/category/doc.md). Excludes README.md files.
    """
    docs_dir = base_dir / "agent-docs"
    if not docs_dir.exists():
        return []

    docs = []

    # Recursively find all .md files, excluding README.md
    for md_file in sorted(docs_dir.rglob("*.md")):
        if md_file.name.lower() == "readme.md":
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
            frontmatter, _ = parse_frontmatter(content)

            if not frontmatter:
                print(f"Warning: No frontmatter in {md_file}")
                continue

            # Map frontmatter fields (title -> display_name, when -> when_to_read)
            display_name = frontmatter.get("title", "").strip()
            description = normalize_text(frontmatter.get("description", ""))
            when_to_read = normalize_text(frontmatter.get("when", ""))

            if not display_name or not description or not when_to_read:
                print(f"Warning: Incomplete frontmatter in {md_file}")
                continue

            # Create relative path from base_dir
            doc_path = md_file.relative_to(base_dir).as_posix()
            docs.append(
                AgentDoc(
                    display_name=display_name,
                    description=description,
                    when_to_read=when_to_read,
                    doc_path=doc_path,
                )
            )
        except yaml.YAMLError as e:
            print(f"Warning: YAML error in {md_file}: {e}")
            continue

    return docs


def count_items(base_dir: Path, dir_name: str, pattern: str) -> int:
    """Count items matching pattern in a directory."""
    target_dir = base_dir / dir_name
    if not target_dir.exists():
        return 0

    count = 0
    for item in target_dir.iterdir():
        if item.is_dir() and not item.name.startswith(".") and (item / pattern).exists():
            count += 1
    return count


def load_project_content(base_dir: Path) -> str | None:
    """Load project-specific content from AGENTS.project.md."""
    project_file = base_dir / "AGENTS.project.md"
    if not project_file.exists():
        return None

    content = project_file.read_text(encoding="utf-8")

    # Check for placeholder tags
    if PLACEHOLDER_TAG in content:
        return None

    # Check if empty after stripping whitespace
    if not content.strip():
        return None

    return content.strip()


def render_agents_md_content(config: AIWorkspaceConfig, base_dir: Path) -> str:
    """Render AGENTS.md content from template and return as string."""
    template_dir = base_dir / ".ai-workspace/templates"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("AGENTS.md.j2")

    # Gather data
    agent_docs = load_agent_docs(base_dir) if config.features.agent_docs else []
    skills_count = count_items(base_dir, "skills", "SKILL.md") if config.features.skills else 0
    commands_count = count_items(base_dir, "commands", "command.md") if config.features.commands else 0
    project_content = load_project_content(base_dir)

    context = {
        "features": {
            "agent_docs": {
                "enabled": config.features.agent_docs,
                "docs": agent_docs,
            },
            "skills": {
                "enabled": config.features.skills,
                "count": skills_count,
            },
            "commands": {
                "enabled": config.features.commands,
                "count": commands_count,
            },
        },
        "project_content": project_content,
    }

    return template.render(**context)


def render_agents_md(config: AIWorkspaceConfig, base_dir: Path) -> None:
    """Render and write AGENTS.md."""
    rendered = render_agents_md_content(config, base_dir)
    agents_md_path = base_dir / "AGENTS.md"
    agents_md_path.write_text(rendered, encoding="utf-8")
    print(f"Generated {agents_md_path}")


def check_agents_md(config: AIWorkspaceConfig, base_dir: Path) -> list[str]:
    """Check if AGENTS.md is up to date. Returns list of issues."""
    rendered = render_agents_md_content(config, base_dir)
    agents_md_path = base_dir / "AGENTS.md"

    if not agents_md_path.exists():
        return ["AGENTS.md does not exist"]

    current = agents_md_path.read_text(encoding="utf-8")
    if current != rendered:
        return ["AGENTS.md is out of sync with source files"]

    return []


def run_validators(config: AIWorkspaceConfig, base_dir: Path) -> None:
    """Run feature-specific validators (validate only, no distribution)."""
    script_dir = base_dir / ".ai-workspace/scripts"

    if config.features.skills:
        subprocess.run(
            ["uv", "run", str(script_dir / "transpile-skills.py"), "--validate"],
            check=False,
        )

    if config.features.commands:
        subprocess.run(
            ["uv", "run", str(script_dir / "transpile-commands.py"), "--validate"],
            check=False,
        )


def main():
    parser = argparse.ArgumentParser(description="Align workspace configuration.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify workspace is aligned without modifying files.",
    )
    args = parser.parse_args()

    # Scripts are in .ai-workspace/scripts/, so go up two levels
    base_dir = Path(__file__).parent.parent.parent

    if args.check:
        print("Verifying workspace alignment...")
        print()
    else:
        print("Aligning workspace configuration...")
        print()

    # 1. Load and validate config
    try:
        config = load_config(base_dir / "ai-workspace.toml")
        print("Loaded ai-workspace.toml")
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # 2. Manage feature directories
    try:
        issues = manage_features(config, base_dir, check=args.check)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.check:
        # 3. Check AGENTS.md
        issues.extend(check_agents_md(config, base_dir))

        # 4. Run validators
        run_validators(config, base_dir)

        if issues:
            print()
            for issue in issues:
                print(f"  - {issue}")
            print()
            print(f"Run to fix: {FIX_COMMAND}")
            sys.exit(1)
        else:
            print()
            print("Workspace is aligned.")
    else:
        # 3. Render AGENTS.md
        render_agents_md(config, base_dir)

        # 4. Run validators
        run_validators(config, base_dir)

        print()
        print("Workspace alignment complete.")


if __name__ == "__main__":
    main()
