from __future__ import annotations

import re
from pathlib import Path

import tiktoken
import yaml

from the_evaluator.engine.registry import get_all_rules
from the_evaluator.engine.suppression import is_suppressed, parse_suppressions
from the_evaluator.engine.types import (
    Diagnostic,
    DiagnosticLocation,
    LintResult,
    ParsedAgent,
    ParsedClaudeMd,
    ParsedCommand,
    ParsedHooks,
    ParsedSkill,
    ReportDescriptor,
    RuleContext,
    Severity,
    TargetType,
)

_INTERPOLATION_RE = re.compile(r"\{\{(\w+)\}\}")

try:
    _ENCODER = tiktoken.encoding_for_model("claude-sonnet-4-20250514")
except Exception:
    _ENCODER = tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


def _interpolate(template: str, data: dict[str, str | int] | None) -> str:
    if not data:
        return template
    return _INTERPOLATION_RE.sub(
        lambda m: str(data.get(m.group(1), m.group(0))), template
    )


def parse_skill(skill_path: str) -> ParsedSkill:
    """Parse a skill directory or SKILL.md file into a ParsedSkill."""
    path = Path(skill_path)
    parse_errors: list[str] = []

    if path.is_file() and path.name.lower() == "skill.md":
        skill_dir = path.parent
        skill_md = path
    elif path.is_dir():
        skill_dir = path
        candidates = [p for p in path.iterdir() if p.name.lower() == "skill.md"]
        if candidates:
            skill_md = candidates[0]
        else:
            return ParsedSkill(
                dir_path=str(skill_dir),
                dir_name=skill_dir.name,
                skill_md_path=str(skill_dir / "SKILL.md"),
                raw_content="",
                frontmatter={},
                raw_frontmatter="",
                frontmatter_start_line=0,
                body="",
                body_start_line=0,
                files=_list_files(skill_dir),
                parse_errors=["SKILL.md not found"],
            )
    else:
        return ParsedSkill(
            dir_path=str(path),
            dir_name=path.name,
            skill_md_path=str(path),
            raw_content="",
            frontmatter={},
            raw_frontmatter="",
            frontmatter_start_line=0,
            body="",
            body_start_line=0,
            files=[],
            parse_errors=[f"Path does not exist: {path}"],
        )

    raw_content = skill_md.read_text()

    frontmatter: dict = {}
    raw_frontmatter = ""
    frontmatter_start_line = 0
    body = raw_content
    body_start_line = 1

    lines = raw_content.split("\n")
    if lines and lines[0].strip() == "---":
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx is not None:
            frontmatter_start_line = 1
            raw_frontmatter = "\n".join(lines[1:end_idx])
            body = "\n".join(lines[end_idx + 1 :])
            body_start_line = end_idx + 2

            try:
                parsed = yaml.safe_load(raw_frontmatter)
                if isinstance(parsed, dict):
                    frontmatter = parsed
                else:
                    parse_errors.append("Frontmatter is not a YAML mapping")
            except yaml.YAMLError as e:
                parse_errors.append(f"YAML parse error: {e}")
        else:
            parse_errors.append("Frontmatter opening '---' found but no closing '---'")

    tokens = _count_tokens(raw_content)

    return ParsedSkill(
        dir_path=str(skill_dir),
        dir_name=skill_dir.name,
        skill_md_path=str(skill_md),
        raw_content=raw_content,
        frontmatter=frontmatter,
        raw_frontmatter=raw_frontmatter,
        frontmatter_start_line=frontmatter_start_line,
        body=body,
        body_start_line=body_start_line,
        files=_list_files(skill_dir),
        parse_errors=parse_errors,
        tokens=tokens,
    )


def _list_files(directory: Path) -> list[str]:
    if not directory.is_dir():
        return []
    return sorted(
        str(p.relative_to(directory))
        for p in directory.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )


