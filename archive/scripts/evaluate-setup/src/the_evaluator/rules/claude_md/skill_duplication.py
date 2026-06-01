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


class ClaudeMdSkillDuplication:
    meta = RuleMeta(
        id="claude-md/skill-duplication",
        default_severity=Severity.WARNING,
        fixable=False,
        description="CLAUDE.md should not duplicate content that's already in skills",
        category=RuleCategory.CONTENT,
        messages={
            "overlap": "CLAUDE.md section '{{section}}' has {{pct}}% similarity with skill '{{skill}}' — consider removing the duplicate content from CLAUDE.md since the skill loads on demand",
        },
        target_type=TargetType.CLAUDE_MD,
    )

    def create(self, context: RuleContext) -> None:
        cmd = context.claude_md
        if cmd is None or not context.all_skills:
            return

        for section in cmd.sections:
            section_text = section.get("content", "")
            if len(section_text.split()) < 20:
                continue

            for skill in context.all_skills:
                if not skill.body or len(skill.body.split()) < 20:
                    continue

                similarity = tfidf_similarity(section_text, skill.body)
                if similarity >= OVERLAP_THRESHOLD:
                    context.report(
                        ReportDescriptor(
                            message_id="overlap",
                            data={
                                "section": section.get("header", "(untitled)"),
                                "pct": str(int(similarity * 100)),
                                "skill": skill.dir_name,
                            },
                            location=DiagnosticLocation(file=cmd.file_path, start_line=1),
                        )
                    )
