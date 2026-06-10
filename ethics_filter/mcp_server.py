"""Ethics Filter — MCP Server.

Provides the ethics evaluation engine as MCP tools and resources.
Any MCP-compatible host (Claude Desktop, Claude Code, Cursor, Copilot, etc.)
can connect and use the Ethics Filter.

Usage:
    uv run ethics-filter-mcp           # stdio transport (default for local tools)
    uv run ethics-filter-mcp --sse     # SSE transport (for remote connections)
"""

from __future__ import annotations
import json
import sys
from typing import Any

from ethics_filter.engine import (
    get_enabled_modules,
    get_constitution,
    get_module_content,
    load_constitutions,
    list_available_modules,
    check_relevance,
    build_evaluation_prompt,
    MODULE_NAMES,
    MODULE_EMOJI,
)

# ---------------------------------------------------------------------------
# MCP server using the official Python MCP SDK
# ---------------------------------------------------------------------------

def create_server():
    """Create and return the MCP server with all tools and resources."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "Error: The 'mcp' package is required.\n"
            "Install it with: uv add mcp  or  pip install mcp",
            file=sys.stderr,
        )
        sys.exit(1)

    mcp = FastMCP("Ethics Filter")

    # -----------------------------------------------------------------------
    # Tools
    # -----------------------------------------------------------------------

    @mcp.tool()
    def determine_relevant_modules(
        decision: str,
        context: str = "",
        constitution: str = "maximalist",
    ) -> str:
        """Determine which ethical modules are relevant to a decision based on keyword analysis.

        Args:
            decision: The proposed action or decision to evaluate.
            context: Additional background context about the decision.
            constitution: Which constitution preset to use (maximalist, small-business-ethical,
                         corporate-governance, startup-quick, personal-reflection, minimal-safe).
        """
        cons = get_constitution(constitution)
        enabled = get_enabled_modules(decision, context, cons)
        return json.dumps({
            "constitution": cons.name,
            "constitution_description": cons.description,
            "strictness": cons.strictness,
            "enabled_modules": enabled,
            "total": len(enabled),
        }, indent=2)

    @mcp.tool()
    def get_module_details(module_name: str) -> str:
        """Get the full criteria and scoring rubric for a specific ethical module.

        Args:
            module_name: One of: environmental, fairness, transparency,
                        conscious-leadership, ethical-framework, compliance.
        """
        if module_name not in MODULE_NAMES:
            available = ", ".join(MODULE_NAMES)
            return json.dumps({
                "error": f"Unknown module '{module_name}'. Available: {available}"
            })
        content = get_module_content(module_name)
        emoji = MODULE_EMOJI.get(module_name, "")
        return json.dumps({
            "name": module_name,
            "emoji": emoji,
            "content": content,
        }, indent=2)

    @mcp.tool()
    def list_constitutions() -> str:
        """List all available constitution presets with descriptions."""
        data = load_constitutions()
        presets = []
        for key, val in data["presets"].items():
            presets.append({
                "id": key,
                "name": val["name"],
                "description": val.get("description", ""),
                "strictness": val.get("strictness", "moderate"),
                "modules_enabled": sum(1 for v in val["modules"].values() if v),
                "modules_total": len(val["modules"]),
            })
        return json.dumps({
            "presets": presets,
            "strictness_levels": data["strictness_levels"],
        }, indent=2)

    @mcp.tool()
    def get_constitution_details(name: str = "maximalist") -> str:
        """Get the full configuration of a constitution preset.

        Args:
            name: Preset name (maximalist, small-business-ethical, corporate-governance,
                 startup-quick, personal-reflection, minimal-safe).
        """
        cons = get_constitution(name)
        data = load_constitutions()
        thresholds = data["strictness_levels"].get(cons.strictness, {})
        return json.dumps({
            "name": cons.name,
            "description": cons.description,
            "strictness": cons.strictness,
            "thresholds": thresholds,
            "modules": cons.modules,
        }, indent=2)

    @mcp.tool()
    def build_prompt(
        decision: str,
        context: str = "",
        constitution: str = "maximalist",
    ) -> str:
        """Build a complete evaluation prompt with module criteria embedded.

        The host LLM can use this prompt directly to produce a scored evaluation.
        Returns structured instructions including which modules are relevant,
        their full criteria content, and the output format required.

        Args:
            decision: The proposed action or decision to evaluate.
            context: Additional background context about the decision.
            constitution: Which constitution preset to use.
        """
        result = build_evaluation_prompt(decision, context, constitution)
        return json.dumps({
            "enabled_modules": result["enabled_modules"],
            "constitution": result["constitution"],
            "strictness": result["strictness"],
            "thresholds": result["thresholds"],
            "prompt": result["prompt"],
        }, indent=2)

    # -----------------------------------------------------------------------
    # Resources
    # -----------------------------------------------------------------------

    @mcp.resource("ethics://modules")
    def all_modules() -> str:
        """List all available ethical modules."""
        modules = list_available_modules()
        lines = ["# Available Ethical Modules\n"]
        for m in modules:
            lines.append(f"- {m['emoji']} **{m['name']}**")
        return "\n".join(lines)

    @mcp.resource("ethics://module/{name}")
    def module_content(name: str) -> str:
        """Get the full content of a module by name."""
        return get_module_content(name)

    @mcp.resource("ethics://constitutions")
    def constitutions_resource() -> str:
        """List all constitution presets."""
        data = load_constitutions()
        lines = ["# Constitution Presets\n"]
        for key, val in data["presets"].items():
            enabled = [k for k, v in val["modules"].items() if v]
            lines.append(
                f"- **{val['name']}** (`{key}`): {val.get('description', '')} "
                f"[Modules: {', '.join(enabled)}]"
            )
        return "\n".join(lines)

    @mcp.resource("ethics://constitution/{name}")
    def constitution_resource(name: str) -> str:
        """Get the full constitution preset configuration."""
        cons = get_constitution(name)
        data = load_constitutions()
        thresholds = data["strictness_levels"].get(cons.strictness, {})
        enabled = [k for k, v in cons.modules.items() if v]
        disabled = [k for k, v in cons.modules.items() if not v]
        return json.dumps({
            "name": cons.name,
            "description": cons.description,
            "strictness": cons.strictness,
            "red_threshold": thresholds.get("red_threshold"),
            "green_threshold": thresholds.get("green_threshold"),
            "modules_enabled": enabled,
            "modules_disabled": disabled,
        }, indent=2)

    return mcp


def main():
    """Run the MCP server with stdio transport (default for local tools)."""
    mcp = create_server()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
