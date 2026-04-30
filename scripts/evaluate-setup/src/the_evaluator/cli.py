from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from the_evaluator.config.loader import load_config
from the_evaluator.engine.engine import lint_directory
from the_evaluator.engine.fixer import apply_fixes
from the_evaluator.engine.registry import clear_rules
from the_evaluator.engine.types import Severity
from the_evaluator.rules import register_all_rules


def _result_to_dict(result) -> dict:
    return {
        "name": result.skill_name,
        "path": result.skill_path,
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
@click.option("--config", "config_file", type=click.Path(), default=None, help="Path to .evaluator.yaml")
@click.option("--fix", is_flag=True, help="Auto-fix trivial issues")
def scan(path: str, preset: str | None, config_file: str | None, fix: bool):
    """Run Layer 1 static analysis on skills."""
    clear_rules()
    register_all_rules()

    config = load_config(scan_path=path, preset_override=preset, config_file=config_file)
    results = lint_directory(path, config.rules)

    if fix:
        all_diagnostics = [d for r in results for d in r.diagnostics]
        fix_results = apply_fixes(all_diagnostics)
        for fr in fix_results:
            print(f"Fixed {fr.fixes_applied} issue(s) in {fr.file_path}", file=sys.stderr)

    total_tokens = sum(r.tokens for r in results)
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)
    total_info = sum(r.info_count for r in results)
    total_fixable = sum(r.fixable_count for r in results)
    total_suppressed = sum(r.suppression_count for r in results)

    print(
        f"Scanned {len(results)} skill(s) | "
        f"{total_tokens:,} tokens | "
        f"{total_errors} error(s), {total_warnings} warning(s), {total_info} info",
        file=sys.stderr,
    )

    output = {
        "scan_path": path,
        "preset": config.preset_name,
        "total_skills": len(results),
        "total_tokens": total_tokens,
        "summary": {
            "errors": total_errors,
            "warnings": total_warnings,
            "info": total_info,
            "fixable": total_fixable,
            "suppressed": total_suppressed,
        },
        "skills": [_result_to_dict(r) for r in results],
    }

    json.dump(output, sys.stdout, indent=2)
    print(file=sys.stdout)

    exit_code = 1 if total_errors > 0 else 0
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
