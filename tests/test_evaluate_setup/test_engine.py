"""Tests for the-evaluator rule engine."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts" / "evaluate-setup" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from the_evaluator.engine.types import Severity, RuleCategory, RuleMeta, DiagnosticLocation, ReportDescriptor
from the_evaluator.engine.registry import register_rule, get_all_rules, clear_rules, get_rules_by_category
from the_evaluator.engine.engine import parse_skill, lint, lint_directory
from the_evaluator.engine.suppression import parse_suppressions, is_suppressed
from the_evaluator.config.loader import load_config
from the_evaluator.config.presets import PRESETS

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
        content = "line 1\n<!-- evaluator-ignore-next-line: frontmatter/trigger-quality -->\ndescription: broad"
        suppressions = parse_suppressions(content)
        assert is_suppressed(suppressions, "frontmatter/trigger-quality", 3)
        assert not is_suppressed(suppressions, "frontmatter/trigger-quality", 1)

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
        for rule_id, severity in PRESETS["security"].items():
            if "security" not in rule_id:
                assert severity == "off"

    def test_load_config_default(self):
        config = load_config()
        assert config.preset_name == "recommended"
        assert "structural/skill-md-exists" in config.rules

    def test_load_config_preset_override(self):
        config = load_config(preset_override="security")
        assert config.preset_name == "security"
        assert config.rules.get("frontmatter/description-required") == "off"


class TestLint:
    def setup_method(self):
        clear_rules()
        from the_evaluator.rules import register_all_rules
        register_all_rules()

    def test_lint_good_skill(self):
        result = lint(str(FIXTURES / "good-skill"))
        trigger_warnings = [d for d in result.diagnostics if d.rule_id == "frontmatter/trigger-quality"]
        assert len(trigger_warnings) == 0

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
