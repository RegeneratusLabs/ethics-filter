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
        "a permanent audit trail. Pass 'scores' to get a scored verdict "
        "(GREEN/AMBER/RED) computed deterministically. When 'scores' is omitted "
        "it returns the evaluation brief (enabled modules, thresholds, rubric "
        "prompt, JSON schema) for the host agent to score inline and reason "
        "over — so the agent ALWAYS replies. Set auto_score=true to have the "
        "plugin call the user's model to score instead (slower)."
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
                    '{"fairness": 90, "compliance": 60}. Provide to get a '
                    "deterministic verdict + audit record."
                ),
            },
            "auto_score": {
                "type": "boolean",
                "description": (
                    "When scores is omitted and auto_score is true, the plugin "
                    "asks the user's model to score the decision. Default false "
                    "(returns the brief for the agent to judge)."
                ),
            },
        },
        "required": ["action"],
    },
}


def _evaluate_to_dict(ctx, action, context, constitution, scores, auto_score=False, reasoning=""):
    """Run the evaluation, returning a JSON-serialisable dict.

    - With explicit ``scores``: deterministic verdict + audit record.
    - With no scores and ``auto_score=True``: ask the host's model to score.
    - With no scores and ``auto_score=False`` (default): return the evaluation
      brief so the HOST AGENT scores inline in its own reply. This is the robust
      path — no hidden nested LLM call that can stall a turn or lose the
      response if the client disconnects mid-evaluation.
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

    if auto_score:
        llm = getattr(ctx, "llm", None)
        complete = getattr(llm, "complete_structured", None) if llm else None
        if complete is not None:
            try:
                out = complete(
                    instructions=brief["prompt"],
                    input=[{"type": "text", "text": f"Decision to evaluate: {action}"}],
                    json_schema=brief["json_schema"],
                )
                raw = out.parsed if getattr(out, "parsed", None) is not None else out.text
                text = raw if isinstance(raw, str) else json.dumps(raw)
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
        "instructions": (
            "Score each enabled module 0-100 against its rubric and deliver the "
            "verdict in your reply. You may call ethics_evaluate again with "
            "{'scores': {...}} for the audited verdict."
        ),
        "action": brief["action"],
        "context": brief["context"],
        "constitution": brief["constitution"],
        "strictness": brief["strictness"],
        "enabled_modules": brief["enabled_modules"],
        "thresholds": brief["thresholds"],
        "json_schema": brief["json_schema"],
        "prompt": brief["prompt"],
    }


def _parse_command_args(raw_args: str):
    """Parse /ethics args: action + optional --context/--constitution/--brief.

    /ethics returns a scored VERDICT by default. --brief returns the evaluation
    worksheet instead (no model call).
    """
    context = ""
    constitution = "small-business-ethical"
    auto_score = True  # /ethics gives a verdict by default
    ctx_match = re.search(r"--context\s+\"([^\"]+)\"", raw_args)
    if ctx_match:
        context = ctx_match.group(1)
    con_match = re.search(r"--constitution\s+(\S+)", raw_args)
    if con_match:
        constitution = con_match.group(1)
    if re.search(r"--brief", raw_args):
        auto_score = False
    action = re.sub(r"--context\s+\"[^\"]*\"", "", raw_args)
    action = re.sub(r"--constitution\s+\S+", "", action)
    action = re.sub(r"--brief", "", action).strip()
    return action, context, constitution, auto_score


def _format_readable(data: dict) -> str:
    if "error" in data:
        return f"Ethics Filter error: {data['error']}"
    if data.get("status") == "scores_required":
        th = data.get("thresholds", {})
        lines = [
            "Ethics Filter — evaluation brief. Score each enabled module 0-100 "
            "against its rubric and deliver the verdict in your reply.",
            f"Action: {data.get('action', '')}",
            f"Constitution: {data.get('constitution', '')} ({data.get('strictness', '')})",
            f"Enabled modules: {', '.join(data.get('enabled_modules', []))}",
            f"Thresholds: RED < {th.get('red_below')}, "
            f"GREEN >= {th.get('green_at_or_above')}",
            "",
            "To get the audited verdict, pass scores: "
            "{'scores': {...}} for each enabled module.",
            "Or use --brief to just get the evaluation worksheet.",
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
    # The runtime calls .exists() on the skill path — pass a Path, not a str.
    ctx.register_skill("ethics-filter", SKILL_DIR / "SKILL.md")

    def handle_ethics_command(raw_args: str) -> str:
        action, context, constitution, auto_score = _parse_command_args(raw_args)
        if not action:
            return (
                "Usage: /ethics <decision> [--context \"background\"] "
                "[--constitution <preset>] [--brief]\n"
                "Example: /ethics \"Approve this supplier\" "
                "--context \"organic farm, 3 quotes\""
            )
        # The desktop slash worker (tui_gateway/slash_worker.py) is a persistent
        # CLI that runs the handler and captures its RETURN VALUE as the chat
        # bubble. It does NOT drain inject_message's _pending_input, so a
        # hand-off that returns only {"ok": true} renders an empty/no-op bubble
        # on the desktop. The health fix: compute the verdict right here and
        # return it as the command output, so the user sees the answer inline.
        # auto_score asks the host model to score against the module rubrics —
        # the same verified path the ethics_evaluate tool uses (fast, scored,
        # auditable). --brief returns the worksheet instead (no model call).
        data = _evaluate_to_dict(
            ctx, action, context, constitution,
            scores=None, auto_score=auto_score,
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
        auto_score = bool(params.get("auto_score", False))
        data = _evaluate_to_dict(
            ctx, action, context, constitution, scores, auto_score=auto_score
        )
        return json.dumps(data, indent=2, ensure_ascii=False)

    ctx.register_tool(
        name="ethics_evaluate",
        toolset="ethics",
        schema=TOOL_SCHEMA,
        handler=handle_ethics_tool,
    )
