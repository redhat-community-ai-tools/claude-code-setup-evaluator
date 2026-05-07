from __future__ import annotations

import re


from the_evaluator.engine.types import (
    DiagnosticLocation,
    ReportDescriptor,
    RuleCategory,
    RuleContext,
    RuleMeta,
    Severity,
)

_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("ignore previous instructions", re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I)),
    ("disregard prior", re.compile(r"disregard\s+(all\s+)?(prior|previous|above)", re.I)),
    ("you are now", re.compile(r"you\s+are\s+now\s+(?:a|an|the)\s+", re.I)),
    ("system prompt override", re.compile(r"system\s*prompt\s*(override|injection|change)", re.I)),
    ("override instructions", re.compile(r"override\s+(all\s+)?(instructions|rules|guidelines)", re.I)),
    ("new instructions", re.compile(r"new\s+instructions?\s*:", re.I)),
    ("jailbreak attempt", re.compile(r"(DAN|do\s+anything\s+now|developer\s+mode)", re.I)),
    ("prompt leak", re.compile(r"(reveal|show|print|output)\s+(your|the)\s+(system\s+)?prompt", re.I)),
    ("role hijack", re.compile(r"forget\s+(everything|all|your)\s+(you|instructions|rules)", re.I)),
    ("hidden instruction", re.compile(r"<\s*(?:system|instruction|hidden)\s*>", re.I)),
    ("role play", re.compile(r"(?:act|pretend)\s+(?:as|to\s+be)\s+(?:a|an|the)\s+", re.I)),
    ("encoding evasion", re.compile(r"(?:in\s+base64|encode\s+(?:as|in|to)\s+base64|base64\s+encod)", re.I)),
    ("repeat after me", re.compile(r"repeat\s+after\s+me", re.I)),
    ("bypass safety", re.compile(r"(?:ignore\s+safety|bypass\s+(?:filter|safety|restriction))", re.I)),
    ("output control", re.compile(r"output\s+the\s+following\s+exactly", re.I)),
    ("markdown image exfiltration", re.compile(r"!\[.*?\]\(https?://", re.I)),
    ("translate evasion", re.compile(r"translate\s+(?:this|the\s+following)\s+(?:to|into)\s+", re.I)),
]



class NoPromptInjection:
    meta: RuleMeta = RuleMeta(
        id="security/no-prompt-injection",
        default_severity=Severity.ERROR,
        fixable=False,
        description="Skill content should not contain prompt injection patterns",
        category=RuleCategory.SECURITY,
        messages={
            "injection_detected": "Potential prompt injection pattern: '{{label}}' at line {{line}}",
            "injection_in_code_block": "Prompt injection pattern '{{label}}' at line {{line}} (inside code block — likely documentation)",
            "injection_in_example": "Prompt injection pattern '{{label}}' at line {{line}} (in example/quote context)",
        },
    )

    def create(self, context: RuleContext) -> None:
        skill = context.skill
        if not skill.raw_content:
            return

        lines = skill.raw_content.split("\n")
        in_code_fence = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code_fence = not in_code_fence
                continue

            for label, pattern in _INJECTION_PATTERNS:
                if pattern.search(line):
                    is_quoted = stripped.startswith(">") or stripped.startswith('"')
                    is_example = any(
                        w in line.lower()
                        for w in ["for example", "e.g.", "such as", "like:"]
                    )

                    if in_code_fence:
                        message_id = "injection_in_code_block"
                        severity_override = Severity.WARNING
                    elif is_quoted or is_example:
                        message_id = "injection_in_example"
                        severity_override = Severity.WARNING
                    else:
                        message_id = "injection_detected"
                        severity_override = None

                    context.report(
                        ReportDescriptor(
                            message_id=message_id,
                            data={"label": label, "line": str(i + 1)},
                            location=DiagnosticLocation(
                                file=skill.skill_md_path,
                                start_line=i + 1,
                            ),
                            severity_override=severity_override,
                        )
                    )
                    break