def parse_command(command_path: str) -> ParsedCommand:
    """Parse a command directory or command.md file."""
    path = Path(command_path)
    parse_errors: list[str] = []

    if path.is_file() and path.name == "command.md":
        cmd_dir = path.parent
        cmd_md = path
    elif path.is_dir():
        cmd_md = path / "command.md"
        cmd_dir = path
        if not cmd_md.exists():
            return ParsedCommand(
                dir_path=str(path), dir_name=path.name, command_md_path=str(cmd_md),
                raw_content="", frontmatter={}, body="", body_start_line=0,
                script_references=[], files=_list_files(path),
                parse_errors=["command.md not found"],
            )
    else:
        return ParsedCommand(
            dir_path=str(path), dir_name=path.name, command_md_path=str(path),
            raw_content="", frontmatter={}, body="", body_start_line=0,
            script_references=[], files=[],
            parse_errors=[f"Path does not exist: {path}"],
        )

    raw_content = cmd_md.read_text()
    frontmatter: dict = {}
    body = raw_content
    body_start_line = 1

    lines = raw_content.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                try:
                    parsed = yaml.safe_load("\n".join(lines[1:i]))
                    if isinstance(parsed, dict):
                        frontmatter = parsed
                except yaml.YAMLError as e:
                    parse_errors.append(f"YAML parse error: {e}")
                body = "\n".join(lines[i + 1:])
                body_start_line = i + 2
                break

    script_refs = re.findall(r"[\w./-]+\.py\b", body)

    return ParsedCommand(
        dir_path=str(cmd_dir), dir_name=cmd_dir.name, command_md_path=str(cmd_md),
        raw_content=raw_content, frontmatter=frontmatter, body=body,
        body_start_line=body_start_line, script_references=script_refs,
        files=_list_files(cmd_dir), parse_errors=parse_errors,
        tokens=_count_tokens(raw_content),
    )


def parse_claude_md(file_path: str) -> ParsedClaudeMd:
    """Parse a CLAUDE.md file."""
    path = Path(file_path)
    if not path.exists():
        return ParsedClaudeMd(
            file_path=file_path, raw_content="", line_count=0,
            sections=[], parse_errors=[f"File not found: {file_path}"],
        )

    raw_content = path.read_text()
    lines = raw_content.split("\n")

    sections: list[dict[str, str]] = []
    current_header = "(top)"
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("#"):
            if current_lines:
                sections.append({"header": current_header, "content": "\n".join(current_lines)})
            current_header = line.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({"header": current_header, "content": "\n".join(current_lines)})

    return ParsedClaudeMd(
        file_path=file_path, raw_content=raw_content, line_count=len(lines),
        sections=sections, tokens=_count_tokens(raw_content),
    )


def parse_hooks(settings_path: str) -> ParsedHooks:
    """Parse hooks from a .claude/settings.json file."""
    import json as json_mod
    path = Path(settings_path)
    if not path.exists():
        return ParsedHooks(
            file_path=settings_path, hooks=[], raw_content="",
            parse_errors=[f"File not found: {settings_path}"],
        )

    raw_content = path.read_text()
    try:
        data = json_mod.loads(raw_content)
    except json_mod.JSONDecodeError as e:
        return ParsedHooks(
            file_path=settings_path, hooks=[], raw_content=raw_content,
            parse_errors=[f"JSON parse error: {e}"],
        )

    hooks = []
    hooks_data = data.get("hooks", {})
    if isinstance(hooks_data, dict):
        for event, hook_list in hooks_data.items():
            if isinstance(hook_list, list):
                for hook in hook_list:
                    hooks.append({"event": event, **(hook if isinstance(hook, dict) else {"command": str(hook)})})

    return ParsedHooks(
        file_path=settings_path, hooks=hooks, raw_content=raw_content,
    )


