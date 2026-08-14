"""Ethics Filter — MCP server.

Exposes the ethics evaluation engine as MCP tools and resources so any
MCP-compatible host (Claude Code, Cursor, Copilot, Cline, Hermes, ...) can
evaluate decisions through the filter.

Usage:
    uv run --extra mcp ethics-filter-mcp                  # stdio (default)
    uv run --extra mcp ethics-filter-mcp --transport sse  # SSE
    uv run --extra mcp ethics-filter-mcp --transport http # HTTP
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional

from ethics_filter import engine as engine
from ethics_filter.engine import MODULE_NAMES


def create_server():
    """Create and return the MCP server with all tools and resources."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        print(
            "Error: the 'mcp' package is required. Install it with:\n"
            "  uv sync --extra mcp   (or)   pip install ethics-filter[mcp]",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    mcp = FastMCP("Ethics Filter")

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    @mcp.tool()
    def determine_relevant_modules(
        decision: str,
        context: str = "",
        constitution: str = "small-business-ethical",
    ) -> str:
        """Determine which ethical modules apply to a decision.

        Args:
            decision: The proposed action or decision to evaluate.
            context: Additional background context.
            constitution: Preset name (small-business-ethical, maximalist,
                corporate-governance, startup-quick, personal-reflection,
                minimal-safe).
        """
        cons = engine.get_constitution(constitution)
        enabled = engine.determine_relevant_modules(decision, context, cons)
        return json.dumps({
            "constitution": cons.name,
            "strictness": cons.strictness,
            "enabled_modules": enabled,
            "total": len(enabled),
        }, indent=2)

    @mcp.tool()
    def get_module_details(module_name: str) -> str:
        """Get the full criteria and scoring rubric for a module.

        Args:
            module_name: One of environmental, fairness, transparency,
                conscious-leadership, ethical-framework, compliance.
        """
        if module_name not in MODULE_NAMES:
            return json.dumps({
                "error": f"Unknown module '{module_name}'. "
                         f"Available: {', '.join(MODULE_NAMES)}"
            })
        meta = next(m for m in engine.list_modules() if m["name"] == module_name)
        return json.dumps({
            "name": module_name,
            "title": meta["title"],
            "description": meta["description"],
            "content": engine.get_module_content(module_name),
        }, indent=2)

    @mcp.tool()
    def list_constitutions() -> str:
        """List all available constitution presets."""
        return json.dumps({
            "presets": engine.list_constitutions(),
            "strictness_levels": engine.load_constitutions()["strictness_levels"],
        }, indent=2)

    @mcp.tool()
    def get_constitution_details(name: str = "small-business-ethical") -> str:
        """Get the full configuration of a constitution preset.

        Args:
            name: Preset name.
        """
        cons = engine.get_constitution(name)
        thresholds = engine.get_thresholds(cons.strictness)
        return json.dumps({
            "id": name,
            "name": cons.name,
            "description": cons.description,
            "strictness": cons.strictness,
            "thresholds": {
                "red_below": thresholds.red_below,
                "green_at_or_above": thresholds.green_at_or_above,
            },
            "modules": cons.modules,
        }, indent=2)

    @mcp.tool()
    def build_prompt(
        decision: str,
        context: str = "",
        constitution: str = "small-business-ethical",
    ) -> str:
        """Build a complete evaluation prompt with module criteria embedded.

        The host LLM answers the returned 'prompt' with JSON matching the
        returned 'json_schema', then feeds the answer to 'evaluate'.
        """
        result = engine.build_evaluation_prompt(decision, context, constitution)
        return json.dumps({
            "constitution": result["constitution"],
            "strictness": result["strictness"],
            "enabled_modules": result["enabled_modules"],
            "thresholds": result["thresholds"],
            "json_schema": result["json_schema"],
            "prompt": result["prompt"],
        }, indent=2)

    @mcp.tool()
    def evaluate(
        decision: str,
        context: str = "",
        constitution: str = "small-business-ethical",
        scores: Optional[dict] = None,
        reasoning: str = "",
    ) -> str:
        """Evaluate a decision and return a scored verdict.

        Args:
            decision: The proposed action or decision.
            context: Additional background context.
            constitution: Preset name.
            scores: JSON object mapping module names to 0-100 scores for every
                relevant module (e.g. {"fairness": 90, "compliance": 60}).
                If omitted, returns the evaluation brief instead of a verdict.
            reasoning: Optional summary of the evaluation.
        """
        try:
            if scores:
                result = engine.evaluate(
                    action=decision,
                    context=context,
                    module_scores=scores,
                    constitution_name=constitution,
                    reasoning=reasoning,
                )
                return json.dumps(result.to_dict(), indent=2)
            brief = engine.build_evaluation_prompt(decision, context, constitution)
            return json.dumps({
                "status": "scores_required",
                "constitution": brief["constitution"],
                "strictness": brief["strictness"],
                "enabled_modules": brief["enabled_modules"],
                "thresholds": brief["thresholds"],
                "json_schema": brief["json_schema"],
                "prompt": brief["prompt"],
            }, indent=2)
        except ValueError as exc:
            return json.dumps({"error": str(exc)}, indent=2)

    @mcp.tool()
    def audit_tail(tail: int = 20) -> str:
        """Return the most recent audit records.

        Args:
            tail: Number of records to return.
        """
        return json.dumps(engine.read_audit_log(tail=tail), indent=2)

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    @mcp.resource("ethics://modules")
    def all_modules() -> str:
        """List all available ethical modules."""
        lines = ["# Available Ethical Modules", ""]
        for m in engine.list_modules():
            always = " (always relevant)" if m["always_relevant"] else ""
            lines.append(f"- **{m['name']}** — {m['title']}{always}")
            lines.append(f"  {m['description']}")
        return "\n".join(lines)

    @mcp.resource("ethics://module/{name}")
    def module_content(name: str) -> str:
        """Get the full content of a module by name."""
        return engine.get_module_content(name)

    @mcp.resource("ethics://constitutions")
    def constitutions_resource() -> str:
        """List all constitution presets."""
        lines = ["# Constitution Presets", ""]
        for c in engine.list_constitutions():
            lines.append(
                f"- **{c['name']}** (`{c['id']}`, {c['strictness']}): "
                f"{c['description']} [Modules: {', '.join(c['modules_enabled'])}]"
            )
        return "\n".join(lines)

    @mcp.resource("ethics://constitution/{name}")
    def constitution_resource(name: str) -> str:
        """Get the full constitution preset configuration."""
        cons = engine.get_constitution(name)
        thresholds = engine.get_thresholds(cons.strictness)
        return json.dumps({
            "id": name,
            "name": cons.name,
            "description": cons.description,
            "strictness": cons.strictness,
            "red_below": thresholds.red_below,
            "green_at_or_above": thresholds.green_at_or_above,
            "modules_enabled": [k for k, v in cons.modules.items() if v],
            "modules_disabled": [k for k, v in cons.modules.items() if not v],
        }, indent=2)

    return mcp


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Ethics Filter MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport (default: stdio)",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Bind host for sse/http"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Bind port for sse/http"
    )
    args = parser.parse_args(argv)

    mcp = create_server()
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
