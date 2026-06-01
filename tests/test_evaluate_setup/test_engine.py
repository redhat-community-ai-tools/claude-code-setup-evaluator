"""Tests for the-evaluator rule engine."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts" / "evaluate-setup" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from the_evaluator.config.loader import load_config
from the_evaluator.config.presets import PRESETS
from the_evaluator.engine.engine import lint, lint_claude_md, lint_command, lint_directory, parse_command, parse_skill
from the_evaluator.engine.registry import clear_rules, get_all_rules, get_rules_by_category, register_rule
from the_evaluator.engine.suppression import is_suppressed, parse_suppressions
from the_evaluator.engine.types import RuleCategory, RuleMeta, Severity

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseSkill:
    def test_parse_good_skill(self):
        result = parse_skill(str(FIXTURES / "good-skill"))
        assert result.dir_name == "good-skill"
        assert result.frontmatter.get("name") == "good-skill"
        assert "Use when" in result.frontmatter.get("description", "")
        assert result.parse_errors == []
        assert result.tokens > 0

    def test_parse_bad_skill(self):
        result = parse_skill(str(FIXTURES / "bad-skill"))
        assert result.dir_name == "bad-skill"
        assert result.frontmatter.get("description") is None
        assert result.parse_errors == []

    def test_parse_missing_skill(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = parse_skill(str(empty_dir))
        assert len(result.parse_errors) > 0
        assert "not found" in result.parse_errors[0].lower()


class TestSuppression:
    def test_file_wide_suppression(self):
        content = "<!-- evaluator-ignore: content/token-budget -->\n# Big Skill\nLots of content..."
        suppressions = parse_suppressions(content)
        assert is_suppressed(suppressions, "content/token-budget", None)
        assert not is_suppressed(suppressions, "other/rule", None)

    def test_next_line_suppression(self):
        content = "line 1\n<!-- evaluator-ignore-next-line: frontmatter/description-quality -->\ndescription: broad"
        suppressions = parse_suppressions(content)
        assert is_suppressed(suppressions, "frontmatter/description-quality", 3)
        assert not is_suppressed(suppressions, "frontmatter/description-quality", 1)

    def test_multi_rule_suppression(self):
        content = "<!-- evaluator-ignore: rule-a, rule-b -->\ncontent"
        suppressions = parse_suppressions(content)
        assert is_suppressed(suppressions, "rule-a", None)
        assert is_suppressed(suppressions, "rule-b", None)


class TestRegistry:
    def setup_method(self):
        clear_rules()

    def test_register_and_retrieve(self):
        class FakeRule:
            meta = RuleMeta(
                id="test/fake",
                default_severity=Severity.WARNING,
                fixable=False,
                description="A test rule",
                category=RuleCategory.CONTENT,
                messages={"msg": "Test message"},
            )

            def create(self, context):
                pass

        register_rule(FakeRule())
        assert len(get_all_rules()) == 1
        assert get_all_rules()[0].meta.id == "test/fake"

    def test_duplicate_registration_raises(self):
        class FakeRule:
            meta = RuleMeta(
                id="test/dupe",
                default_severity=Severity.WARNING,
                fixable=False,
                description="A test rule",
                category=RuleCategory.CONTENT,
                messages={},
            )

            def create(self, context):
                pass

        register_rule(FakeRule())
        with pytest.raises(ValueError, match="already registered"):
            register_rule(FakeRule())

    def test_get_by_category(self):
        class ContentRule:
            meta = RuleMeta(
                id="test/content",
                default_severity=Severity.WARNING,
                fixable=False,
                description="Content rule",
                category=RuleCategory.CONTENT,
                messages={},
            )

            def create(self, context):
                pass

        class SecurityRule:
            meta = RuleMeta(
                id="test/security",
                default_severity=Severity.ERROR,
                fixable=False,
                description="Security rule",
                category=RuleCategory.SECURITY,
                messages={},
            )

            def create(self, context):
                pass

        register_rule(ContentRule())
        register_rule(SecurityRule())
        content_rules = get_rules_by_category(RuleCategory.CONTENT)
        assert len(content_rules) == 1
        assert content_rules[0].meta.id == "test/content"


class TestConfigPresets:
    def test_recommended_preset_exists(self):
        assert "recommended" in PRESETS
        assert "structural/skill-md-exists" in PRESETS["recommended"]

    def test_strict_inherits_recommended(self):
        for rule_id in PRESETS["recommended"]:
            assert rule_id in PRESETS["strict"]

    def test_security_disables_non_security(self):
        security_rule_ids = {
            "security/no-prompt-injection",
            "security/no-credential-access",
            "agent/no-prompt-injection",
            "agent/no-credential-access",
            "command/no-prompt-injection",
            "command/no-credential-access",
        }
        for rule_id, severity in PRESETS["security"].items():
            if rule_id not in security_rule_ids:
                assert severity == "off", f"{rule_id} should be 'off' in security preset"

    def test_load_config_default(self):
        config = load_config()
        assert config.preset_name == "recommended"
        assert "structural/skill-md-exists" in config.rules

    def test_load_config_preset_override(self):
        config = load_config(preset_override="security")
        assert config.preset_name == "security"
        assert config.rules.get("frontmatter/description-required") == "off"


class TestDuplicateDetection:
    def setup_method(self):
        from the_evaluator.rules.content.duplicate_detection import reset_duplicate_state

        reset_duplicate_state()
        clear_rules()
        from the_evaluator.rules import register_all_rules

        register_all_rules()

    def test_identical_skills_detected(self, tmp_path):
        body = "## Rules\n\nAlways use raise from for exception chaining.\nNever catch bare exceptions.\n"
        for name in ("skill-a", "skill-b"):
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Use when writing Python\n---\n{body}")
        results = lint_directory(str(tmp_path))
        dupe_diags = [d for r in results for d in r.diagnostics if d.rule_id == "content/duplicate-detection"]
        assert len(dupe_diags) == 1
        assert "similar" in dupe_diags[0].message

    def test_different_skills_not_flagged(self, tmp_path):
        (tmp_path / "security").mkdir()
        (tmp_path / "security" / "SKILL.md").write_text(
            "---\nname: security\ndescription: Use when checking security\n---\n"
            "## Secret Scanning\nGrep for API keys: AIzaSy, sk-ant, ghp_.\nCheck .gitignore coverage.\n"
        )
        (tmp_path / "pipeline").mkdir()
        (tmp_path / "pipeline" / "SKILL.md").write_text(
            "---\nname: pipeline\ndescription: Use when building pipelines\n---\n"
            "## Stage Structure\ndef main(argv=None): parse args, load input, process, save output with metadata.\n"
        )
        results = lint_directory(str(tmp_path))
        dupe_diags = [d for r in results for d in r.diagnostics if d.rule_id == "content/duplicate-detection"]
        assert len(dupe_diags) == 0

    def test_common_boilerplate_not_inflated(self, tmp_path):
        """TF-IDF should downweight common words so skills sharing only boilerplate don't match."""
        boilerplate = "import os\nimport sys\nfrom pathlib import Path\ndef main():\n    return\n"
        (tmp_path / "skill-x").mkdir()
        (tmp_path / "skill-x" / "SKILL.md").write_text(
            "---\nname: skill-x\ndescription: Use when doing X\n---\n"
            f"{boilerplate}\n## Credential Management\nLoad secrets from dotenv. Validate required vars.\n"
        )
        (tmp_path / "skill-y").mkdir()
        (tmp_path / "skill-y" / "SKILL.md").write_text(
            "---\nname: skill-y\ndescription: Use when doing Y\n---\n"
            f"{boilerplate}\n## Data Pipeline\nEvery stage outputs metadata with generated_at timestamp.\n"
        )
        results = lint_directory(str(tmp_path))
        dupe_diags = [d for r in results for d in r.diagnostics if d.rule_id == "content/duplicate-detection"]
        assert len(dupe_diags) == 0

    def test_high_similarity_above_threshold(self, tmp_path):
        """Two skills with 90%+ shared distinctive content should be flagged."""
        shared = (
            "## Team API Conventions\n\n"
            "Always set timeout to 30 seconds on requests.\n"
            "Retry transient failures: 429, 500, 502, 503, 504.\n"
            "Never retry permanent failures: 400, 401, 403, 404.\n"
            "Log method, URL, status code, duration.\n"
            "Validate response structure before accessing fields.\n"
        )
        (tmp_path / "api-v1").mkdir()
        (tmp_path / "api-v1" / "SKILL.md").write_text(
            f"---\nname: api-v1\ndescription: Use when calling APIs\n---\n{shared}"
        )
        (tmp_path / "api-v2").mkdir()
        (tmp_path / "api-v2" / "SKILL.md").write_text(
            f"---\nname: api-v2\ndescription: Use when calling APIs v2\n---\n{shared}\nAlso check rate limits.\n"
        )
        results = lint_directory(str(tmp_path))
        dupe_diags = [d for r in results for d in r.diagnostics if d.rule_id == "content/duplicate-detection"]
        assert len(dupe_diags) == 1


