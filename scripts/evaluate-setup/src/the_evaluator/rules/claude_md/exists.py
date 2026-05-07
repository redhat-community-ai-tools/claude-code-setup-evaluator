from __future__ import annotations

from the_evaluator.engine.types import (
    DiagnosticLocation,
    ReportDescriptor,
    RuleCategory,
    RuleContext,
    RuleMeta,
    Severity,
    TargetType,
)


class ClaudeMdExists:
    meta = RuleMeta(
        id="claude-md/exists",
        default_severity=Severity.WARNING,
        fixable=False,
        description="Project should have a CLAUDE.md with project-specific instructions",
        category=RuleCategory.STRUCTURAL,
        messages={
            "not_found": "No CLAUDE.md found — consider creating one with project-specific instructions (build commands, test runners, code style). See https://code.claude.com/docs/en/best-practices",
        },
        target_type=TargetType.CLAUDE_MD,
    )

    def create(self, context: RuleContext) -> None:
        cmd = context.claude_md
        if cmd is None:
            return

        if any("not found" in e.lower() or "file not found" in e.lower() for e in cmd.parse_errors):
            context.report(ReportDescriptor(
                message_id="not_found",
                location=DiagnosticLocation(file=cmd.file_path, start_line=1),
            ))
