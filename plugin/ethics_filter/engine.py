"""Ethics Filter — core evaluation engine.

Framework-agnostic. Zero runtime dependencies (stdlib only). Any Python
program, agent, or service can import this module directly.

The engine has three jobs:

1. **Relevance** — decide which of the six ethical modules apply to a
   proposed action given the decision text and the active constitution.
2. **Evaluation** — given a score (0-100) for each relevant module,
   aggregate them, apply strictness thresholds, detect tensions between
   modules, and produce a verdict: GREEN (proceed), AMBER (flag), or
   RED (block).
3. **Audit** — persist every evaluation as a JSONL record so decisions
   are traceable and defensible.

Scores are judgments made by a human or an LLM using the module rubrics
in ``ethics_filter/modules/``. The engine never fabricates scores; it
makes the scoring honest, consistent, and auditable.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PACKAGE_DIR = Path(__file__).resolve().parent
MODULES_DIR = PACKAGE_DIR / "modules"
CONSTITUTION_FILE = PACKAGE_DIR / "constitution" / "templates.json"

def default_audit_path() -> Path:
    """Resolve the audit log path from the environment at call time."""
    return Path(
        os.environ.get("ETHICS_FILTER_AUDIT", Path.home() / ".ethics-filter" / "audit.jsonl")
    )


DEFAULT_AUDIT_PATH = default_audit_path()

# ---------------------------------------------------------------------------
# Module registry
# ---------------------------------------------------------------------------

# ``relevant_when`` keywords gate a module on the lowercased action+context
# text. Modules with an empty list and no exclusions are always relevant.
# ``exclude_when`` phrases suppress a module when present.
MODULES: list[dict[str, Any]] = [
    {
        "name": "environmental",
        "title": "Environmental Stewardship",
        "description": (
            "Impact on the natural world: carbon, waste, water, biodiversity, "
            "resource use, lifecycle and circularity."
        ),
        "relevant_when": [
            "physical resources", "manufacturing", "transport", "energy",
            "waste", "packaging", "supply chain", "travel", "raw materials",
            "chemicals", "emissions", "water", "land use", "construction",
            "product design", "sourcing", "fossil fuels", "renewable",
            "shipping", "fleet", "facilities", "office", "hardware",
            "food production", "agriculture", "forestry", "mining",
            "carbon", "footprint", "recycling", "plastic", "sustainable",
            "eco", "environment", "climate", "co2", "green", "pollution",
        ],
        "exclude_when": [],
    },
    {
        "name": "fairness",
        "title": "Fairness & Stakeholder Impact",
        "description": (
            "Who is affected and how: equitable distribution of benefits and "
            "burdens, worker welfare, community impact, supply chain equity."
        ),
        "relevant_when": [],
        "exclude_when": [
            "purely personal preference",
            "trivial internal decision affecting only the decision-maker",
            "no external stakeholders",
            "no other people affected",
            "affects only the decision-maker",
        ],
    },
    {
        "name": "transparency",
        "title": "Transparency & Accountability",
        "description": (
            "Would you publish this decision: publicity test, traceability, "
            "accountability, values alignment, conflicts of interest."
        ),
        "relevant_when": [],
        "exclude_when": [
            "trivial personal preference without consequences",
            "purely personal preference",
            "no external stakeholders",
            "no deeper implications",
            "no wrong choice",
        ],
    },
    {
        "name": "conscious-leadership",
        "title": "Conscious Leadership & Values Alignment",
        "description": (
            "Above or below the line: ownership vs blame, values alignment, "
            "long-term vs short-term orientation, growth orientation."
        ),
        "relevant_when": [
            "values", "purpose", "long-term", "leadership", "culture",
            "team", "integrity", "dilemma", "difficult choice", "character",
            "role model", "conflict", "change management", "strategy",
            "hiring", "firing", "conversation", "accountability", "growth",
            "relationship", "family", "friend", "community", "care",
            "apology", "amends", "promotion", "career",
            "ethical", "morals", "principle", "responsibility", "trust",
        ],
        "exclude_when": [],
    },
    {
        "name": "ethical-framework",
        "title": "Ethical Decision Framework",
        "description": (
            "The meta-ethical lens: utilitarian, rights, fairness, common "
            "good, and virtue. Always relevant when enabled."
        ),
        "relevant_when": [],
        "exclude_when": [],
    },
    {
        "name": "compliance",
        "title": "Compliance & Certification Guard",
        "description": (
            "Legal, regulatory and certification obligations: certification "
            "risk, legal compliance, audit readiness, traceability, reporting."
        ),
        "relevant_when": [
            "legal", "regulation", "certification", "contract", "audit",
            "tax", "reporting", "license", "permit", "standard",
            "policy", "law", "compliance", "governance", "board",
            "disclosure", "filing", "statutory", "obligation",
            "b corp", "iso", "organic", "fair trade", "accredited",
            "employment", "privacy", "gdpr", "financial", "industry standard",
            "illegal", "crime", "unlawful", "toxic", "hazardous",
            "inspection", "regulatory", "statute", "liability",
            "negligence", "due diligence", "fiduciary", "oversight",
            "safety violation", "structural risk", "building code",
        ],
        "exclude_when": [],
    },
]

MODULE_NAMES: list[str] = [m["name"] for m in MODULES]

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Thresholds:
    """Decision thresholds for a strictness level.

    - RED: score < ``red_below``
    - AMBER: ``red_below`` <= score < ``green_at_or_above``
    - GREEN: score >= ``green_at_or_above``
    """

    red_below: float
    green_at_or_above: float

    def classify(self, score: float) -> str:
        if score < self.red_below:
            return "red"
        if score >= self.green_at_or_above:
            return "green"
        return "amber"


@dataclass(frozen=True)
class Constitution:
    name: str
    description: str
    modules: dict[str, bool]
    strictness: str


@dataclass
class ModuleResult:
    name: str
    score: float
    rationale: str = ""
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "rationale": self.rationale,
            "flags": self.flags,
        }


@dataclass
class EvaluationResult:
    """A complete, auditable evaluation."""

    action: str
    context: str
    decision: str  # green | amber | red
    overall_score: float
    module_results: list[ModuleResult]
    enabled_modules: list[str]
    constitution: str
    strictness: str
    thresholds: dict[str, float]
    flags: list[str] = field(default_factory=list)
    tensions: list[str] = field(default_factory=list)
    reasoning: str = ""
    requires_human: bool = False
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "context": self.context,
            "constitution": self.constitution,
            "strictness": self.strictness,
            "thresholds": self.thresholds,
            "enabled_modules": self.enabled_modules,
            "module_results": [m.to_dict() for m in self.module_results],
            "overall_score": round(self.overall_score, 2),
            "decision": self.decision,
            "flags": self.flags,
            "tensions": self.tensions,
            "reasoning": self.reasoning,
            "requires_human": self.requires_human,
        }


# ---------------------------------------------------------------------------
# Constitution loading
# ---------------------------------------------------------------------------


def load_constitutions(path: Optional[Path] = None) -> dict[str, Any]:
    """Load constitution templates from JSON."""
    p = path or CONSTITUTION_FILE
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def get_constitution(
    name: str = "small-business-ethical",
    constitutions: Optional[dict[str, Any]] = None,
) -> Constitution:
    """Get a constitution preset by name. Falls back to the default preset."""
    if constitutions is None:
        constitutions = load_constitutions()
    presets = constitutions["presets"]
    if name not in presets:
        raise ValueError(
            f"Unknown constitution '{name}'. "
            f"Available: {', '.join(sorted(presets))}"
        )
    preset = presets[name]
    return Constitution(
        name=preset["name"],
        description=preset.get("description", ""),
        modules=preset["modules"],
        strictness=preset.get("strictness", "moderate"),
    )


def list_constitutions(
    constitutions: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """Return metadata about all constitution presets."""
    if constitutions is None:
        constitutions = load_constitutions()
    return [
        {
            "id": key,
            "name": val["name"],
            "description": val.get("description", ""),
            "strictness": val.get("strictness", "moderate"),
            "modules_enabled": [k for k, v in val["modules"].items() if v],
        }
        for key, val in constitutions["presets"].items()
    ]


def get_thresholds(
    strictness: str,
    constitutions: Optional[dict[str, Any]] = None,
) -> Thresholds:
    """Get thresholds for a strictness level."""
    if constitutions is None:
        constitutions = load_constitutions()
    levels = constitutions["strictness_levels"]
    if strictness not in levels:
        raise ValueError(
            f"Unknown strictness '{strictness}'. "
            f"Available: {', '.join(sorted(levels))}"
        )
    s = levels[strictness]
    return Thresholds(
        red_below=float(s["red_threshold"]),
        green_at_or_above=float(s["green_threshold"]),
    )


# ---------------------------------------------------------------------------
# Module content
# ---------------------------------------------------------------------------


def get_module_content(module_name: str) -> str:
    """Read a module's markdown content from the package modules dir."""
    path = MODULES_DIR / f"{module_name}.md"
    if not path.exists():
        return f"# {module_name}\n\nModule content not found."
    return path.read_text(encoding="utf-8")


