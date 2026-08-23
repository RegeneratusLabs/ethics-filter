"""Threshold and aggregation tests."""

import pytest

from ethics_filter.engine import Thresholds, evaluate, get_thresholds


class TestThresholds:
    @pytest.mark.parametrize(
        "strictness,red_below,green_at_or_above",
        [
            ("relaxed", 30, 70),
            ("moderate", 50, 80),
            ("strict", 70, 90),
        ],
    )
    def test_levels(self, strictness, red_below, green_at_or_above):
        t = get_thresholds(strictness)
        assert t.red_below == red_below
        assert t.green_at_or_above == green_at_or_above

    def test_classify_boundaries(self):
        t = Thresholds(red_below=50, green_at_or_above=80)
        assert t.classify(0) == "red"
        assert t.classify(49.9) == "red"
        assert t.classify(50) == "amber"
        assert t.classify(79.9) == "amber"
        assert t.classify(80) == "green"
        assert t.classify(100) == "green"

    def test_unknown_strictness_raises(self):
        with pytest.raises(ValueError):
            get_thresholds("ultra")


class TestEvaluateAggregation:
    def test_mean_of_enabled_modules(self, audit_path):
        result = evaluate(
            action="Publish salary bands",
            context="50-person company",
            module_scores={"fairness": 90, "transparency": 85, "ethical-framework": 88},
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.overall_score == pytest.approx((90 + 85 + 88) / 3)
        assert result.decision == "green"  # >= 80 moderate
        assert result.enabled_modules == ["fairness", "transparency", "ethical-framework"]

    def test_red_verdict_and_human_escalation(self, audit_path):
        result = evaluate(
            action="Fix prices with competitors",
            context="illegal, collusion",
            module_scores={
                "fairness": 5, "transparency": 10, "ethical-framework": 5,
                "compliance": 5,
            },
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.decision == "red"
        assert result.requires_human is True
        assert "fairness" in result.flags

    def test_red_module_vetoes_green_mean(self, audit_path):
        """A single RED module must block the decision, even if the mean is high."""
        result = evaluate(
            action="Contract cheap unvetted factory labour",
            context="compliance and labour concerns, potential forced labour risk",
            module_scores={
                "fairness": 90, "transparency": 85, "ethical-framework": 88,
                "compliance": 40,  # RED under moderate (red_below=50)
            },
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.overall_score == pytest.approx((90 + 85 + 88 + 40) / 4)
        assert result.decision == "red", "RED module must veto the mean"
        assert result.requires_human is True
        assert "compliance" in result.flags

    def test_no_red_module_no_veto(self, audit_path):
        result = evaluate(
            action="Publish salary bands",
            context="50-person company",
            module_scores={
                "fairness": 90, "transparency": 85, "ethical-framework": 88,
            },
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.decision == "green"
        assert result.flags == []

    def test_amber_midrange(self, audit_path):
        result = evaluate(
            action="Take a luxury vacation with high carbon footprint",
            context="travel, flights, resort",
            module_scores={
                "environmental": 40, "fairness": 75, "transparency": 70,
                "conscious-leadership": 60, "ethical-framework": 65,
            },
            constitution_name="personal-reflection",
            audit=False,
            audit_path=audit_path,
        )
        assert 50 <= result.overall_score < 80
        assert result.decision == "amber"

    def test_missing_score_raises(self, audit_path):
        with pytest.raises(ValueError, match="Missing scores for enabled modules"):
            evaluate(
                action="Restructure the team",
                context="affects 20 employees, hiring, firing",
                module_scores={"fairness": 90},
                constitution_name="small-business-ethical",
                audit=False,
                audit_path=audit_path,
            )

    def test_out_of_range_score_raises(self, audit_path):
        with pytest.raises(ValueError, match="0-100"):
            evaluate(
                action="Any decision",
                context="",
                module_scores={"fairness": 80, "transparency": 80, "ethical-framework": 150},
                constitution_name="small-business-ethical",
                audit=False,
                audit_path=audit_path,
            )

    def test_unknown_module_score_raises(self, audit_path):
        with pytest.raises(ValueError, match="Unknown module"):
            evaluate(
                action="Any decision",
                context="",
                module_scores={
                    "fairness": 80, "transparency": 80,
                    "ethical-framework": 80, "magic": 90,
                },
                constitution_name="small-business-ethical",
                audit=False,
                audit_path=audit_path,
            )

    def test_no_scores_raises(self, audit_path):
        with pytest.raises(ValueError, match="module_scores"):
            evaluate(
                action="Any decision",
                context="",
                module_scores=None,
                constitution_name="small-business-ethical",
                audit=False,
                audit_path=audit_path,
            )

    def test_tension_detection(self, audit_path):
        result = evaluate(
            action="Outsource customer service overseas",
            context="compliance and labour law considerations, employment impact",
            module_scores={
                "fairness": 30, "transparency": 80, "ethical-framework": 60,
                "compliance": 90,
            },
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.tensions, "expected a tension for a 60-point spread"
        assert "Module disagreement" in result.tensions[0]

    def test_strictness_override(self, audit_path):
        result = evaluate(
            action="Publish salary bands",
            context="50-person company",
            module_scores={"fairness": 90, "transparency": 85, "ethical-framework": 88},
            constitution_name="small-business-ethical",
            strictness="strict",
            audit=False,
            audit_path=audit_path,
        )
        # strict needs >= 90 for green; 87.7 is amber
        assert result.decision == "amber"
        assert result.strictness == "strict"

    def test_underscore_key_normalised_to_hyphen(self, audit_path):
        """Agent-supplied underscore keys must map to canonical hyphen names."""
        result = evaluate(
            action="Publish salary bands",
            context="50-person company",
            module_scores={
                "fairness": 90,
                "transparency": 85,
                "ethical_framework": 88,  # underscore -> ethical-framework
            },
            constitution_name="small-business-ethical",
            audit=False,
            audit_path=audit_path,
        )
        assert result.decision == "green"
        names = [m.name for m in result.module_results]
        assert "ethical-framework" in names
        assert all("_" not in n for n in names)
