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
from the_evaluator.utils.similarity import tfidf_similarity

OVERLAP_THRESHOLD = 0.60


class CommandSkillOverlap:
    meta = RuleMeta(
        id="command/skill-overlap",
        default_severity=Severity.WARNING,
        fixable=False,
        description="Detect commands that duplicate content already in a skill",
        category=RuleCategory.CONTENT,
        messages={
            "overlap": "Command '{{command}}' has {{pct}}% similarity with skill '{{skill}}' — consider whether both are needed",
        },
        target_type=TargetType.COMMAND,
    )

    def create(self, context: RuleContext) -> None:
        cmd = context.command
        if cmd is None or not cmd.body or not context.all_skills:
            return

        if len(cmd.body.split()) < 20:
            return

        for skill in context.all_skills:
            if not skill.body or len(skill.body.split()) < 20:
                continue

            similarity = tfidf_similarity(cmd.body, skill.body)
            if similarity >= OVERLAP_THRESHOLD:
                context.report(ReportDescriptor(
                    message_id="overlap",
                    data={
                        "command": cmd.dir_name,
                        "pct": str(int(similarity * 100)),
                        "skill": skill.dir_name,
                    },
                    location=DiagnosticLocation(file=cmd.command_md_path, start_line=1),
                ))