def list_modules() -> list[dict[str, Any]]:
    """Return metadata about all available modules."""
    return [
        {
            "name": m["name"],
            "title": m["title"],
            "description": m["description"],
            "always_relevant": not m["relevant_when"] and not m["exclude_when"],
        }
        for m in MODULES
    ]


# ---------------------------------------------------------------------------
# Relevance engine
# ---------------------------------------------------------------------------


def check_relevance(action: str, context: str, module: str) -> bool:
    """Return True if a module is relevant to the given decision text."""
    info = next((m for m in MODULES if m["name"] == module), None)
    if info is None:
        return False
    text = f"{action} {context}".lower()

    if info["exclude_when"]:
        for phrase in info["exclude_when"]:
            if phrase in text:
                return False

    if not info["relevant_when"]:
        # No inclusion keywords: relevant unless explicitly excluded
        # (ethical-framework, fairness, transparency).
        return True

    return any(kw in text for kw in info["relevant_when"])


def determine_relevant_modules(
    action: str,
    context: str,
    constitution: Constitution,
) -> list[str]:
    """Return modules that are both enabled in the constitution and relevant."""
    enabled = []
    for mod_name, active in constitution.modules.items():
        if not active:
            continue
        if check_relevance(action, context, mod_name):
            enabled.append(mod_name)
    return enabled


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_scores(
    scores: dict[str, float],
    enabled_modules: list[str],
) -> None:
    """Ensure every enabled module has a numeric score in 0-100."""
    missing = [m for m in enabled_modules if m not in scores]
    if missing:
        raise ValueError(
            f"Missing scores for enabled modules: {', '.join(missing)}. "
            f"Provided: {', '.join(sorted(scores)) or 'none'}."
        )
    for name, score in scores.items():
        if name not in MODULE_NAMES:
            raise ValueError(f"Unknown module '{name}' in scores.")
        if not isinstance(score, (int, float)):
            raise ValueError(f"Score for '{name}' must be numeric, got {score!r}.")
        if not 0 <= float(score) <= 100:
            raise ValueError(f"Score for '{name}' must be 0-100, got {score}.")


