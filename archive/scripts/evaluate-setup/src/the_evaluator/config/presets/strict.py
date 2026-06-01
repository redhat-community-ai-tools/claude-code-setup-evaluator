from the_evaluator.config.presets.recommended import RECOMMENDED

STRICT: dict[str, str] = {
    **RECOMMENDED,
    "frontmatter/description-quality": "error",
    "frontmatter/format-valid": "error",
    "content/token-budget": "error",
    "claude-md/exists": "error",
    "agent/disallowed-tools-parseable": "error",
    "agent/constraint-body-match": "error",
}
