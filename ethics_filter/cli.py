"""Ethics Filter — command line interface.

Usage:
    ethics-filter evaluate "ACTION" [--context TEXT] [--constitution NAME]
        [--strictness LEVEL] [--scores JSON] [--json] [--no-audit]
    ethics-filter audit [--tail N] [--json]
    ethics-filter modules
    ethics-filter constitutions
    ethics-filter version

Without ``--scores``, ``evaluate`` prints an evaluation brief (enabled
modules, thresholds, full rubric prompt) that any LLM can answer. With
``--scores`` it computes the verdict from the given module scores, writes an
audit record, and prints the result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ethics_filter import __version__
from ethics_filter.engine import (
    build_evaluation_prompt,
    evaluate,
    list_constitutions,
    list_modules,
    read_audit_log,
)


def _print_json(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _cmd_evaluate(args: argparse.Namespace) -> int:
    if not args.action:
        print("error: ACTION is required.", file=sys.stderr)
        return 2

    if args.scores:
        try:
            scores = json.loads(args.scores)
        except json.JSONDecodeError:
            print(f"error: --scores is not valid JSON: {args.scores}", file=sys.stderr)
            return 2
        if not isinstance(scores, dict):
            print("error: --scores must be a JSON object of module -> score.", file=sys.stderr)
            return 2
        try:
            result = evaluate(
                action=args.action,
                context=args.context,
                module_scores=scores,
                constitution_name=args.constitution,
                strictness=args.strictness,
                audit=not args.no_audit,
                audit_path=Path(args.audit_path) if args.audit_path else None,
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        if args.json:
            _print_json(result.to_dict())
        else:
            print(f"Decision: {result.decision.upper()}")
            print(f"Overall score: {result.overall_score:.1f} / 100")
            print(f"Constitution: {result.constitution} ({result.strictness})")
            print(f"Enabled modules: {', '.join(result.enabled_modules)}")
            for mr in result.module_results:
                verdict = (
                    "RED" if mr.score < result.thresholds["red_below"]
                    else "GREEN" if mr.score >= result.thresholds["green_at_or_above"]
                    else "AMBER"
                )
                print(f"  {mr.name:<22} {mr.score:>5.1f}  {verdict}")
            if result.tensions:
                print("Tensions:")
                for t in result.tensions:
                    print(f"  - {t}")
            if result.flags:
                print(f"Red-flagged modules: {', '.join(result.flags)}")
            print(f"Requires human review: {'yes' if result.requires_human else 'no'}")
            if result.reasoning:
                print(f"Reasoning: {result.reasoning}")
            if not args.no_audit:
                print("Audit record appended.")
        return 0

    # Brief mode: print the evaluation brief for an LLM to score.
    try:
        brief = build_evaluation_prompt(
            args.action, args.context, args.constitution
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        _print_json(
            {
                "action": brief["action"],
                "context": brief["context"],
                "constitution": brief["constitution"],
                "strictness": brief["strictness"],
                "enabled_modules": brief["enabled_modules"],
                "thresholds": brief["thresholds"],
                "prompt": brief["prompt"],
            }
        )
    else:
        print(f"Action: {args.action}")
        if args.context:
            print(f"Context: {args.context}")
        print(f"Constitution: {brief['constitution']} ({brief['strictness']})")
        print(f"Enabled modules ({len(brief['enabled_modules'])}): "
              f"{', '.join(brief['enabled_modules'])}")
        print(f"Thresholds: RED < {brief['thresholds']['red_below']:.0f}, "
              f"GREEN >= {brief['thresholds']['green_at_or_above']:.0f}")
        print("\n--- EVALUATION PROMPT ---\n")
        print(brief["prompt"])
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    records = read_audit_log(
        Path(args.audit_path) if args.audit_path else None,
        tail=args.tail,
    )
    if args.json:
        _print_json(records)
    else:
        if not records:
            print("No audit records found.")
            return 0
        print(f"Audit log ({len(records)} most recent records):")
        for r in records:
            print(
                f"  {r['timestamp']}  {r['decision'].upper():<5} "
                f"{r['overall_score']:>5.1f}  {r['action'][:60]}"
            )
    return 0


def _cmd_modules(_args: argparse.Namespace) -> int:
    modules = list_modules()
    for m in modules:
        always = " (always relevant)" if m["always_relevant"] else ""
        print(f"{m['name']:<22} {m['title']}{always}")
        print(f"  {m['description']}")
    return 0


def _cmd_constitutions(_args: argparse.Namespace) -> int:
    for c in list_constitutions():
        print(f"{c['id']:<24} {c['name']} ({c['strictness']})")
        print(f"  {c['description']}")
        print(f"  Enabled: {', '.join(c['modules_enabled'])}")
    return 0


def _cmd_version(_args: argparse.Namespace) -> int:
    print(f"ethics-filter {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ethics-filter",
        description="Universal ethics evaluation engine.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_eval = sub.add_parser("evaluate", help="Evaluate a decision")
    p_eval.add_argument("action", help="The proposed action or decision")
    p_eval.add_argument("--context", default="", help="Background context")
    p_eval.add_argument(
        "--constitution",
        default="small-business-ethical",
        help="Constitution preset (default: small-business-ethical)",
    )
    p_eval.add_argument(
        "--strictness",
        default=None,
        help="Override strictness: relaxed, moderate, strict",
    )
    p_eval.add_argument(
        "--scores",
        default=None,
        help='JSON object of module scores, e.g. \'{"fairness": 90, "compliance": 60}\'',
    )
    p_eval.add_argument("--json", action="store_true", help="Emit JSON output")
    p_eval.add_argument("--no-audit", action="store_true", help="Skip audit logging")
    p_eval.add_argument("--audit-path", default=None, help="Audit log file path")
    p_eval.set_defaults(func=_cmd_evaluate)

    p_audit = sub.add_parser("audit", help="Show recent audit records")
    p_audit.add_argument("--tail", type=int, default=20, help="Records to show")
    p_audit.add_argument("--json", action="store_true", help="Emit JSON output")
    p_audit.add_argument("--audit-path", default=None, help="Audit log file path")
    p_audit.set_defaults(func=_cmd_audit)

    p_mod = sub.add_parser("modules", help="List modules")
    p_mod.set_defaults(func=_cmd_modules)

    p_con = sub.add_parser("constitutions", help="List constitution presets")
    p_con.set_defaults(func=_cmd_constitutions)

    p_ver = sub.add_parser("version", help="Show version")
    p_ver.set_defaults(func=_cmd_version)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
