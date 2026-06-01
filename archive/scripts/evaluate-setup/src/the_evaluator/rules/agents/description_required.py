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


class AgentDescriptionRequired:
    meta: RuleMeta = RuleMeta(
        id="agent/description-required",
        default_severity=Severity.ERROR,
        fixable=False,
        description="Agent must have a description in frontmatter",
        category=RuleCategory.FRONTMATTER,
        messages={
            "missing": "Required field 'description' is missing from agent frontmatter",
            "empty": "Field 'description' must not be empty",
        },
        target_type=TargetType.AGENT,
    )

    def create(self, context: RuleContext) -> None:
        agent = context.agent
        if not agent or agent.parse_errors:
            return

        description = agent.frontmatter.get("description")
        loc = DiagnosticLocation(
            file=agent.agent_md_path,
            start_line=agent.frontmatter_start_line or 1,
        )

        if description is None:
            context.report(ReportDescriptor(message_id="missing", location=loc))
        elif isinstance(description, str) and description.strip() == "":
            context.report(ReportDescriptor(message_id="empty", location=loc))