def parse_agent(agent_path: str) -> ParsedAgent:
    """Parse an agent .md file into a ParsedAgent."""
    path = Path(agent_path)
    parse_errors: list[str] = []

    if not path.exists() or not path.is_file():
        return ParsedAgent(
            dir_path=str(path.parent), file_name=path.name,
            agent_md_path=str(path), raw_content="",
            frontmatter={}, raw_frontmatter="", frontmatter_start_line=0,
            body="", body_start_line=0,
            referenced_skills=[], disallowed_tools=[], allowed_tools=[],
            model=None, sibling_files={}, files=[],
            parse_errors=[f"File not found: {path}"],
        )

    raw_content = path.read_text()

    frontmatter: dict = {}
    raw_frontmatter = ""
    frontmatter_start_line = 0
    body = raw_content
    body_start_line = 1

    lines = raw_content.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                frontmatter_start_line = 1
                raw_frontmatter = "\n".join(lines[1:i])
                body = "\n".join(lines[i + 1:])
                body_start_line = i + 2
                try:
                    parsed = yaml.safe_load(raw_frontmatter)
                    if isinstance(parsed, dict):
                        frontmatter = parsed
                    else:
                        parse_errors.append("Frontmatter is not a YAML mapping")
                except yaml.YAMLError as e:
                    parse_errors.append(f"YAML parse error: {e}")
                break
        else:
            parse_errors.append("Frontmatter opening '---' found but no closing '---'")

    referenced_skills = frontmatter.get("skills", []) or []
    if isinstance(referenced_skills, str):
        referenced_skills = [s.strip() for s in referenced_skills.split(",")]

    disallowed_raw = frontmatter.get("disallowedTools", "") or ""
    disallowed_tools = [t.strip() for t in disallowed_raw.split(",") if t.strip()]

    allowed_raw = frontmatter.get("tools", "") or ""
    allowed_tools = [t.strip() for t in allowed_raw.split(",") if t.strip()]

    model = frontmatter.get("model")

    agent_dir = path.parent
    scaffold_root = agent_dir.parent
    sibling_files: dict[str, list[str]] = {}
    for sibling_name in ("harness", "policies", "scripts", "schemas", "env"):
        sibling_dir = scaffold_root / sibling_name
        if sibling_dir.is_dir():
            sibling_files[sibling_name] = sorted(
                str(p.relative_to(scaffold_root))
                for p in sibling_dir.rglob("*") if p.is_file()
            )

    tokens = _count_tokens(raw_content)

    return ParsedAgent(
        dir_path=str(agent_dir), file_name=path.name,
        agent_md_path=str(path), raw_content=raw_content,
        frontmatter=frontmatter, raw_frontmatter=raw_frontmatter,
        frontmatter_start_line=frontmatter_start_line,
        body=body, body_start_line=body_start_line,
        referenced_skills=referenced_skills,
        disallowed_tools=disallowed_tools,
        allowed_tools=allowed_tools, model=model,
        sibling_files=sibling_files,
        files=_list_files(agent_dir),
        parse_errors=parse_errors, tokens=tokens,
    )


def lint_agent(
    agent_path: str,
    config_rules: dict[str, str | list] | None = None,
    all_skills: list[ParsedSkill] | None = None,
) -> LintResult:
    """Lint a single agent .md file."""
    agent = parse_agent(agent_path)
    diagnostics: list[Diagnostic] = []

    for parse_error in agent.parse_errors:
        diagnostics.append(Diagnostic(
            rule_id="parser", severity=Severity.ERROR, message=parse_error,
            location=DiagnosticLocation(file=agent.agent_md_path), category="structural",
        ))

    rule_diags, suppression_count = _run_rules(
        TargetType.AGENT, agent.agent_md_path, agent.raw_content,
        skill=None, target=agent, config_rules=config_rules,
        all_skills=all_skills,
    )
    diagnostics.extend(rule_diags)

    return LintResult(
        target_path=agent_path, target_name=agent.file_name.removesuffix(".md"),
        tokens=agent.tokens, target_type="agent", diagnostics=diagnostics,
        error_count=sum(1 for d in diagnostics if d.severity == Severity.ERROR),
        warning_count=sum(1 for d in diagnostics if d.severity == Severity.WARNING),
        info_count=sum(1 for d in diagnostics if d.severity == Severity.INFO),
        fixable_count=sum(1 for d in diagnostics if d.fix is not None),
        suppression_count=suppression_count,
    )


