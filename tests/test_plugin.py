"""Hermes plugin tests using a mock ctx (no live Hermes session needed).

Follows the verified mock-ctx pattern from the hermes-plugin-development
skill: stub registrations, invoke handlers directly, assert on output.
"""

import importlib.util
import json
from pathlib import Path

import pytest

PLUGIN_INIT = Path(__file__).resolve().parent.parent / "plugin" / "__init__.py"


def _load_plugin():
    spec = importlib.util.spec_from_file_location("ethics_filter_plugin", PLUGIN_INIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PLUGIN = _load_plugin()


class FakeStructuredResult:
    """Duck-typed PluginLlmStructuredResult: .parsed (dict) + .text."""

    def __init__(self, parsed=None, text=""):
        self.parsed = parsed
        self.text = text


class MockLLM:
    def __init__(self, response):
        self.response = response
        self.last_kwargs = None

    def complete_structured(self, instructions=None, input=None, json_schema=None, **kwargs):
        self.last_kwargs = {
            "instructions": instructions,
            "input": input,
            "json_schema": json_schema,
        }
        return FakeStructuredResult(
            parsed=self.response, text=json.dumps(self.response)
        )


class MockCtx:
    def __init__(self, llm=None):
        self.commands = []
        self.hooks = []
        self.skills = []
        self.tools = []
        self.llm = llm
        self.injected = None

    def inject_message(self, content, role="user", **kwargs):
        self.injected = (role, content)

    def register_command(self, name, handler, description):
        self.commands.append((name, handler, description))

    def register_hook(self, name, cb):
        self.hooks.append((name, cb))

    def register_skill(self, name, path):
        self.skills.append((name, path))

    def register_tool(self, **kwargs):
        self.tools.append(kwargs)


def make_ctx(llm=None):
    return MockCtx(llm=llm)


class TestRegistration:
    def test_registers_skill(self):
        ctx = make_ctx()
        PLUGIN.register(ctx)
        names = [name for name, _ in ctx.skills]
        assert "ethics-filter" in names
        path = dict(ctx.skills)["ethics-filter"]
        # The runtime calls .exists() on the path — it must be a Path, not str.
        assert isinstance(path, Path)
        assert path.exists()

    def test_registers_command(self):
        ctx = make_ctx()
        PLUGIN.register(ctx)
        assert any(name == "ethics" for name, _, _ in ctx.commands)

    def test_registers_tool(self):
        ctx = make_ctx()
        PLUGIN.register(ctx)
        assert any(t["name"] == "ethics_evaluate" for t in ctx.tools)
        assert ctx.tools[0]["toolset"] == "ethics"
        assert "description" in ctx.tools[0]["schema"]

    def test_skill_path_points_to_bundled_skill(self):
        ctx = make_ctx()
        PLUGIN.register(ctx)
        path = dict(ctx.skills)["ethics-filter"]
        assert "plugin" in Path(path).parts
        assert Path(path).name == "SKILL.md"


class TestToolHandler:
    def test_with_scores_returns_verdict(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ETHICS_FILTER_AUDIT", str(tmp_path / "audit.jsonl"))
        ctx = make_ctx()
        PLUGIN.register(ctx)
        handler = ctx.tools[0]["handler"]
        out = handler({
            "action": "Fix prices with competitors",
            "context": "illegal collusion",
            "scores": {
                "fairness": 5, "transparency": 10,
                "ethical-framework": 5, "compliance": 5,
            },
        })
        data = json.loads(out)
        assert data["decision"] == "red"
        assert data["requires_human"] is True
        assert data["overall_score"] == 6.25

    def test_auto_score_uses_llm(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ETHICS_FILTER_AUDIT", str(tmp_path / "audit.jsonl"))
        llm = MockLLM({
            "module_results": [
                {"name": "fairness", "score": 90, "rationale": "equitable"},
                {"name": "transparency", "score": 85, "rationale": "open"},
                {"name": "ethical-framework", "score": 88, "rationale": "sound"},
            ],
            "overall_score": 87.7,
            "decision": "green",
            "reasoning": "broadly sound",
        })
        ctx = make_ctx(llm=llm)
        PLUGIN.register(ctx)
        handler = ctx.tools[0]["handler"]
        out = handler({
            "action": "Publish salary bands",
            "context": "50-person company",
            "auto_score": True,
        })
        data = json.loads(out)
        assert data["decision"] == "green"
        assert data["overall_score"] == pytest.approx(87.666, abs=0.01)
        assert len(data["module_results"]) == 3
        # The host API is complete_structured(instructions, input, json_schema).
        assert llm.last_kwargs["json_schema"]["type"] == "object"
        assert "Publish salary bands" in llm.last_kwargs["instructions"]
        assert llm.last_kwargs["input"][0]["type"] == "text"

    def test_default_returns_brief_without_calling_llm(self, tmp_path, monkeypatch):
        """Default (no scores, auto_score=False) NEVER fires the nested LLM."""
        monkeypatch.setenv("ETHICS_FILTER_AUDIT", str(tmp_path / "audit.jsonl"))
        llm = MockLLM({
            "module_results": [],
            "overall_score": 99,
            "decision": "green",
            "reasoning": "",
        })
        ctx = make_ctx(llm=llm)
        PLUGIN.register(ctx)
        handler = ctx.tools[0]["handler"]
        out = handler({
            "action": "Publish salary bands",
            "context": "50-person company",
        })
        data = json.loads(out)
        assert data["status"] == "scores_required"
        assert "prompt" in data
        assert data["enabled_modules"] == [
            "fairness", "transparency", "ethical-framework",
        ]
        # proof: the mock LLM was never invoked
        assert llm.last_kwargs is None

    def test_without_scores_and_no_llm_returns_brief(self):
        ctx = make_ctx(llm=None)
        PLUGIN.register(ctx)
        handler = ctx.tools[0]["handler"]
        out = handler({
            "action": "Publish salary bands",
            "context": "50-person company",
        })
        data = json.loads(out)
        assert data["status"] == "scores_required"
        assert "prompt" in data
        assert data["enabled_modules"] == [
            "fairness", "transparency", "ethical-framework",
        ]

    def test_missing_scores_error(self):
        ctx = make_ctx()
        PLUGIN.register(ctx)
        handler = ctx.tools[0]["handler"]
        out = handler({
            "action": "Publish salary bands",
            "context": "50-person company",
            "scores": {"fairness": 90},
        })
        data = json.loads(out)
        assert "error" in data
        assert "Missing scores" in data["error"]


class TestCommandHandler:
    def test_command_returns_verdict_inline(self, tmp_path, monkeypatch):
        """The desktop slash worker captures the handler's RETURN VALUE as the
        chat bubble. /ethics therefore computes and returns the verdict inline
        (via auto_score) instead of relying on inject_message, which the slash
        worker never drains (renders an empty/no-op bubble on desktop)."""
        monkeypatch.setenv("ETHICS_FILTER_AUDIT", str(tmp_path / "audit.jsonl"))
        llm = MockLLM({
            "module_results": [
                {"name": "fairness", "score": 82, "rationale": "equitable"},
                {"name": "transparency", "score": 78, "rationale": "open"},
                {"name": "ethical-framework", "score": 80, "rationale": "sound"},
                {"name": "compliance", "score": 75, "rationale": "ok"},
            ],
            "overall_score": 78.8,
            "decision": "amber",
            "reasoning": "broadly sound but needs due-diligence verification",
        })
        ctx = make_ctx(llm=llm)
        PLUGIN.register(ctx)
        handler = dict((name, h) for name, h, _ in ctx.commands)["ethics"]
        out = handler("Should I approve this organic farm supplier?")
        # The command output IS the rendered verdict — no inject_message.
        assert "AMBER" in out
        assert "78.8" in out
        assert "fairness" in out
        assert ctx.injected is None

    def test_command_parses_context_and_constitution(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ETHICS_FILTER_AUDIT", str(tmp_path / "audit.jsonl"))
        llm = MockLLM({
            "module_results": [
                {"name": "fairness", "score": 90, "rationale": "fair"},
                {"name": "transparency", "score": 90, "rationale": "clear"},
                {"name": "ethical-framework", "score": 90, "rationale": "sound"},
                {"name": "compliance", "score": 90, "rationale": "compliant"},
            ],
            "overall_score": 90,
            "decision": "green",
            "reasoning": "clean",
        })
        ctx = make_ctx(llm=llm)
        PLUGIN.register(ctx)
        handler = dict((name, h) for name, h, _ in ctx.commands)["ethics"]
        handler('Approve this partnership --context "local business, three quotes" --constitution minimal-safe')
        # Context and constitution are fed into the evaluation, not a kickoff.
        assert "local business, three quotes" in llm.last_kwargs["instructions"]
        assert "Minimal Safe Baseline" in llm.last_kwargs["instructions"]
        assert ctx.injected is None

    def test_command_brief_flag_returns_worksheet_without_llm(self, tmp_path, monkeypatch):
        """--brief skips the model call and returns the worksheet (no LLM)."""
        monkeypatch.setenv("ETHICS_FILTER_AUDIT", str(tmp_path / "audit.jsonl"))
        llm = MockLLM({})
        ctx = make_ctx(llm=llm)
        PLUGIN.register(ctx)
        handler = dict((name, h) for name, h, _ in ctx.commands)["ethics"]
        out = handler("Should I approve this supplier? --brief")
        assert "evaluation brief" in out.lower()
        assert "Score each enabled module" in out
        assert llm.last_kwargs is None  # no model call for --brief
        assert ctx.injected is None

    def test_empty_args_returns_usage(self):
        ctx = make_ctx()
        PLUGIN.register(ctx)
        handler = dict((name, h) for name, h, _ in ctx.commands)["ethics"]
        out = handler("")
        assert "Usage:" in out
