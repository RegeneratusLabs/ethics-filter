"""Prompt building and LLM response parsing tests."""

import json

import pytest

from ethics_filter.engine import (
    build_evaluation_prompt,
    get_module_content,
    parse_evaluation_response,
)


class TestBuildPrompt:
    def test_prompt_contains_modules_and_thresholds(self):
        brief = build_evaluation_prompt(
            "Publish salary bands",
            "50-person company",
            "small-business-ethical",
        )
        assert brief["enabled_modules"] == ["fairness", "transparency", "ethical-framework"]
        assert brief["strictness"] == "moderate"
        assert brief["thresholds"]["red_below"] == 50
        assert brief["thresholds"]["green_at_or_above"] == 80
        assert "Publish salary bands" in brief["prompt"]
        assert "fairness" in brief["prompt"]
        assert "json_schema" in brief
        assert "module_contents" in brief
        for mod in brief["enabled_modules"]:
            assert brief["module_contents"][mod] == get_module_content(mod)

    def test_prompt_includes_all_rubrics_for_illegal_action(self):
        brief = build_evaluation_prompt(
            "Dump toxic waste illegally",
            "hazardous chemicals, criminal liability",
            "maximalist",
        )
        # conscious-leadership does not keyword-match this text; the other
        # five modules fire.
        assert set(brief["enabled_modules"]) == {
            "environmental", "fairness", "transparency",
            "ethical-framework", "compliance",
        }


class TestParseResponse:
    SCORES = {
        "fairness": 90, "transparency": 85, "ethical-framework": 88,
    }

    def test_parses_clean_json(self, audit_path):
        raw = json.dumps({
            "module_results": [
                {"name": "fairness", "score": 90, "rationale": "equitable"},
                {"name": "transparency", "score": 85, "rationale": "open"},
                {"name": "ethical-framework", "score": 88, "rationale": "sound"},
            ],
            "overall_score": 87.7,
            "decision": "green",
            "reasoning": "broadly sound",
        })
        result = parse_evaluation_response(
            raw,
            action="Publish salary bands",
            context="50-person company",
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.decision == "green"
        assert result.overall_score == pytest.approx((90 + 85 + 88) / 3)
        assert len(result.module_results) == 3

    def test_tolerates_markdown_fence(self, audit_path):
        raw = '```json\n{"module_results": [{"name": "fairness", "score": 75, "rationale": "ok"}, {"name": "transparency", "score": 75, "rationale": "ok"}, {"name": "ethical-framework", "score": 75, "rationale": "ok"}], "overall_score": 75, "decision": "amber", "reasoning": "mixed"}\n```'
        result = parse_evaluation_response(
            raw,
            action="Any decision",
            context="",
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.decision == "amber"

    def test_recomputes_verdict_when_llm_is_wrong(self, audit_path):
        # LLM claims green but scores are red under the thresholds.
        raw = json.dumps({
            "module_results": [
                {"name": "fairness", "score": 10, "rationale": ""},
                {"name": "transparency", "score": 15, "rationale": ""},
                {"name": "ethical-framework", "score": 20, "rationale": ""},
                {"name": "compliance", "score": 25, "rationale": ""},
            ],
            "overall_score": 99,
            "decision": "green",
            "reasoning": "clearly fine",
        })
        result = parse_evaluation_response(
            raw,
            action="Fix prices with competitors",
            context="illegal collusion",
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.decision == "red"
        assert result.overall_score == pytest.approx(17.5)
        assert result.requires_human is True

    def test_ignores_unknown_module_scores(self, audit_path):
        raw = json.dumps({
            "module_results": [
                {"name": "fairness", "score": 80, "rationale": ""},
                {"name": "transparency", "score": 80, "rationale": ""},
                {"name": "ethical-framework", "score": 80, "rationale": ""},
                {"name": "magic-module", "score": 100, "rationale": ""},
            ],
            "overall_score": 80,
            "decision": "green",
            "reasoning": "",
        })
        result = parse_evaluation_response(
            raw,
            action="Any decision",
            context="",
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert [m.name for m in result.module_results] == ["fairness", "transparency", "ethical-framework"]

    def test_no_json_raises(self, audit_path):
        with pytest.raises(ValueError, match="No valid JSON"):
            parse_evaluation_response(
                "I refuse to answer in JSON.",
                action="Any decision",
                context="",
                constitution_name="small-business-ethical",
                audit=False,
                audit_path=audit_path,
            )

    def test_missing_module_raises(self, audit_path):
        raw = json.dumps({
            "module_results": [
                {"name": "fairness", "score": 80, "rationale": ""},
            ],
            "overall_score": 80,
            "decision": "green",
            "reasoning": "",
        })
        with pytest.raises(ValueError, match="Missing scores"):
            parse_evaluation_response(
                raw,
                action="Publish salary bands",
                context="pay equity audit",
                constitution_name="small-business-ethical",
                audit=False,
                audit_path=audit_path,
            )