class TestDescriptionQuality:
    def setup_method(self):
        clear_rules()
        from the_evaluator.rules import register_all_rules

        register_all_rules()

    def test_good_description_passes(self):
        result = lint(str(FIXTURES / "good-skill"))
        diags = [d for d in result.diagnostics if d.rule_id == "frontmatter/description-quality"]
        assert len(diags) == 0

    def test_first_person_flagged(self, tmp_path):
        d = tmp_path / "fp-skill"
        d.mkdir()
        (d / "SKILL.md").write_text(
            '---\nname: fp-skill\ndescription: "I will help you write Python code"\n---\nBody content.\n'
        )
        result = lint(str(d))
        diags = [d for d in result.diagnostics if d.rule_id == "frontmatter/description-quality"]
        messages = " ".join(d.message for d in diags)
        assert "first-person" in messages.lower() or "first_person" in messages.lower() or "I will" in messages

    def test_no_use_case_flagged(self, tmp_path):
        d = tmp_path / "no-context"
        d.mkdir()
        (d / "SKILL.md").write_text(
            '---\nname: no-context\ndescription: "Python conventions and patterns"\n---\nBody content.\n'
        )
        result = lint(str(d))
        diags = [d for d in result.diagnostics if d.rule_id == "frontmatter/description-quality"]
        messages = " ".join(d.message for d in diags)
        assert "use-case" in messages.lower() or "use_case" in messages.lower() or "context" in messages.lower()

    def test_too_short_flagged(self, tmp_path):
        d = tmp_path / "short-desc"
        d.mkdir()
        (d / "SKILL.md").write_text('---\nname: short-desc\ndescription: "Code help"\n---\nBody.\n')
        result = lint(str(d))
        diags = [d for d in result.diagnostics if d.rule_id == "frontmatter/description-quality"]
        messages = " ".join(d.message for d in diags)
        assert "too vague" in messages.lower() or "too_short" in messages.lower() or "characters" in messages

    def test_too_long_flagged(self, tmp_path):
        d = tmp_path / "long-desc"
        d.mkdir()
        long_desc = "A" * 1030
        (d / "SKILL.md").write_text(f'---\nname: long-desc\ndescription: "{long_desc}"\n---\nBody.\n')
        result = lint(str(d))
        diags = [d for d in result.diagnostics if d.rule_id == "frontmatter/description-quality"]
        messages = " ".join(d.message for d in diags)
        assert "1,024" in messages or "1024" in messages.replace(",", "")


