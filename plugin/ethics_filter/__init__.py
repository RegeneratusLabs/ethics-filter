"""Ethics Filter — a framework-agnostic ethics evaluation engine.

Evaluate any decision — corporate, personal, or hybrid — through six
structured ethical modules, with strictness thresholds, tension detection,
and a permanent audit trail.

Public API:
    evaluate(action, context, module_scores, ...) -> EvaluationResult
    build_evaluation_prompt(action, context, ...)  -> brief for an LLM
    parse_evaluation_response(text, ...)           -> EvaluationResult
    determine_relevant_modules(action, context, constitution)
    list_modules(), list_constitutions()
    read_audit_log(tail=...)

Zero runtime dependencies. The MCP server and CLI are optional extras.
"""

from ethics_filter.engine import (
    Constitution,
    EvaluationResult,
    ModuleResult,
    Thresholds,
    build_evaluation_prompt,
    check_relevance,
    determine_relevant_modules,
    evaluate,
    get_constitution,
    get_module_content,
    get_thresholds,
    list_constitutions,
    list_modules,
    load_constitutions,
    parse_evaluation_response,
    read_audit_log,
)

__version__ = "1.0.0"

__all__ = [
    "Constitution",
    "EvaluationResult",
    "ModuleResult",
    "Thresholds",
    "build_evaluation_prompt",
    "check_relevance",
    "determine_relevant_modules",
    "evaluate",
    "get_constitution",
    "get_module_content",
    "get_thresholds",
    "list_constitutions",
    "list_modules",
    "load_constitutions",
    "parse_evaluation_response",
    "read_audit_log",
    "__version__",
]
