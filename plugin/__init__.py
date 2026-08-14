"""Ethics Filter — Hermes plugin.

Registers three things:
1. The bundled ``ethics-filter`` skill (loadable as ``plugin:ethics-filter``),
   with the module rubrics and constitution templates as linked files.
2. The ``/ethics`` slash command — evaluate a decision and get a readable
   verdict.
3. The ``ethics_evaluate`` tool — evaluate a decision and get a scored,
   auditable verdict. When ``scores`` is omitted, the user's own model is
   asked to score the decision against the module rubrics, then the engine
   computes the verdict and writes the audit record.

The plugin is self-contained: it vendors the engine under ``plugin/ethics_filter/``
so it works after ``hermes plugins install`` without a separate pip install.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    from ethics_filter.engine import (
        build_evaluation_prompt,
        evaluate,
        parse_evaluation_response,
    )
except ImportError:
    # Vendored copy inside the plugin bundle.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ethics_filter.engine import (  # noqa: F811
        build_evaluation_prompt,
        evaluate,
        parse_evaluation_response,
    )

SKILL_DIR = Path(__file__).resolve().parent / "skills" / "ethics-filter"

TOOL_SCHEMA = {
    "name": "ethics_evaluate",
    "description": (
        "Evaluate a decision through the Ethics Filter: six ethical modules "
        "(environmental, fairness, transparency, conscious leadership, ethical "
        "framework, compliance), strictness thresholds, tension detection, and "
        "a permanent audit trail. Returns a scored verdict (GREEN/AMBER/RED) "
        "with per-module scores and reasoning. When 'scores' is omitted, the "
        "user's model scores the decision against the module rubrics."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The proposed action or decision to evaluate.",
            },
            "context": {
                "type": "string",
                "description": "Background: stakeholders, constraints, relevant facts.",
            },
            "constitution": {
                "type": "string",
                "description": (
                    "Preset: small-business-ethical (default), personal-reflection, "
                    "corporate-governance, startup-quick, maximalist, minimal-safe."
                ),
            },
            "scores": {
                "type": "object",
                "description": (
                    "Optional 0-100 score for every relevant module, e.g. "
                    '{"fairness": 90, "compliance": 60}. Omit to auto-score '
                    "with the user's model."
                ),
            },
        },
        "required": ["action"],
    },
}


def _evaluate_to_dict(ctx, action, context, constitution, scores, reasoning=""):
    """Run the evaluation, returning a JSON-serialisable dict.

    With explicit scores the verdict is computed deterministically. Without
    scores, the user's model is asked to score the decision (falling back to
    returning the evaluation brief if that fails).
    """
    if scores:
        try:
            result = evaluate(
                action=action,
                context=context,
                module_scores=scores,
                constitution_name=constitution,
                reasoning=reasoning,
            )
            return result.to_dict()
        except ValueError as exc:
            return {"error": str(exc)}

    brief = build_evaluation_prompt(action, context, constitution)
    llm = getattr(ctx, "llm", None)
    complete = getattr(llm, "complete_structured", None) if llm else None
    if complete is not None:
        try:
            out = complete(prompt=brief["prompt"], schema=brief["json_schema"])
            text = out if isinstance(out, str) else json.dumps(out)
            result = parse_evaluation_response(
                text, action, context, constitution, reasoning=reasoning
            )
            return result.to_dict()
        except Exception as exc:  # noqa: BLE001 — plugin must not crash
            return {
                "error": f"LLM evaluation failed: {exc}",
                "prompt": brief["prompt"],
            }

    return {
        "status": "scores_required",
        "constitution": brief["constitution"],
        "strictness": brief["strictness"],
        "enabled_modules": brief["enabled_modules"],
        "thresholds": brief["thresholds"],
        "json_schema": brief["json_schema"],
        "prompt": brief["prompt"],
    }


def _parse_command_args(raw_args: str):
    """Parse /ethics args: the action plus optional --context/--constitution."""
    context = ""
    constitution = "small-business-ethical"
    ctx_match = re.search(r"--context\s+\"([^\"]+)\"", raw_args)
    if ctx_match:
        context = ctx_match.group(1)
    con_match = re.search(r"--constitution\s+(\S+)", raw_args)
    if con_match:
        constitution = con_match.group(1)
    action = re.sub(r"--context\s+\"[^\"]*\"", "", raw_args)
    action = re.sub(r"--constitution\s+\S+", "", action).strip()
    return action, context, constitution


def _format_readable(data: dict) -> str:
    if "error" in data:
        return f"Ethics Filter error: {data['error']}"
    if data.get("status") == "scores_required":
        lines = [
            "Ethics Filter — scores required. Provide module scores, e.g.:",
            f"  /ethics {data['prompt']}",
            "",
            "Or call ethics_evaluate with scores for every relevant module:",
            f"  {', '.join(data['enabled_modules'])}",
        ]
        return "\n".join(lines)
    decision = data.get("decision", "unknown").upper()
    lines = [
        f"Ethics Filter: {decision} (score {data.get('overall_score', 0):.1f}/100)",
        f"Constitution: {data.get('constitution', '')} ({data.get('strictness', '')})",
        f"Enabled modules: {', '.join(data.get('enabled_modules', []))}",
    ]
    for mr in data.get("module_results", []):
        lines.append(f"  {mr['name']:<22} {mr['score']:>5.1f}")
    for tension in data.get("tensions", []):
        lines.append(f"Tension: {tension}")
    if data.get("requires_human"):
        lines.append("Requires human review.")
    if data.get("reasoning"):
        lines.append(f"Reasoning: {data['reasoning']}")
    return "\n".join(lines)


def register(ctx) -> None:
    ctx.register_skill("ethics-filter", str(SKILL_DIR / "SKILL.md"))

    def handle_ethics_command(raw_args: str) -> str:
        action, context, constitution = _parse_command_args(raw_args)
        if not action:
            return (
                "Usage: /ethics <decision> [--context \"background\"] "
                "[--constitution <preset>]\n"
                "Example: /ethics \"Approve this supplier\" "
                "--context \"organic farm, 3 quotes\""
            )
        data = _evaluate_to_dict(
            ctx, action, context, constitution, scores=None
        )
        return _format_readable(data)

    ctx.register_command(
        "ethics",
        handle_ethics_command,
        description="Evaluate a decision through the Ethics Filter",
    )

    def handle_ethics_tool(params, **kwargs) -> str:
        del kwargs
        action = params.get("action", "")
        context = params.get("context", "")
        constitution = params.get("constitution", "small-business-ethical")
        scores = params.get("scores")
        data = _evaluate_to_dict(ctx, action, context, constitution, scores)
        return json.dumps(data, indent=2, ensure_ascii=False)

    ctx.register_tool(
        name="ethics_evaluate",
        toolset="ethics",
        schema=TOOL_SCHEMA,
        handler=handle_ethics_tool,
    )