class TestCommandSecurity:
    def setup_method(self):
        clear_rules()
        from the_evaluator.rules import register_all_rules

        register_all_rules()

    def test_good_command_passes(self):
        result = lint_command(str(FIXTURES / "commands" / "good-command"))
        security_diags = [d for d in result.diagnostics if d.rule_id.startswith("command/no-")]
        assert len(security_diags) == 0

    def test_bad_command_injection_detected(self):
        result = lint_command(str(FIXTURES / "commands" / "bad-command"))
        injection_diags = [d for d in result.diagnostics if d.rule_id == "command/no-prompt-injection"]
        assert len(injection_diags) >= 1

    def test_bad_command_credential_detected(self):
        result = lint_command(str(FIXTURES / "commands" / "bad-command"))
        cred_diags = [d for d in result.diagnostics if d.rule_id == "command/no-credential-access"]
        assert len(cred_diags) >= 1

    def test_bad_command_dangerous_command_detected(self):
        result = lint_command(str(FIXTURES / "commands" / "bad-command"))
        all_diags = [d for d in result.diagnostics if d.rule_id == "command/no-credential-access"]
        messages = " ".join(d.message for d in all_diags)
        assert "sudo" in messages.lower() or "chmod 777" in messages.lower()


class TestClaudeMdExists:
    def setup_method(self):
        clear_rules()
        from the_evaluator.rules import register_all_rules

        register_all_rules()

    def test_missing_claude_md_flagged(self, tmp_path):
        result = lint_claude_md(str(tmp_path / "CLAUDE.md"))
        diags = [d for d in result.diagnostics if d.rule_id == "claude-md/exists"]
        assert len(diags) == 1

    def test_existing_claude_md_passes(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# Project\n\nUse uv for all Python execution.\n")
        result = lint_claude_md(str(tmp_path / "CLAUDE.md"))
        diags = [d for d in result.diagnostics if d.rule_id == "claude-md/exists"]
        assert len(diags) == 0


class TestLint:
    def setup_method(self):
        clear_rules()
        from the_evaluator.rules import register_all_rules

        register_all_rules()

    def test_lint_good_skill(self):
        result = lint(str(FIXTURES / "good-skill"))
        quality_warnings = [d for d in result.diagnostics if d.rule_id == "frontmatter/description-quality"]
        assert len(quality_warnings) == 0

    def test_lint_bad_skill_finds_issues(self):
        result = lint(str(FIXTURES / "bad-skill"))
        assert result.error_count > 0
        rule_ids = {d.rule_id for d in result.diagnostics}
        assert "frontmatter/description-required" in rule_ids

    def test_lint_security_skill_finds_injection(self):
        result = lint(str(FIXTURES / "security-skill"))
        security_diags = [d for d in result.diagnostics if "security" in d.rule_id]
        assert len(security_diags) > 0

    def test_lint_with_security_preset(self):
        config = load_config(preset_override="security")
        result = lint(str(FIXTURES / "good-skill"), config.rules)
        non_security = [d for d in result.diagnostics if "security" not in d.rule_id and d.rule_id != "parser"]
        assert len(non_security) == 0

    def test_lint_directory(self):
        results = lint_directory(str(FIXTURES))
        assert len(results) == 3
        names = {r.target_name for r in results}
        assert "good-skill" in names
        assert "bad-skill" in names
        assert "security-skill" in names


class TestCommandSkillOverlap:
    def setup_method(self):
        clear_rules()
        from the_evaluator.rules import register_all_rules

        register_all_rules()

    def test_overlapping_command_and_skill_detected(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        shared_content = "Always use timeout=30 on requests. " * 30
        (skill_dir / "SKILL.md").write_text(
            f'---\nname: my-skill\ndescription: "API patterns"\n---\n{shared_content}\n'
        )
        parsed_skills = [parse_skill(str(skill_dir))]

        cmd_dir = tmp_path / "my-command"
        cmd_dir.mkdir()
        (cmd_dir / "command.md").write_text(f'---\ndescription: "API review"\n---\n{shared_content}\n')

        result = lint_command(str(cmd_dir), all_skills=parsed_skills)
        overlap_diags = [d for d in result.diagnostics if d.rule_id == "command/skill-overlap"]
        assert len(overlap_diags) == 1
        assert "my-skill" in overlap_diags[0].message

    def test_different_command_and_skill_no_false_positive(self, tmp_path):
        skill_dir = tmp_path / "python-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            '---\nname: python-skill\ndescription: "Python conventions"\n---\n'
            "Use dotenv for credential management. Always validate environment variables at startup. "
            "Set timeout=30 on all HTTP requests. Retry only transient failures.\n"
        )
        parsed_skills = [parse_skill(str(skill_dir))]

        cmd_dir = tmp_path / "deploy-cmd"
        cmd_dir.mkdir()
        (cmd_dir / "command.md").write_text(
            '---\ndescription: "Deploy to staging"\n---\n'
            "Run the deployment pipeline. Check container health. Verify DNS propagation. "
            "Monitor error rates for 15 minutes after deploy.\n"
        )

        result = lint_command(str(cmd_dir), all_skills=parsed_skills)
        overlap_diags = [d for d in result.diagnostics if d.rule_id == "command/skill-overlap"]
        assert len(overlap_diags) == 0


class TestCommandDuplicateDetection:
    def setup_method(self):
        clear_rules()
        from the_evaluator.rules import register_all_rules

        register_all_rules()
        from the_evaluator.rules.commands.duplicate_detection import reset_command_duplicate_state

        reset_command_duplicate_state()

    def test_duplicate_commands_detected(self, tmp_path):
        shared_body = "Review code for security vulnerabilities and credential leaks. " * 20

        cmd1 = tmp_path / "review-security"
        cmd1.mkdir()
        (cmd1 / "command.md").write_text(f'---\ndescription: "Security review"\n---\n{shared_body}\n')

        cmd2 = tmp_path / "sec-check"
        cmd2.mkdir()
        (cmd2 / "command.md").write_text(f'---\ndescription: "Security check"\n---\n{shared_body}\n')

        parsed_commands = [parse_command(str(cmd1)), parse_command(str(cmd2))]

        lint_command(str(cmd1), all_commands=parsed_commands)
        result2 = lint_command(str(cmd2), all_commands=parsed_commands)
        dup_diags = [d for d in result2.diagnostics if d.rule_id == "command/duplicate-detection"]
        assert len(dup_diags) == 1
        assert "review-security" in dup_diags[0].message

    def test_different_commands_no_false_positive(self, tmp_path):
        cmd1 = tmp_path / "deploy"
        cmd1.mkdir()
        (cmd1 / "command.md").write_text(
            '---\ndescription: "Deploy"\n---\nRun deployment pipeline with health checks and DNS verification.\n'
        )

        cmd2 = tmp_path / "review"
        cmd2.mkdir()
        (cmd2 / "command.md").write_text(
            '---\ndescription: "Review"\n---\nReview code quality with linting, type checking, and test coverage.\n'
        )

        parsed_commands = [parse_command(str(cmd1)), parse_command(str(cmd2))]

        lint_command(str(cmd1), all_commands=parsed_commands)
        result2 = lint_command(str(cmd2), all_commands=parsed_commands)
        dup_diags = [d for d in result2.diagnostics if d.rule_id == "command/duplicate-detection"]
        assert len(dup_diags) == 0
