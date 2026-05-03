from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Protocol


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class TargetType(str, Enum):
    SKILL = "skill"
    COMMAND = "command"
    CLAUDE_MD = "claude_md"
    HOOKS = "hooks"


class RuleCategory(str, Enum):
    STRUCTURAL = "structural"
    FRONTMATTER = "frontmatter"
    CONTENT = "content"
    SECURITY = "security"
    BEST_PRACTICES = "best_practices"


@dataclass(frozen=True)
class DiagnosticLocation:
    file: str
    start_line: Optional[int] = None


@dataclass(frozen=True)
class DiagnosticFix:
    description: str
    replacement: Optional[str] = None


@dataclass(frozen=True)
class Diagnostic:
    rule_id: str
    severity: Severity
    message: str
    location: DiagnosticLocation
    category: RuleCategory
    fix: Optional[DiagnosticFix] = None


@dataclass
class RuleMeta:
    id: str
    default_severity: Severity
    fixable: bool
    description: str
    category: RuleCategory
    messages: dict[str, str]
    target_type: TargetType = TargetType.SKILL


@dataclass
class ReportDescriptor:
    message_id: str
    data: Optional[dict[str, str | int]] = None
    location: Optional[DiagnosticLocation] = None
    fix: Optional[DiagnosticFix] = None
    severity_override: Optional[Severity] = None


@dataclass
class ParsedSkill:
    dir_path: str
    dir_name: str
    skill_md_path: str
    raw_content: str
    frontmatter: dict[str, Any]
    raw_frontmatter: str
    frontmatter_start_line: int
    body: str
    body_start_line: int
    files: list[str]
    parse_errors: list[str] = field(default_factory=list)
    tokens: int = 0


@dataclass
class ParsedCommand:
    dir_path: str
    dir_name: str
    command_md_path: str
    raw_content: str
    frontmatter: dict[str, Any]
    body: str
    body_start_line: int
    script_references: list[str]
    files: list[str]
    parse_errors: list[str] = field(default_factory=list)
    tokens: int = 0


@dataclass
class ParsedClaudeMd:
    file_path: str
    raw_content: str
    line_count: int
    sections: list[dict[str, str]]
    parse_errors: list[str] = field(default_factory=list)
    tokens: int = 0


@dataclass
class ParsedHooks:
    file_path: str
    hooks: list[dict[str, Any]]
    raw_content: str
    parse_errors: list[str] = field(default_factory=list)


ParsedFile = ParsedSkill | ParsedCommand | ParsedClaudeMd | ParsedHooks


@dataclass
class RuleContext:
    skill: ParsedSkill
    report: Callable[[ReportDescriptor], None]
    severity: Severity
    options: list[Any] = field(default_factory=list)
    target: Optional[ParsedFile] = None
    all_skills: list[ParsedSkill] = field(default_factory=list)

    @property
    def command(self) -> ParsedCommand | None:
        return self.target if isinstance(self.target, ParsedCommand) else None

    @property
    def claude_md(self) -> ParsedClaudeMd | None:
        return self.target if isinstance(self.target, ParsedClaudeMd) else None

    @property
    def hooks(self) -> ParsedHooks | None:
        return self.target if isinstance(self.target, ParsedHooks) else None


@dataclass
class LintResult:
    skill_path: str
    skill_name: str
    tokens: int
    target_type: str = "skill"
    diagnostics: list[Diagnostic] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    fixable_count: int = 0
    suppression_count: int = 0


class Rule(Protocol):
    meta: RuleMeta

    def create(self, context: RuleContext) -> None: ...