def _run_rules(
    target_type: TargetType,
    file_path: str,
    raw_content: str,
    skill: ParsedSkill | None,
    target: object | None,
    config_rules: dict[str, str | list] | None,
    all_skills: list[ParsedSkill] | None = None,
) -> tuple[list[Diagnostic], int]:
    """Run rules for a given target type. Returns (diagnostics, suppression_count)."""
    diagnostics: list[Diagnostic] = []
    suppression_count = 0
    suppressions = parse_suppressions(raw_content) if raw_content else {}
    config_rules = config_rules or {}

    dummy_skill = skill or ParsedSkill(
        dir_path="", dir_name="", skill_md_path=file_path, raw_content="",
        frontmatter={}, raw_frontmatter="", frontmatter_start_line=0,
        body="", body_start_line=0, files=[],
    )

    rules = get_all_rules()

    for rule in rules:
        if rule.meta.target_type != target_type:
            continue

        severity_config = config_rules.get(rule.meta.id)
        if severity_config == "off":
            continue

        if isinstance(severity_config, list) and len(severity_config) > 0:
            sev_str = severity_config[0]
            options = severity_config[1:]
        elif isinstance(severity_config, str):
            sev_str = severity_config
            options = []
        else:
            sev_str = rule.meta.default_severity.value
            options = []

        if sev_str == "off":
            continue

        try:
            severity = Severity(sev_str)
        except ValueError:
            severity = rule.meta.default_severity

        def make_report(rule_id, sev, meta_messages, category, fixable, fp):
            def report(descriptor: ReportDescriptor) -> None:
                nonlocal suppression_count
                loc = descriptor.location or DiagnosticLocation(file=fp)
                if is_suppressed(suppressions, rule_id, loc.start_line):
                    suppression_count += 1
                    return
                template = meta_messages.get(descriptor.message_id, descriptor.message_id)
                message = _interpolate(template, descriptor.data)
                effective_severity = descriptor.severity_override or sev
                diagnostics.append(Diagnostic(
                    rule_id=rule_id, severity=effective_severity, message=message,
                    location=loc, category=category, fix=descriptor.fix if fixable else None,
                ))
            return report

        context = RuleContext(
            skill=dummy_skill,
            report=make_report(
                rule.meta.id, severity, rule.meta.messages,
                rule.meta.category, rule.meta.fixable, file_path,
            ),
            severity=severity,
            options=options,
            target=target,
            all_skills=all_skills or [],
        )
        rule.create(context)

    return diagnostics, suppression_count


def lint(skill_path: str, config_rules: dict[str, str | list] | None = None) -> LintResult:
    """Lint a single skill directory or SKILL.md file."""
    skill = parse_skill(skill_path)
    diagnostics: list[Diagnostic] = []

    for parse_error in skill.parse_errors:
        diagnostics.append(Diagnostic(
            rule_id="parser", severity=Severity.ERROR, message=parse_error,
            location=DiagnosticLocation(file=skill.skill_md_path),
            category=skill.parse_errors[0] if skill.parse_errors else "structural",
        ))

    rule_diags, suppression_count = _run_rules(
        TargetType.SKILL, skill.skill_md_path, skill.raw_content,
        skill=skill, target=skill, config_rules=config_rules,
    )
    diagnostics.extend(rule_diags)

    return LintResult(
        target_path=skill_path, target_name=skill.dir_name, tokens=skill.tokens,
        target_type="skill", diagnostics=diagnostics,
        error_count=sum(1 for d in diagnostics if d.severity == Severity.ERROR),
        warning_count=sum(1 for d in diagnostics if d.severity == Severity.WARNING),
        info_count=sum(1 for d in diagnostics if d.severity == Severity.INFO),
        fixable_count=sum(1 for d in diagnostics if d.fix is not None),
        suppression_count=suppression_count,
    )


def lint_command(command_path: str, config_rules: dict[str, str | list] | None = None) -> LintResult:
    """Lint a single command directory."""
    cmd = parse_command(command_path)
    diagnostics: list[Diagnostic] = []

    for parse_error in cmd.parse_errors:
        diagnostics.append(Diagnostic(
            rule_id="parser", severity=Severity.ERROR, message=parse_error,
            location=DiagnosticLocation(file=cmd.command_md_path), category="structural",
        ))

    rule_diags, suppression_count = _run_rules(
        TargetType.COMMAND, cmd.command_md_path, cmd.raw_content,
        skill=None, target=cmd, config_rules=config_rules,
    )
    diagnostics.extend(rule_diags)

    return LintResult(
        target_path=command_path, target_name=cmd.dir_name, tokens=cmd.tokens,
        target_type="command", diagnostics=diagnostics,
        error_count=sum(1 for d in diagnostics if d.severity == Severity.ERROR),
        warning_count=sum(1 for d in diagnostics if d.severity == Severity.WARNING),
        info_count=sum(1 for d in diagnostics if d.severity == Severity.INFO),
        fixable_count=sum(1 for d in diagnostics if d.fix is not None),
        suppression_count=suppression_count,
    )


