"""Ethics Filter — Core Evaluation Engine.

Framework-agnostic. No Hermes, no MCP, no agent dependencies.
Any Python code can import and use this module.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Where the module markdown files live (relative to this file or absolute)
MODULES_DIR = Path(__file__).resolve().parent.parent / "modules"
CONSTITUTION_FILE = Path(__file__).resolve().parent.parent / "constitution" / "templates.json"

# ---------------------------------------------------------------------------
# Module Relevance Rules
# ---------------------------------------------------------------------------

MODULE_RELEVANCE: dict[str, dict[str, list[str]]] = {
    "environmental": {
        "relevant_when": [
            "physical resources", "manufacturing", "transport", "energy",
            "waste", "packaging", "supply chain", "travel", "raw materials",
            "chemicals", "emissions", "water", "land use", "construction",
            "product design", "sourcing", "fossil fuels", "renewable",
            "shipping", "fleet", "facilities", "office", "hardware",
            "food production", "agriculture", "forestry", "mining",
            "carbon", "footprint", "recycling", "plastic", "sustainable",
            "eco", "environment", "climate", "co2", "green", "pollution",
        ]
    },
    "fairness": {
        "relevant_when": [],
        "exclude_when": [
            "purely personal preference",
            "trivial internal decision affecting only the decision-maker",
            "no external stakeholders",
            "no other people affected",
            "affects only the decision-maker",
        ]
    },
    "transparency": {
        "relevant_when": [],
        "exclude_when": [
            "trivial personal preference without consequences",
            "purely personal preference",
            "no external stakeholders",
            "no deeper implications",
            "no wrong choice",
        ]
    },
    "conscious-leadership": {
        "relevant_when": [
            "values", "purpose", "long-term", "leadership", "culture",
            "team", "integrity", "dilemma", "difficult choice", "character",
            "role model", "conflict", "change management", "strategy",
            "hiring", "firing", "conversation", "accountability", "growth",
            "relationship", "family", "friend", "community", "care",
            "apology", "amends", "promotion", "career",
            "ethical", "morals", "principle", "responsibility", "trust",
        ]
    },
    "ethical-framework": {
        "relevant_when": [],  # always relevant
    },
    "compliance": {
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
        ]
    },
}

MODULE_NAMES = [
    "environmental", "fairness", "transparency",
    "conscious-leadership", "ethical-framework", "compliance",
]

MODULE_EMOJI = {
    "environmental": "🌏",
    "fairness": "🤝",
    "transparency": "🔓",
    "conscious-leadership": "🧘",
    "ethical-framework": "⚖️",
    "compliance": "📋",
}

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class StrictnessLevel:
    red_threshold: float
    amber_min: float
    green_threshold: float

@dataclass
class Constitution:
    """A loaded constitution preset."""
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

@dataclass
class EvaluationResult:
    decision: str  # green, amber, red
    overall_score: float
    module_results: list[ModuleResult]
    enabled_modules: list[str]
    constitution: str
    strictness: str
    reasoning: str = ""

# ---------------------------------------------------------------------------
# Constitution loading
# ---------------------------------------------------------------------------

def load_constitutions(path: Optional[Path] = None) -> dict:
    """Load constitution templates from JSON."""
    p = path or CONSTITUTION_FILE
    with open(p) as f:
        return json.load(f)

def get_constitution(name: str = "maximalist", constitutions: Optional[dict] = None) -> Constitution:
    """Get a constitution preset by name."""
    if constitutions is None:
        constitutions = load_constitutions()
    preset = constitutions["presets"].get(name, constitutions["presets"]["maximalist"])
    return Constitution(
        name=preset["name"],
        description=preset.get("description", ""),
        modules=preset["modules"],
        strictness=preset.get("strictness", "moderate"),
    )

# ---------------------------------------------------------------------------
# Relevance engine
# ---------------------------------------------------------------------------

def check_relevance(action: str, context: str, module: str) -> bool:
    """Determine if a module is relevant to the given decision."""
    info = MODULE_RELEVANCE.get(module, {})
    text = (action + " " + context).lower()

    # If module has exclusion rules, check them first
    if info.get("exclude_when"):
        for exclude in info["exclude_when"]:
            if exclude.lower() in text:
                return False

    # If module has no inclusion keywords, it's always relevant (ethical-framework)
    if not info.get("relevant_when"):
        return True

    # Otherwise, check for keyword matches
    return any(kw.lower() in text for kw in info["relevant_when"])


def get_enabled_modules(
    action: str,
    context: str,
    constitution: Constitution,
) -> list[str]:
    """Return the list of modules that are both enabled in constitution AND relevant."""
    enabled = []
    text = (action + " " + context).lower()
    for mod, active in constitution.modules.items():
        if not active:
            continue
        # ethical-framework is always enabled when active
        if mod == "ethical-framework":
            enabled.append(mod)
            continue
        if check_relevance(action, context, mod):
            enabled.append(mod)
    return enabled


def get_thresholds(strictness: str, constitutions: Optional[dict] = None) -> StrictnessLevel:
    """Get threshold values for a strictness level."""
    if constitutions is None:
        constitutions = load_constitutions()
    s = constitutions["strictness_levels"].get(strictness, constitutions["strictness_levels"]["moderate"])
    return StrictnessLevel(
        red_threshold=s["red_threshold"],
        amber_min=s["amber_min"],
        green_threshold=s["green_threshold"],
    )


# ---------------------------------------------------------------------------
# Module content loading
# ---------------------------------------------------------------------------

def get_module_content(module_name: str) -> str:
    """Read a module's markdown content from the modules/ directory."""
    path = MODULES_DIR / f"{module_name}.md"
    if not path.exists():
        return f"# {module_name}\n\nModule content not found."
    with open(path) as f:
        return f.read()


