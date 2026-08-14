"""Scenario regression suite — 52 real decisions from the original corpus.

Corpus semantics: the scenario authors scored only the modules they intended
to participate, and the relevance engine may over-fire on keywords (e.g. a
charity decision whose text mentions "environment" firing the environmental
module). The corpus therefore encodes its intended module set through score
coverage. ``corpus_verdict`` reproduces that: only enabled modules that have a
score participate in the mean.

The second test cross-checks that the strict ``evaluate()`` path (which
requires scores for EVERY enabled module) agrees with corpus semantics on the
41 scenarios where the corpus is complete.
"""

import json
from pathlib import Path

import pytest

from ethics_filter.engine import (
    determine_relevant_modules,
    evaluate,
    get_constitution,
    get_thresholds,
)

SCENARIOS_FILE = Path(__file__).parent / "scenarios.json"


def load_scenarios():
    with open(SCENARIOS_FILE, encoding="utf-8") as f:
        return json.load(f)


SCENARIOS = load_scenarios()


def corpus_enabled(scenario):
    cons = get_constitution(scenario["constitution"])
    return determine_relevant_modules(scenario["action"], scenario["context"], cons)


def corpus_verdict(scenario):
    """Verdict under corpus semantics (enabled modules that have scores)."""
    enabled = corpus_enabled(scenario)
    scores = {
        m: scenario["module_scores"][m]
        for m in enabled
        if m in scenario["module_scores"]
    }
    overall = sum(scores.values()) / len(scores)
    cons = get_constitution(scenario["constitution"])
    thresholds = get_thresholds(cons.strictness)
    return thresholds.classify(overall), overall


class TestCorpusMetadata:
    def test_52_scenarios(self):
        assert len(SCENARIOS) == 52

    def test_unique_ids(self):
        ids = [s["id"] for s in SCENARIOS]
        assert len(ids) == len(set(ids))

    def test_all_modules_covered(self):
        scored = {m for s in SCENARIOS for m in s["module_scores"]}
        assert {
            "environmental", "fairness", "transparency",
            "conscious-leadership", "ethical-framework", "compliance",
        } <= scored

    def test_expected_decision_valid(self):
        for s in SCENARIOS:
            assert s["expected_range"]["expected_decision"] in {"green", "amber", "red"}


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
def test_scenario_expected_verdict(scenario):
    verdict, _ = corpus_verdict(scenario)
    assert verdict == scenario["expected_range"]["expected_decision"]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
def test_scenario_score_range(scenario):
    _, overall = corpus_verdict(scenario)
    expected = scenario["expected_range"]
    assert expected["overall_min"] <= overall <= expected["overall_max"], (
        f"overall {overall:.1f} outside expected range "
        f"[{expected['overall_min']}, {expected['overall_max']}]"
    )


COMPLETE_SCENARIOS = [
    s for s in SCENARIOS
    if set(corpus_enabled(s)) <= set(s["module_scores"])
]


@pytest.mark.parametrize("scenario", COMPLETE_SCENARIOS, ids=lambda s: s["id"])
def test_strict_evaluate_agrees_with_corpus(scenario):
    """Where the corpus is complete, strict evaluate() must agree."""
    result = evaluate(
        action=scenario["action"],
        context=scenario["context"],
        module_scores=scenario["module_scores"],
        constitution_name=scenario["constitution"],
        audit=False,
    )
    assert result.decision == scenario["expected_range"]["expected_decision"]


def test_corpus_gaps_are_documented():
    """The corpus may under-score; assert the gap set is known and stable."""
    gaps = [
        s["id"] for s in SCENARIOS
        if not (set(corpus_enabled(s)) <= set(s["module_scores"]))
    ]
    assert gaps == [
        "A6", "B4", "B5", "C5", "G2", "G3", "G4", "G5", "H3", "I2", "I3",
    ], "if this changes, regenerate tests/scenarios.json from the engine"
