from the_evaluator.engine.registry import register_rule


def register_all_rules() -> None:
    """Import and register all built-in rules."""
    # Skill rules
    from the_evaluator.rules.agents.constraint_body_match import ConstraintBodyMatch

    # Agent rules
    from the_evaluator.rules.agents.description_required import AgentDescriptionRequired
    from the_evaluator.rules.agents.disallowed_tools_parseable import DisallowedToolsParseable
    from the_evaluator.rules.agents.no_credential_access import AgentNoCredentialAccess
    from the_evaluator.rules.agents.no_prompt_injection import AgentNoPromptInjection
    from the_evaluator.rules.agents.referenced_skills_exist import ReferencedSkillsExist

    # CLAUDE.md rules
    from the_evaluator.rules.claude_md.exists import ClaudeMdExists
    from the_evaluator.rules.claude_md.skill_duplication import ClaudeMdSkillDuplication

    # Command rules
    from the_evaluator.rules.commands.description_required import CommandDescriptionRequired
    from the_evaluator.rules.commands.duplicate_detection import CommandDuplicateDetection
    from the_evaluator.rules.commands.no_credential_access import CommandNoCredentialAccess
    from the_evaluator.rules.commands.no_prompt_injection import CommandNoPromptInjection
    from the_evaluator.rules.commands.script_exists import CommandScriptExists
    from the_evaluator.rules.commands.skill_overlap import CommandSkillOverlap
    from the_evaluator.rules.content.broken_references import BrokenReferences
    from the_evaluator.rules.content.duplicate_detection import DuplicateDetection
    from the_evaluator.rules.content.token_budget import TokenBudget
    from the_evaluator.rules.frontmatter.description_quality import DescriptionQuality
    from the_evaluator.rules.frontmatter.description_required import DescriptionRequired
    from the_evaluator.rules.frontmatter.format_valid import FormatValid

    # Hooks rules
    from the_evaluator.rules.hooks.valid_structure import HooksValidStructure
    from the_evaluator.rules.security.no_credential_access import NoCredentialAccess
    from the_evaluator.rules.security.no_prompt_injection import NoPromptInjection
    from the_evaluator.rules.structural.skill_md_exists import SkillMdExists

    for rule_cls in [
        SkillMdExists,
        DescriptionRequired,
        DescriptionQuality,
        FormatValid,
        TokenBudget,
        BrokenReferences,
        DuplicateDetection,
        NoPromptInjection,
        NoCredentialAccess,
        CommandDescriptionRequired,
        CommandScriptExists,
        CommandNoPromptInjection,
        CommandNoCredentialAccess,
        CommandSkillOverlap,
        CommandDuplicateDetection,
        ClaudeMdExists,
        ClaudeMdSkillDuplication,
        HooksValidStructure,
        AgentDescriptionRequired,
        ReferencedSkillsExist,
        DisallowedToolsParseable,
        ConstraintBodyMatch,
        AgentNoPromptInjection,
        AgentNoCredentialAccess,
    ]:
        register_rule(rule_cls())
