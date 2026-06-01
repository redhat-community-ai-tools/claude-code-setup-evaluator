"""Tests for agent evaluation — parser, rules, and discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from the_evaluator.engine.engine import lint_agent, parse_agent
from the_evaluator.engine.registry import clear_rules
from the_evaluator.engine.types import ParsedSkill, Severity
from the_evaluator.rules import register_all_rules

FIXTURES = Path(__file__).parent / "fixtures" / "agents"
GOOD_AGENT = str(FIXTURES / "good-agent" / "agent.md")
BAD_AGENT = str(FIXTURES / "bad-agent" / "agent.md")


@pytest.fixture(autouse=True)
def _setup_rules():
    clear_rules()
    register_all_rules()


class TestParseAgent:
    def test_parse_good_agent(self):
        agent = parse_agent(GOOD_AGENT)
        assert agent.frontmatter["name"] == "review"
        assert agent.frontmatter["description"].startswith("Review PRs")
        assert agent.model == "opus"
        assert "code-review" in agent.referenced_skills
        assert "pr-review" in agent.referenced_skills
        assert len(agent.disallowed_tools) == 5
        assert "Edit" in agent.disallowed_tools
        assert "Write" in agent.disallowed_tools
        assert agent.tokens > 0
        assert not agent.parse_errors

    def test_parse_bad_agent(self):
        agent = parse_agent(BAD_AGENT)
        assert agent.frontmatter.get("name") == "broken-agent"
        assert agent.frontmatter.get("description") is None
        assert "nonexistent-skill" in agent.referenced_skills
        assert not agent.parse_errors

    def test_parse_missing_file(self):
        agent = parse_agent("/nonexistent/agent.md")
        assert len(agent.parse_errors) == 1
        assert "not found" in agent.parse_errors[0].lower()


class TestAgentDescriptionRequired:
    def test_good_agent_passes(self):
        result = lint_agent(GOOD_AGENT)
        rule_ids = [d.rule_id for d in result.diagnostics]
        assert "agent/description-required" not in rule_ids

    def test_bad_agent_missing_description(self):
        result = lint_agent(BAD_AGENT)
        diags = [d for d in result.diagnostics if d.rule_id == "agent/description-required"]
        assert len(diags) == 1
        assert diags[0].severity == Severity.ERROR


class TestReferencedSkillsExist:
    def _make_skill(self, name: str) -> ParsedSkill:
        return ParsedSkill(
            dir_path="",
            dir_name=name,
            skill_md_path="",
            raw_content="",
            frontmatter={},
            raw_frontmatter="",
            frontmatter_start_line=0,
            body="",
            body_start_line=0,
            files=[],
        )

    def test_missing_skills_flagged(self):
        result = lint_agent(BAD_AGENT, all_skills=[])
        diags = [d for d in result.diagnostics if d.rule_id == "agent/referenced-skills-exist"]
        assert len(diags) == 2
        messages = " ".join(d.message for d in diags)
        assert "nonexistent-skill" in messages
        assert "also-missing" in messages

    def test_present_skills_pass(self):
        skills = [self._make_skill("code-review"), self._make_skill("pr-review")]
        result = lint_agent(GOOD_AGENT, all_skills=skills)
        diags = [d for d in result.diagnostics if d.rule_id == "agent/referenced-skills-exist"]
        assert len(diags) == 0

    def test_partial_match(self):
        skills = [self._make_skill("code-review")]
        result = lint_agent(GOOD_AGENT, all_skills=skills)
        diags = [d for d in result.diagnostics if d.rule_id == "agent/referenced-skills-exist"]
        assert len(diags) == 1
        assert "pr-review" in diags[0].message


class TestDisallowedToolsParseable:
    def test_good_agent_passes(self):
        result = lint_agent(GOOD_AGENT)
        diags = [d for d in result.diagnostics if d.rule_id == "agent/disallowed-tools-parseable"]
        assert len(diags) == 0

    def test_bad_agent_unparseable(self):
        result = lint_agent(BAD_AGENT)
        diags = [d for d in result.diagnostics if d.rule_id == "agent/disallowed-tools-parseable"]
        assert len(diags) >= 1


class TestConstraintBodyMatch:
    def test_good_agent_constraints_matched(self):
        result = lint_agent(GOOD_AGENT)
        diags = [d for d in result.diagnostics if d.rule_id == "agent/constraint-body-match"]
        assert len(diags) == 0

    def test_bad_agent_no_body_constraints(self):
        result = lint_agent(BAD_AGENT)
        diags = [d for d in result.diagnostics if d.rule_id == "agent/constraint-body-match"]
        assert len(diags) == 0

    def test_unmatched_delete_constraint(self, tmp_path):
        agent_dir = tmp_path / "agents" / "delete-agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.md").write_text(
            '---\nname: delete-agent\ndescription: "Test agent"\n'
            'disallowedTools: "Edit"\n---\n\n'
            "You cannot delete files.\nYou cannot install packages.\n"
        )
        result = lint_agent(str(agent_dir / "agent.md"))
        diags = [d for d in result.diagnostics if d.rule_id == "agent/constraint-body-match"]
        labels = [d.message for d in diags]
        assert any("delete" in m for m in labels)
        assert any("install" in m for m in labels)


class TestLintAgent:
    def test_lint_result_type(self):
        result = lint_agent(GOOD_AGENT)
        assert result.target_type == "agent"
        assert result.target_name == "agent"
        assert result.tokens > 0

    def test_bad_agent_has_errors(self):
        result = lint_agent(BAD_AGENT)
        assert result.error_count > 0


class TestAgentDiscovery:
    def test_find_agents_in_fixtures(self):
        from the_evaluator.cli import _find_agents

        agents = _find_agents(FIXTURES)
        assert len(agents) == 2
        names = {a.name for a in agents}
        assert "agent.md" in names

    def test_has_agent_frontmatter(self):
        from the_evaluator.cli import _has_agent_frontmatter

        assert _has_agent_frontmatter(Path(GOOD_AGENT))
        assert _has_agent_frontmatter(Path(BAD_AGENT))

    def test_skill_not_detected_as_agent(self):
        from the_evaluator.cli import _has_agent_frontmatter

        skill_path = Path(__file__).parent / "fixtures" / "good-skill" / "SKILL.md"
        if skill_path.exists():
            assert not _has_agent_frontmatter(skill_path)


class TestFullsendIntegration:
    """Integration test against fullsend agents (if available)."""

    FULLSEND_AGENTS = (
        Path(__file__).parent.parent.parent
        / "repositories"
        / "fullsend"
        / "internal"
        / "scaffold"
        / "fullsend-repo"
        / "agents"
    )

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "repositories" / "fullsend").exists(),
        reason="fullsend repo not cloned",
    )
    def test_lint_fullsend_agents(self):
        from the_evaluator.cli import _find_agents

        agents = _find_agents(self.FULLSEND_AGENTS.parent)
        assert len(agents) >= 4

        for agent_path in agents:
            result = lint_agent(str(agent_path))
            assert result.target_type == "agent"
            assert result.tokens > 0