def _detect_tensions(module_results: list[ModuleResult]) -> list[str]:
    """Flag material disagreement between module verdicts."""
    if len(module_results) < 2:
        return []
    tensions: list[str] = []
    # A spread >= 40 points means the modules disagree hard.
    scores = [r.score for r in module_results]
    spread = max(scores) - min(scores)
    if spread >= 40:
        low = min(module_results, key=lambda r: r.score)
        high = max(module_results, key=lambda r: r.score)
        tensions.append(
            f"Module disagreement: {high.name} ({high.score:.0f}) vs "
            f"{low.name} ({low.score:.0f}) — resolve before acting."
        )
    return tensions


def evaluate(
    action: str,
    context: str = "",
    module_scores: Optional[dict[str, float]] = None,
    constitution_name: str = "small-business-ethical",
    strictness: Optional[str] = None,
    reasoning: str = "",
    audit: bool = True,
    audit_path: Optional[Path] = None,
    timestamp: Optional[str] = None,
) -> EvaluationResult:
    """Evaluate a decision end to end.

    ``module_scores`` maps module names to 0-100 scores. Every module that is
    both enabled by the constitution and relevant to the decision MUST have a
    score; missing scores raise ``ValueError``. The overall score is the mean
    of the relevant module scores; the verdict comes from the strictness
    thresholds.

    When ``audit`` is True the evaluation is appended to the JSONL audit log
    (default: ``$ETHICS_FILTER_AUDIT`` or ``~/.ethics-filter/audit.jsonl``).
    """
    constitutions = load_constitutions()
    constitution = get_constitution(constitution_name, constitutions)
    enabled = determine_relevant_modules(action, context, constitution)
    thresholds = get_thresholds(strictness or constitution.strictness, constitutions)

    if not module_scores:
        raise ValueError(
            "evaluate() requires module_scores. "
            "Use build_evaluation_prompt() to obtain scores from an LLM, "
            "then pass them here (or use parse_evaluation_response())."
        )

    _validate_scores(module_scores, enabled)

    module_results = [
        ModuleResult(
            name=name,
            score=float(module_scores[name]),
            flags=_module_flags(name, float(module_scores[name]), thresholds),
        )
        for name in enabled
    ]

    overall = sum(r.score for r in module_results) / len(module_results)
    decision = thresholds.classify(overall)

    # VETO: any enabled module scoring RED blocks the whole decision.
    # The mean must never dilute a genuine red flag into a pass — one module
    # in the block zone makes the decision a block, regardless of the average.
    if any(thresholds.classify(r.score) == "red" for r in module_results):
        decision = "red"

    flags = [r.name for r in module_results if thresholds.classify(r.score) == "red"]
    tensions = _detect_tensions(module_results)
    requires_human = decision == "red" or any(
        thresholds.classify(r.score) == "red" for r in module_results
    )

    result = EvaluationResult(
        action=action,
        context=context,
        decision=decision,
        overall_score=overall,
        module_results=module_results,
        enabled_modules=enabled,
        constitution=constitution.name,
        strictness=strictness or constitution.strictness,
        thresholds={
            "red_below": thresholds.red_below,
            "green_at_or_above": thresholds.green_at_or_above,
        },
        flags=flags,
        tensions=tensions,
        reasoning=reasoning,
        requires_human=requires_human,
        timestamp=timestamp or _utcnow_iso(),
    )

    if audit:
        _write_audit_record(result, audit_path)

    return result