def list_available_modules() -> list[dict]:
    """Return metadata about all available modules."""
    result = []
    for name in MODULE_NAMES:
        result.append({
            "name": name,
            "emoji": MODULE_EMOJI.get(name, ""),
            "description": MODULE_RELEVANCE.get(name, {}).get("relevant_when", ["Always on"]) if name == "ethical-framework" else [],
        })
    return result

# ---------------------------------------------------------------------------
# Evaluation builder
# ---------------------------------------------------------------------------

def build_evaluation_prompt(
    decision: str,
    context: str = "",
    constitution_name: str = "maximalist",
) -> dict:
    """Build a structured prompt that an LLM can use to evaluate a decision.

    Returns a dict with:
      - decision / context: the original inputs
      - enabled_modules: which modules to evaluate
      - constitution: the preset details
      - module_contents: the full markdown for each relevant module
      - prompt: a structured instruction the LLM should follow
    """
    constitutions = load_constitutions()
    constitution = get_constitution(constitution_name, constitutions)
    enabled = get_enabled_modules(decision, context, constitution)
    thresholds = get_thresholds(constitution.strictness, constitutions)

    modules_content = {}
    for mod_name in enabled:
        modules_content[mod_name] = get_module_content(mod_name)

    prompt = f"""You are the Ethics Filter — a structured ethical evaluation engine.

## Decision to evaluate
**Action**: {decision}
{"**Context**: " + context if context else ""}

## Constitution
**Preset**: {constitution.name}
**Strictness**: {constitution.strictness}
- GREEN >= {thresholds.green_threshold}
- AMBER = {thresholds.amber_min} to {thresholds.green_threshold - 1}
- RED < {thresholds.red_threshold}

## Enabled Modules ({len(enabled)})
{", ".join(f"{MODULE_EMOJI.get(m, '')} {m}" for m in enabled)}

## Instructions
For each enabled module, evaluate the decision against that module's criteria.
Assign a score (0-100) and provide reasoning. Then produce:
1. Per-module scores + flags
2. Overall score (average)
3. Final verdict: GREEN, AMBER, or RED
4. A summary of key tensions or concerns

Output your response as structured JSON with the following schema:
{{
  "module_results": [
    {{"name": "...", "score": 0-100, "rationale": "...", "flags": []}}
  ],
  "overall_score": 0-100,
  "decision": "green|amber|red",
  "reasoning": "summary of the evaluation"
}}
"""

    return {
        "decision": decision,
        "context": context,
        "constitution": constitution_name,
        "strictness": constitution.strictness,
        "enabled_modules": enabled,
        "module_contents": modules_content,
        "thresholds": {
            "green": thresholds.green_threshold,
            "amber_min": thresholds.amber_min,
            "red": thresholds.red_threshold,
        },
        "prompt": prompt,
    }
