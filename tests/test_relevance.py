"""Relevance engine tests: keyword gating, exclusions, always-on modules."""

import pytest

from ethics_filter.engine import (
    check_relevance,
    determine_relevant_modules,
    get_constitution,
    list_modules,
)


class TestCheckRelevance:
    def test_environmental_keyword_hit(self):
        assert check_relevance(
            "Switch fleet to electric vehicles", "", "environmental"
        )

    def test_environmental_no_hit(self):
        assert not check_relevance(
            "Apologize to a friend for a mistake", "", "environmental"
        )

    def test_compliance_keyword_hit(self):
        assert check_relevance(
            "Draft the annual tax filing", "", "compliance"
        )

    def test_compliance_no_hit(self):
        assert not check_relevance(
            "Choose a restaurant for dinner", "", "compliance"
        )

    def test_conscious_leadership_relationship_keyword(self):
        assert check_relevance(
            "Have a difficult conversation with a team member", "", "conscious-leadership"
        )

    def test_fairness_exclusion_phrase(self):
        assert not check_relevance(
            "Choose my own breakfast cereal — purely personal preference",
            "",
            "fairness",
        )

    def test_fairness_defaults_to_relevant(self):
        assert check_relevance(
            "Restructure the sales team", "affects 20 employees", "fairness"
        )

    def test_transparency_exclusion_phrase(self):
        assert not check_relevance(
            "Pick a paint colour, trivial personal preference without consequences",
            "",
            "transparency",
        )

    def test_ethical_framework_always_relevant(self):
        assert check_relevance("Anything at all", "", "ethical-framework")

    def test_unknown_module_is_not_relevant(self):
        assert not check_relevance("Anything", "", "not-a-module")


class TestDetermineRelevantModules:
    def test_personal_decision_keeps_meta_only(self):
        cons = get_constitution("small-business-ethical")
        enabled = determine_relevant_modules(
            "Choose my own breakfast cereal — purely personal preference",
            "",
            cons,
        )
        assert enabled == ["ethical-framework"]

    def test_apology_skips_environmental_and_compliance(self):
        cons = get_constitution("small-business-ethical")
        enabled = determine_relevant_modules(
            "Send a sincere apology to a friend",
            "I was late and let them down",
            cons,
        )
        assert "environmental" not in enabled
        assert "compliance" not in enabled
        assert "ethical-framework" in enabled

    def test_disabled_modules_never_fire(self):
        cons = get_constitution("minimal-safe")
        enabled = determine_relevant_modules(
            "Build a new warehouse with concrete and steel",
            "manufacturing, transport, requires building permits and regulatory approval",
            cons,
        )
        assert "environmental" not in enabled  # disabled in minimal-safe
        assert "compliance" in enabled  # permit + regulatory keywords

    def test_all_modules_fire_for_illegal_dumping(self):
        cons = get_constitution("maximalist")
        enabled = determine_relevant_modules(
            "Dump toxic waste into the river at night",
            "illegal, hazardous chemicals",
            cons,
        )
        # conscious-leadership does not keyword-match this text (no values/
        # integrity/relationship terms); the other five fire.
        assert set(enabled) == {
            "environmental", "fairness", "transparency",
            "ethical-framework", "compliance",
        }


class TestListModules:
    def test_six_modules_with_descriptions(self):
        modules = list_modules()
        names = [m["name"] for m in modules]
        assert names == [
            "environmental", "fairness", "transparency",
            "conscious-leadership", "ethical-framework", "compliance",
        ]
        for m in modules:
            assert m["title"]
            assert m["description"]

    def test_ethical_framework_always_relevant_flag(self):
        by_name = {m["name"]: m for m in list_modules()}
        assert by_name["ethical-framework"]["always_relevant"] is True
        assert by_name["environmental"]["always_relevant"] is False
