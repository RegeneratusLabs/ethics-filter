# Canvas UI Pattern — Turn Ethics Modules into Interactive Agent Personas

This reference documents the pattern used in the [Ethics Filter Canvas](https://github.com/RegeneratusLabs/ethics-filter-canvas) — a web UI that wraps the 6 ethics modules into distinct character-based agent personas.

## Pattern Overview

Each ethics module becomes a named agent persona with:
- **Name** — short, memorable handle (e.g. "🌏 Steward" not "Environmental module")
- **Title** — role description (e.g. "Environmental Steward")
- **Tagline** — one-liner character summary ("Guardian of the natural world")
- **Color** — consistent identity color used across cards, score bars, and badges
- **Icon** — emoji or icon for visual identity
- **Prompt suffix** — lens-specific instruction telling the evaluator what to prioritise

## Persona Mapping

| Module Key | Persona Name | Icon | Color | Core Question |
|---|---|---|---|---|
| environmental | Steward | 🌏 🌿 | #2d8a4e | What is the impact on the natural world? |
| fairness | Advocate | 🤝 ⚖️ | #4a6fa5 | Who is treated fairly or unfairly? |
| transparency | Beacon | 🔓 💡 | #d4a843 | Would you publish this decision? |
| conscious-leadership | Sage | 🧘 🪷 | #8b5cf6 | Is this from above or below the line? |
| ethical-framework | Philosopher | ⚖️ 📜 | #e11d48 | What do different ethical lenses say? |
| compliance | Guardian | 📋 🛡️ | #0891b2 | Does this breach any standard or law? |

## Relevance Extension for Business Ideas

The original module relevance keywords (from `MODULE_RELEVANCE` in engine.py) are designed for generic decision evaluation. When wrapping in a product UI, extend the relevance detection with common business-domain heuristics:

**Environmental** — add: food, farm, grow, produce, land, resource, local, sustainable, organic, mile, nature, plant, animal, soil, water

**Fairness** — fire by default for any business idea (business decisions always affect people)

**Transparency** — fire by default for any non-trivial business idea

**Conscious Leadership** — add: purpose, mission, community, people, help, support, small, local, family, founder, vision, change, better, future

**Compliance** — add: data, privacy, money, payment, legal, regulate, bank, finance, insurance, health, certif, license, contract, platform

**Ethical Framework** — always fires

## Wrapping the Engine

The ethics_filter engine is purely functional (functions, not classes). Import directly:

```python
from ethics_filter.engine import (
    MODULE_RELEVANCE, MODULE_NAMES, MODULE_EMOJI,
    check_relevance, get_module_content, get_enabled_modules,
    load_constitutions, get_constitution, build_evaluation_prompt,
)
```

The engine does NOT have an `EthicsEngine` class — use standalone functions.

## Scoring (MVP / Keyword-Based)

For a zero-LLM MVP, use keyword-hit heuristics:

```python
def _evaluate_module(module_key, context):
    text_lower = context.lower()
    rules = MODULE_RELEVANCE.get(module_key, {})
    keywords = rules.get("relevant_when", [])
    hits = sum(1 for kw in keywords if kw in text_lower)
    ratio = min(hits / max(len(keywords) * 0.1, 1), 1.0)
    # More keyword matches = more ethical complexity = lower score
    base = 85 - (ratio * 30)
    return max(0, min(100, int(base)))
```

For production, replace with LLM evaluation using `build_evaluation_prompt()` which generates structured prompts with full module rubrics.

## Verdict Aggregation

Combine all agent scores into a single verdict:

| Condition | Verdict |
|---|---|
| Average >= 75 and no flags | 🟢 Green Light — proceed with confidence |
| Average >= 55 | 🟡 Proceed with Caution — review flagged agents |
| Average < 55 or critical flags | 🔴 Pause & Reflect — significant concerns |

## Related Skills

- `mvp-dashboard` — generic FastAPI dashboard patterns (auth, charts, deployment)
- `ethics-skillset-architecture` — how to design new module types