def lint_claude_md(
    file_path: str, config_rules: dict[str, str | list] | None = None,
    all_skills: list[ParsedSkill] | None = None,
) -> LintResult:
    """Lint a CLAUDE.md file."""
    claude_md = parse_claude_md(file_path)
    diagnostics: list[Diagnostic] = []

    for parse_error in claude_md.parse_errors:
        diagnostics.append(Diagnostic(
            rule_id="parser", severity=Severity.ERROR, message=parse_error,
            location=DiagnosticLocation(file=file_path), category="structural",
        ))

    rule_diags, suppression_count = _run_rules(
        TargetType.CLAUDE_MD, file_path, claude_md.raw_content,
        skill=None, target=claude_md, config_rules=config_rules,
        all_skills=all_skills,
    )
    diagnostics.extend(rule_diags)

    return LintResult(
        target_path=file_path, target_name=Path(file_path).name, tokens=claude_md.tokens,
        target_type="claude_md", diagnostics=diagnostics,
        error_count=sum(1 for d in diagnostics if d.severity == Severity.ERROR),
        warning_count=sum(1 for d in diagnostics if d.severity == Severity.WARNING),
        info_count=sum(1 for d in diagnostics if d.severity == Severity.INFO),
        fixable_count=sum(1 for d in diagnostics if d.fix is not None),
        suppression_count=suppression_count,
    )


def lint_hooks(
    settings_path: str, config_rules: dict[str, str | list] | None = None,
) -> LintResult:
    """Lint hooks from settings.json."""
    hooks = parse_hooks(settings_path)
    diagnostics: list[Diagnostic] = []

    for parse_error in hooks.parse_errors:
        diagnostics.append(Diagnostic(
            rule_id="parser", severity=Severity.ERROR, message=parse_error,
            location=DiagnosticLocation(file=settings_path), category="structural",
        ))

    rule_diags, suppression_count = _run_rules(
        TargetType.HOOKS, settings_path, hooks.raw_content,
        skill=None, target=hooks, config_rules=config_rules,
    )
    diagnostics.extend(rule_diags)

    return LintResult(
        target_path=settings_path, target_name="hooks", tokens=0,
        target_type="hooks", diagnostics=diagnostics,
        error_count=sum(1 for d in diagnostics if d.severity == Severity.ERROR),
        warning_count=sum(1 for d in diagnostics if d.severity == Severity.WARNING),
        info_count=sum(1 for d in diagnostics if d.severity == Severity.INFO),
        fixable_count=sum(1 for d in diagnostics if d.fix is not None),
        suppression_count=suppression_count,
    )


def lint_directory(
    scan_path: str, config_rules: dict[str, str | list] | None = None
) -> list[LintResult]:
    """Lint all skills found under a directory."""
    path = Path(scan_path)
    results = []

    if path.is_file() and path.name.lower() == "skill.md":
        results.append(lint(str(path.parent), config_rules))
        return results

    if not path.is_dir():
        return results

    excluded = {".git", ".venv", "node_modules", "repositories", "__pycache__", "tests"}
    skill_dirs: list[Path] = []
    for p in sorted(path.rglob("SKILL.md")):
        relative_parts = p.relative_to(path).parts
        if excluded.isdisjoint(relative_parts):
            skill_dirs.append(p.parent)

    if not skill_dirs and (path / "SKILL.md").exists():
        skill_dirs = [path]

    seen: set[str] = set()
    for skill_dir in skill_dirs:
        resolved = str(skill_dir.resolve())
        if resolved not in seen:
            seen.add(resolved)
            results.append(lint(str(skill_dir), config_rules))

    return results
