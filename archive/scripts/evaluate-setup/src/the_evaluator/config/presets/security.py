SECURITY: dict[str, str] = {
    "structural/skill-md-exists": "off",
    "frontmatter/description-required": "off",
    "frontmatter/description-quality": "off",
    "frontmatter/format-valid": "off",
    "content/token-budget": "off",
    "content/broken-references": "off",
    "content/duplicate-detection": "off",
    "security/no-prompt-injection": "error",
    "security/no-credential-access": "error",
    # Command security rules
    "command/no-prompt-injection": "error",
    "command/no-credential-access": "error",
    # CLAUDE.md rules
    "claude-md/exists": "off",
    # Agent rules
    "agent/description-required": "off",
    "agent/referenced-skills-exist": "off",
    "agent/disallowed-tools-parseable": "off",
    "agent/constraint-body-match": "off",
    "agent/no-prompt-injection": "error",
    "agent/no-credential-access": "error",
}