def _module_flags(name: str, score: float, thresholds: Thresholds) -> list[str]:
    verdict = thresholds.classify(score)
    if verdict == "red":
        return [f"{name}: score {score:.0f} is below the {thresholds.red_below:.0f} red threshold"]
    if verdict == "amber":
        return [f"{name}: score {score:.0f} warrants review before proceeding"]
    return []


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


def _write_audit_record(result: EvaluationResult, audit_path: Optional[Path]) -> Path:
    path = Path(audit_path) if audit_path else default_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")
    return path


def read_audit_log(path: Optional[Path] = None, tail: int = 20) -> list[dict[str, Any]]:
    """Read the most recent ``tail`` audit records (newest last)."""
    p = Path(path) if path else default_audit_path()
    if not p.exists():
        return []
    records: list[dict[str, Any]] = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records[-tail:]


# ---------------------------------------------------------------------------
# LLM-assisted path
# ---------------------------------------------------------------------------

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "module_results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "score": {"type": "number", "minimum": 0, "maximum": 100},
                    "rationale": {"type": "string"},
                    "flags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "score", "rationale"],
            },
        },
        "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
        "decision": {"type": "string", "enum": ["green", "amber", "red"]},
        "reasoning": {"type": "string"},
    },
    "required": ["module_results", "overall_score", "decision", "reasoning"],
}


