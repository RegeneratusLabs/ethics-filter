"""MCP server tests: tool/resource registration and tool calls."""

import asyncio
import json

import pytest

from ethics_filter.mcp_server import create_server


def _run(coro):
    return asyncio.run(coro)


def _extract_text(result):
    """call_tool returns (content_blocks, structured) — pull the first text."""
    if isinstance(result, tuple):
        result = result[0]
    for block in result:
        text = getattr(block, "text", None)
        if text:
            return text
    return str(result)


@pytest.fixture(scope="module")
def server():
    return create_server()


class TestServerShape:
    def test_tools_registered(self, server):
        tools = _run(server.list_tools())
        names = {t.name for t in tools}
        assert {
            "determine_relevant_modules",
            "get_module_details",
            "list_constitutions",
            "get_constitution_details",
            "build_prompt",
            "evaluate",
            "audit_tail",
        } <= names

    def test_resources_registered(self, server):
        resources = _run(server.list_resources())
        uris = {str(r.uri) for r in resources}
        assert "ethics://modules" in uris
        assert "ethics://constitutions" in uris

    def test_resource_templates_registered(self, server):
        templates = _run(server.list_resource_templates())
        uris = {t.uriTemplate for t in templates}
        assert "ethics://module/{name}" in uris
        assert "ethics://constitution/{name}" in uris


class TestToolCalls:
    def test_determine_relevant_modules(self, server):
        result = _run(server.call_tool(
            "determine_relevant_modules",
            {"decision": "Dump toxic waste illegally", "context": "hazardous"},
        ))
        data = json.loads(_extract_text(result))
        assert "environmental" in data["enabled_modules"]
        assert "compliance" in data["enabled_modules"]

    def test_get_module_details(self, server):
        result = _run(server.call_tool("get_module_details", {"module_name": "fairness"}))
        data = json.loads(_extract_text(result))
        assert data["title"] == "Fairness & Stakeholder Impact"
        assert "Core Question" in data["content"]

    def test_get_module_details_unknown(self, server):
        result = _run(server.call_tool("get_module_details", {"module_name": "nope"}))
        data = json.loads(_extract_text(result))
        assert "error" in data

    def test_build_prompt(self, server):
        result = _run(server.call_tool(
            "build_prompt",
            {"decision": "Publish salary bands", "context": "50-person company"},
        ))
        data = json.loads(_extract_text(result))
        assert data["enabled_modules"] == ["fairness", "transparency", "ethical-framework"]
        assert "prompt" in data
        assert "json_schema" in data

    def test_evaluate_with_scores(self, server, monkeypatch, tmp_path):
        # Route the audit log to a tmp path so tests don't write home dirs.
        monkeypatch.setenv("ETHICS_FILTER_AUDIT", str(tmp_path / "audit.jsonl"))
        result = _run(server.call_tool(
            "evaluate",
            {
                "decision": "Fix prices with competitors",
                "context": "illegal collusion",
                "scores": {
                    "fairness": 5, "transparency": 10,
                    "ethical-framework": 5, "compliance": 5,
                },
            },
        ))
        data = json.loads(_extract_text(result))
        assert data["decision"] == "red"
        assert data["requires_human"] is True

    def test_evaluate_without_scores_returns_brief(self, server):
        result = _run(server.call_tool(
            "evaluate",
            {"decision": "Publish salary bands", "context": "50-person company"},
        ))
        data = json.loads(_extract_text(result))
        assert data["status"] == "scores_required"
        assert "prompt" in data

    def test_evaluate_missing_score_error(self, server):
        result = _run(server.call_tool(
            "evaluate",
            {"decision": "Publish salary bands", "context": "50-person company",
             "scores": {"fairness": 90}},
        ))
        data = json.loads(_extract_text(result))
        assert "error" in data
        assert "Missing scores" in data["error"]

    def test_audit_tail(self, server, monkeypatch, tmp_path):
        monkeypatch.setenv("ETHICS_FILTER_AUDIT", str(tmp_path / "audit.jsonl"))
        _run(server.call_tool(
            "evaluate",
            {"decision": "A test decision", "context": "",
             "scores": {"fairness": 80, "transparency": 80, "ethical-framework": 80}},
        ))
        result = _run(server.call_tool("audit_tail", {"tail": 5}))
        records = json.loads(_extract_text(result))
        assert len(records) >= 1
        assert records[-1]["action"] == "A test decision"


class TestResourceReads:
    def test_modules_resource(self, server):
        result = _run(server.read_resource("ethics://modules"))
        content = result[0].content if hasattr(result, "__getitem__") else str(result)
        assert "ethical-framework" in content

    def test_module_resource(self, server):
        result = _run(server.read_resource("ethics://module/compliance"))
        content = result[0].content if hasattr(result, "__getitem__") else str(result)
        assert "Compliance & Certification Guard" in content

    def test_constitution_resource(self, server):
        result = _run(server.read_resource("ethics://constitution/maximalist"))
        content = result[0].content if hasattr(result, "__getitem__") else str(result)
        data = json.loads(content)
        assert data["strictness"] == "strict"
