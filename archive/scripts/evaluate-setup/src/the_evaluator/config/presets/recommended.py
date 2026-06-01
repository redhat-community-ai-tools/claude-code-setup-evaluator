RECOMMENDED: dict[str, str] = {
    "structural/skill-md-exists": "error",
    "frontmatter/description-required": "error",
    "frontmatter/description-quality": "warning",
    "frontmatter/format-valid": "warning",
    "content/token-budget": "warning",
    "content/broken-references": "error",
    "content/duplicate-detection": "warning",
    "security/no-prompt-injection": "error",
    "security/no-credential-access": "error",
    # Command rules
    "command/no-prompt-injection": "error",
    "command/no-credential-access": "error",
    # CLAUDE.md rules
    "claude-md/exists": "warning",
    # Agent rules
    "agent/description-required": "error",
    "agent/referenced-skills-exist": "error",
    "agent/disallowed-tools-parseable": "warning",
    "agent/constraint-body-match": "warning",
    "agent/no-prompt-injection": "error",
    "agent/no-credential-access": "error",
}
