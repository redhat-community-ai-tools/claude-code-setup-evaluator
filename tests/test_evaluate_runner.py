"""Tests for the evaluate command runner.

Covers pure helper functions: config parsing, question loading,
field extraction, and result processing.
"""
import json
from pathlib import Path

import pytest
import yaml

# runner.py is a PEP 723 script — import it by path
import importlib.util
import sys

ROOT = Path(__file__).parent.parent
_runner_path = ROOT / "commands" / "evaluate" / "runner.py"
_spec = importlib.util.spec_from_file_location("runner", _runner_path)
_runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_runner)

extract_field = _runner.extract_field
sanitize_label = _runner.sanitize_label
env_substitute = _runner.env_substitute
load_questions = _runner.load_questions
parse_config = _runner.parse_config
_parse_target = _runner._parse_target
_process_result = _runner._process_result
next_run_number = _runner.next_run_number


class TestExtractField:
    def test_simple_key(self):
        assert extract_field({"answer": "hello"}, "answer") == "hello"

    def test_nested_key(self):
        data = {"response": {"text": "hello"}}
        assert extract_field(data, "response.text") == "hello"

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": 42}}}
        assert extract_field(data, "a.b.c") == 42

    def test_missing_key_returns_none(self):
        assert extract_field({"a": 1}, "b") is None

    def test_missing_nested_key_returns_none(self):
        assert extract_field({"a": {"b": 1}}, "a.c") is None

    def test_non_dict_intermediate_returns_none(self):
        assert extract_field({"a": "string"}, "a.b") is None


class TestSanitizeLabel:
    def test_clean_label(self):
        assert sanitize_label("v1-test") == "v1-test"

    def test_spaces_replaced(self):
        assert sanitize_label("my version 1") == "my-version-1"

    def test_special_chars_replaced(self):
        assert sanitize_label("v1.0/beta@2") == "v1-0-beta-2"

    def test_leading_trailing_dashes_stripped(self):
        assert sanitize_label("!hello!") == "hello"