def build_evaluation_prompt(
    action: str,
    context: str = "",
    constitution_name: str = "small-business-ethical",
) -> dict[str, Any]:
    """Build a structured evaluation brief for an LLM.

    Returns a dict with the decision/context, the enabled modules, the full
    module rubric markdown, the thresholds, a ready-to-send ``prompt``, and a
    ``json_schema`` for structured output. Feed the LLM response to
    ``parse_evaluation_response()`` to get an ``EvaluationResult``.
    """
    constitutions = load_constitutions()
    constitution = get_constitution(constitution_name, constitutions)
    enabled = determine_relevant_modules(action, context, constitution)
    thresholds = get_thresholds(constitution.strictness, constitutions)

    modules_content = {name: get_module_content(name) for name in enabled}

    module_list = "\n".join(
        f"### {name}\n{modules_content[name]}" for name in enabled
    )

    prompt = f"""You are the Ethics Filter, a structured ethical evaluation engine.

Evaluate the proposed decision against each enabled module's rubric. For every
module, assign a score from 0 to 100 (higher = more ethical on that dimension)
and give a concise rationale. Scores are structured thinking aids, not
measurements — the reasoning matters more than the number.

## Decision to evaluate
Action: {action}
{('Context: ' + context) if context else ''}

## Constitution
Preset: {constitution.name}
Strictness: {constitution.strictness}
- GREEN (proceed): overall score >= {thresholds.green_at_or_above:.0f}
- AMBER (flag for human judgment): {thresholds.red_below:.0f} <= overall < {thresholds.green_at_or_above:.0f}
- RED (block, escalate to human): overall < {thresholds.red_below:.0f}

## Enabled modules ({len(enabled)})
{', '.join(enabled)}

## Module rubrics
{module_list}

## Output format
Respond ONLY with JSON matching this schema:
{json.dumps(OUTPUT_SCHEMA, indent=2)}

Rules:
- Score every enabled module. Do not skip modules.
- Anchor each score to a specific rubric band: state which band your score falls
  in (0-25 severe, 26-50 weak, 51-75 acceptable, 76-100 strong) and the evidence
  for it. DO NOT default to 70-90 for everything.
- Be hard on red flags. If any criterion for a module clearly fails, that module
  must score below the red threshold — a single red module blocks the decision.
- If modules disagree materially, note the tension in "reasoning".
- Any module scoring RED blocks the whole decision. When in doubt, prefer the
  stricter call. This filter is not a rubber stamp; a pass should be earned.
"""

    return {
        "action": action,
        "context": context,
        "constitution": constitution_name,
        "strictness": constitution.strictness,
        "enabled_modules": enabled,
        "module_contents": modules_content,
        "thresholds": {
            "red_below": thresholds.red_below,
            "green_at_or_above": thresholds.green_at_or_above,
        },
        "json_schema": OUTPUT_SCHEMA,
        "prompt": prompt,
    }


def parse_evaluation_response(
    text: str,
    action: str,
    context: str = "",
    constitution_name: str = "small-business-ethical",
    strictness: Optional[str] = None,
    reasoning: str = "",
    audit: bool = True,
    audit_path: Optional[Path] = None,
) -> EvaluationResult:
    """Parse an LLM's JSON response into an EvaluationResult.

    Tolerates markdown fences and extra prose around the JSON. Validates the
    module scores against the enabled modules, recomputes the overall score
    and verdict from the strictness thresholds (ignoring the LLM's own
    overall/decision if they disagree), and writes the audit record.
    """
    data = _extract_json(text)
    if data is None:
        raise ValueError("No valid JSON found in LLM response.")

    constitutions = load_constitutions()
    constitution = get_constitution(constitution_name, constitutions)
    enabled = determine_relevant_modules(action, context, constitution)
    thresholds = get_thresholds(strictness or constitution.strictness, constitutions)

    raw_results = data.get("module_results") or []
    scores: dict[str, float] = {}
    rationales: dict[str, str] = {}
    for item in raw_results:
        name = item.get("name", "")
        if name in MODULE_NAMES:
            try:
                scores[name] = float(item["score"])
            except (KeyError, TypeError, ValueError):
                continue
            rationales[name] = str(item.get("rationale", ""))

    _validate_scores(scores, enabled)

    module_results = [
        ModuleResult(
            name=name,
            score=scores[name],
            rationale=rationales.get(name, ""),
            flags=_module_flags(name, scores[name], thresholds),
        )
        for name in enabled
    ]
    overall = sum(r.score for r in module_results) / len(module_results)
    decision = thresholds.classify(overall)

    # VETO: any enabled module scoring RED blocks the whole decision (fail-closed).
    if any(thresholds.classify(r.score) == "red" for r in module_results):
        decision = "red"

    flags = [r.name for r in module_results if thresholds.classify(r.score) == "red"]
    tensions = _detect_tensions(module_results)

    result = EvaluationResult(
        action=action,
        context=context,
        decision=decision,
        overall_score=overall,
        module_results=module_results,
        enabled_modules=enabled,
        constitution=constitution.name,
        strictness=strictness or constitution.strictness,
        thresholds={
            "red_below": thresholds.red_below,
            "green_at_or_above": thresholds.green_at_or_above,
        },
        flags=flags,
        tensions=tensions,
        reasoning=reasoning or str(data.get("reasoning", "")),
        requires_human=decision == "red" or bool(flags),
        timestamp=_utcnow_iso(),
    )

    if audit:
        _write_audit_record(result, audit_path)

    return result


def _extract_json(text: str) -> Optional[dict[str, Any]]:
    """Pull the first balanced JSON object out of a string."""
    text = text.strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None
