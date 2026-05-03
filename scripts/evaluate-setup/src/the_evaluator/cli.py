from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from the_evaluator.config.loader import load_config
from the_evaluator.engine.engine import (
    lint_claude_md,
    lint_command,
    lint_directory,
    lint_hooks,
    parse_skill,
)
from the_evaluator.engine.registry import clear_rules
from the_evaluator.rules import register_all_rules


def _result_to_dict(result) -> dict:
    return {
        "name": result.target_name,
        "path": result.target_path,
        "type": result.target_type,
        "tokens": result.tokens,
        "diagnostics": [
            {
                "rule_id": d.rule_id,
                "severity": d.severity.value,
                "message": d.message,
                "location": {
                    "file": d.location.file,
                    "start_line": d.location.start_line,
                },
                "category": d.category if isinstance(d.category, str) else d.category.value,
                **(
                    {
                        "fix": {
                            "description": d.fix.description,
                            "replacement": d.fix.replacement,
                        }
                    }
                    if d.fix
                    else {}
                ),
            }
            for d in result.diagnostics
        ],
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "info_count": result.info_count,
        "fixable_count": result.fixable_count,
        "suppression_count": result.suppression_count,
    }


@click.group()
def cli():
    """the-evaluator: evaluate your Claude Code setup."""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--preset",
    type=click.Choice(["recommended", "strict", "security"]),
    default=None,
    help="Evaluation preset (default: recommended)",
)
@click.option("--config", "config_file", type=click.Path(), default=None)
@click.option("--commands", is_flag=True, help="Also evaluate commands")
@click.option("--claude-md", "claude_md", is_flag=True, help="Also evaluate CLAUDE.md")
@click.option("--hooks", is_flag=True, help="Also evaluate hooks")
@click.option("--all", "scan_all", is_flag=True, help="Evaluate everything: skills + commands + CLAUDE.md + hooks")
@click.option("--target", default=None, help="Focus on a single skill by name")
def scan(
    path: str,
    preset: str | None,
    config_file: str | None,
    commands: bool,
    claude_md: bool,
    hooks: bool,
    scan_all: bool,
    target: str | None,
):
    """Run Layer 1 static analysis on your Claude Code setup."""
    clear_rules()
    register_all_rules()

    config = load_config(scan_path=path, preset_override=preset, config_file=config_file)
    all_results = []
    scan_path = Path(path)

    # --- Skills ---
    skill_results = lint_directory(path, config.rules)
    if target:
        all_results.extend([r for r in skill_results if r.target_name == target])
    else:
        all_results.extend(skill_results)

    # --- Commands ---
    if commands or scan_all:
        cmd_dirs = _find_commands(scan_path)
        for cmd_dir in cmd_dirs:
            all_results.append(lint_command(str(cmd_dir), config.rules))

    # --- CLAUDE.md ---
    if claude_md or scan_all:
        parsed_skills = [parse_skill(str(r.target_path)) for r in skill_results] if skill_results else []
        for claude_path in _find_claude_mds(scan_path):
            all_results.append(lint_claude_md(str(claude_path), config.rules, parsed_skills))

    # --- Hooks ---
    if hooks or scan_all:
        for settings_path in _find_settings(scan_path):
            all_results.append(lint_hooks(str(settings_path), config.rules))

    # --- Output ---
    total_tokens = sum(r.tokens for r in all_results)
    total_errors = sum(r.error_count for r in all_results)
    total_warnings = sum(r.warning_count for r in all_results)
    total_info = sum(r.info_count for r in all_results)
    total_fixable = sum(r.fixable_count for r in all_results)
    total_suppressed = sum(r.suppression_count for r in all_results)

    type_counts = {}
    for r in all_results:
        type_counts[r.target_type] = type_counts.get(r.target_type, 0) + 1

    summary_parts = []
    for t, c in sorted(type_counts.items()):
        summary_parts.append(f"{c} {t}(s)")

    print(
        f"Scanned {', '.join(summary_parts)} | "
        f"{total_tokens:,} tokens | "
        f"{total_errors} error(s), {total_warnings} warning(s), {total_info} info",
        file=sys.stderr,
    )

    output = {
        "scan_path": path,
        "preset": config.preset_name,
        "total_items": len(all_results),
        "total_tokens": total_tokens,
        "summary": {
            "errors": total_errors,
            "warnings": total_warnings,
            "info": total_info,
            "fixable": total_fixable,
            "suppressed": total_suppressed,
            "by_type": type_counts,
        },
        "items": [_result_to_dict(r) for r in all_results],
    }

    json.dump(output, sys.stdout, indent=2)
    print(file=sys.stdout)

    exit_code = 1 if total_errors > 0 else 0
    sys.exit(exit_code)


def _find_commands(scan_path: Path) -> list[Path]:
    """Find command directories under a path."""
    results = []
    commands_dir = scan_path / "commands"
    if not commands_dir.is_dir():
        commands_dir = scan_path
    for p in sorted(commands_dir.iterdir()):
        if p.is_dir() and (p / "command.md").exists():
            results.append(p)
    return results


def _find_claude_mds(scan_path: Path) -> list[Path]:
    """Find CLAUDE.md files."""
    results = []
    for name in ["CLAUDE.md", "CLAUDE.local.md"]:
        candidate = scan_path / name
        if candidate.exists():
            results.append(candidate)
    parent = scan_path.parent
    if parent != scan_path:
        for name in ["CLAUDE.md"]:
            candidate = parent / name
            if candidate.exists() and candidate not in results:
                results.append(candidate)
    return results


def _find_settings(scan_path: Path) -> list[Path]:
    """Find .claude/settings.json files."""
    results = []
    for candidate in [
        scan_path / ".claude" / "settings.json",
        scan_path / ".claude" / "settings.local.json",
    ]:
        if candidate.exists():
            results.append(candidate)
    return results


if __name__ == "__main__":
    cli()