class TestEnvSubstitute:
    def test_substitutes_env_var(self, monkeypatch):
        monkeypatch.setenv("MY_TOKEN", "secret123")
        assert env_substitute("Bearer ${MY_TOKEN}") == "Bearer secret123"

    def test_missing_var_becomes_empty(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        assert env_substitute("key=${NONEXISTENT_VAR}") == "key="

    def test_no_substitution_needed(self):
        assert env_substitute("plain text") == "plain text"

    def test_multiple_vars(self, monkeypatch):
        monkeypatch.setenv("A", "1")
        monkeypatch.setenv("B", "2")
        assert env_substitute("${A}+${B}") == "1+2"


class TestLoadQuestions:
    def test_inline_questions(self):
        result = load_questions(["q1", "q2"], None)
        assert result == ["q1", "q2"]

    def test_txt_file(self, tmp_path):
        f = tmp_path / "questions.txt"
        f.write_text("question one\n# comment\nquestion two\n\n")
        result = load_questions(None, str(f))
        assert result == ["question one", "question two"]

    def test_yaml_file(self, tmp_path):
        f = tmp_path / "questions.yaml"
        f.write_text(yaml.dump(["q1", "q2"]))
        result = load_questions(None, str(f))
        assert result == ["q1", "q2"]

    def test_json_file(self, tmp_path):
        f = tmp_path / "questions.json"
        f.write_text(json.dumps(["q1", "q2"]))
        result = load_questions(None, str(f))
        assert result == ["q1", "q2"]

    def test_missing_file_raises(self):
        with pytest.raises(Exception, match="not found"):
            load_questions(None, "/nonexistent/file.txt")

    def test_unsupported_format_raises(self, tmp_path):
        f = tmp_path / "questions.csv"
        f.write_text("a,b,c")
        with pytest.raises(Exception, match="Unsupported"):
            load_questions(None, str(f))

    def test_no_questions_raises(self):
        with pytest.raises(Exception):
            load_questions(None, None)


class TestParseConfig:
    def _write_config(self, tmp_path, cfg: dict) -> Path:
        p = tmp_path / "eval.yaml"
        p.write_text(yaml.dump(cfg))
        return p

    def test_single_target_module(self, tmp_path):
        cfg = {
            "target": {"module": "mymod.run"},
            "questions": ["q1"],
        }
        result = parse_config(self._write_config(tmp_path, cfg))
        assert len(result["targets"]) == 1
        assert result["targets"][0]["type"] == "module"
        assert result["targets"][0]["value"] == "mymod.run"

    def test_single_target_command(self, tmp_path):
        cfg = {
            "target": {"command": "echo {question}"},
            "questions": ["q1"],
        }
        result = parse_config(self._write_config(tmp_path, cfg))
        assert result["targets"][0]["type"] == "command"

    def test_single_target_endpoint(self, tmp_path):
        cfg = {
            "target": {"endpoint": "http://localhost:8000/ask"},
            "questions": ["q1"],
        }
        result = parse_config(self._write_config(tmp_path, cfg))
        assert result["targets"][0]["type"] == "endpoint"

    def test_multi_target(self, tmp_path):
        cfg = {
            "targets": {
                "bot-a": {"module": "a.run", "questions": ["q1"]},
                "bot-b": {"command": "echo hi", "questions": ["q1"]},
            },
        }
        result = parse_config(self._write_config(tmp_path, cfg))
        assert len(result["targets"]) == 2
        names = {t["name"] for t in result["targets"]}
        assert names == {"bot-a", "bot-b"}

    def test_settings_override_defaults(self, tmp_path):
        cfg = {
            "settings": {"timeout": 60, "env_file": ".env.test"},
            "target": {"module": "m.run"},
            "questions": ["q1"],
        }
        result = parse_config(self._write_config(tmp_path, cfg))
        assert result["timeout"] == 60
        assert result["env_file"] == ".env.test"

    def test_default_timeout(self, tmp_path):
        cfg = {"target": {"module": "m.run"}, "questions": ["q1"]}
        result = parse_config(self._write_config(tmp_path, cfg))
        assert result["timeout"] == 30

    def test_missing_file_raises(self):
        with pytest.raises(Exception, match="not found"):
            parse_config(Path("/nonexistent/eval.yaml"))

    def test_empty_file_raises(self, tmp_path):
        p = tmp_path / "eval.yaml"
        p.write_text("")
        with pytest.raises(Exception, match="Empty"):
            parse_config(p)

    def test_no_target_key_raises(self, tmp_path):
        p = tmp_path / "eval.yaml"
        p.write_text(yaml.dump({"questions": ["q1"]}))
        with pytest.raises(Exception, match="target"):
            parse_config(p)

    def test_fields_propagated_to_single_target(self, tmp_path):
        cfg = {
            "target": {"module": "m.run"},
            "fields": {"answer": "response.text"},
            "questions": ["q1"],
        }
        result = parse_config(self._write_config(tmp_path, cfg))
        assert result["targets"][0]["fields"]["answer"] == "response.text"


class TestParseTarget:
    def test_module_target(self):
        t = _parse_target("test", {"module": "m.run"})
        assert t["type"] == "module"
        assert t["value"] == "m.run"
        assert t["name"] == "test"

    def test_command_target(self):
        t = _parse_target("test", {"command": "echo hi"})
        assert t["type"] == "command"

    def test_endpoint_target(self):
        t = _parse_target("test", {"endpoint": "http://localhost/ask"})
        assert t["type"] == "endpoint"

    def test_no_type_raises(self):
        with pytest.raises(Exception, match="must specify"):
            _parse_target("test", {"questions": ["q1"]})

    def test_custom_headers(self):
        t = _parse_target("test", {
            "endpoint": "http://localhost/ask",
            "headers": {"Authorization": "Bearer ${TOKEN}"},
        })
        assert t["headers"]["Authorization"] == "Bearer ${TOKEN}"

    def test_custom_request_field(self):
        t = _parse_target("test", {
            "endpoint": "http://localhost/ask",
            "request_field": "prompt",
        })
        assert t["request_field"] == "prompt"


class TestProcessResult:
    def _target(self, fields=None):
        return {"fields": fields or {}}

    def test_string_result(self):
        r = _process_result("hello", self._target(), 100)
        assert r["answer"] == "hello"
        assert r["latency_ms"] == 100
        assert r["error"] is None

    def test_dict_result_default_answer_key(self):
        r = _process_result({"answer": "hi"}, self._target(), 50)
        assert r["answer"] == "hi"

    def test_dict_result_custom_answer_field(self):
        data = {"response": {"text": "hello"}}
        r = _process_result(data, self._target({"answer": "response.text"}), 50)
        assert r["answer"] == "hello"

    def test_extra_fields_extracted(self):
        data = {"answer": "hi", "meta": {"tokens": 42}}
        r = _process_result(data, self._target({"tokens": "meta.tokens"}), 50)
        assert r["fields"]["tokens"] == 42

    def test_non_dict_non_string_converted(self):
        r = _process_result(42, self._target(), 10)
        assert r["answer"] == "42"


class TestNextRunNumber:
    def test_empty_index(self):
        assert next_run_number({"runs": []}) == 1

    def test_sequential(self):
        index = {"runs": [{"run_number": 1}, {"run_number": 2}]}
        assert next_run_number(index) == 3

    def test_with_gaps(self):
        index = {"runs": [{"run_number": 1}, {"run_number": 5}]}
        assert next_run_number(index) == 6
