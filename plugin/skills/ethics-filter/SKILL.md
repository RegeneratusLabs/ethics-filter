---
name: ethics-filter
description: "Use when evaluating any decision for ethical soundness across environmental, fairness, transparency, conscious-leadership, ethical-framework, and compliance dimensions, with a scored verdict and audit trail."
version: 1.0.0
author: Regeneratus Labs
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ethics, decision-framework, governance, compliance, values]
    related_skills: [ethics-skillset-architecture, deep-research]
linked_files:
  - modules/environmental.md
  - modules/fairness.md
  - modules/transparency.md
  - modules/conscious-leadership.md
  - modules/ethical-framework.md
  - modules/compliance.md
  - constitution/templates.json
  - references/ethics-frameworks.md
  - references/testing-methodology.md
  - references/agent-baseline-testing.md
---

# Ethics Filter — Universal Ethics Evaluation Engine

## Overview

A structured decision-evaluation engine that runs any proposed action — corporate, personal, or hybrid — through six independent ethical lenses. Each lens (module) fires only when contextually relevant. The output is a scored, auditable, reasoned evaluation with clear decision thresholds: GREEN (proceed), AMBER (flag for human judgment), RED (block).

The engine ships as:
- **Python SDK** — `evaluate()`, `build_evaluation_prompt()`, `parse_evaluation_response()`
- **CLI** — `ethics-filter evaluate "..." --scores '{...}'`
- **MCP server** — tools + resources for any MCP-compatible agent
- **Hermes plugin** — bundled skill, `/ethics` command, `ethics_evaluate` tool

Verified against a 52-scenario corpus covering 9 decision categories (23 GREEN, 14 AMBER, 15 RED), pinned by regression tests in `tests/test_scenarios.py`.

## When to Use

Use the filter for decisions that affect stakeholders, communities, the environment, or your own integrity:
- Business strategy, procurement, hiring, marketing, compliance
- Personal choices with moral weight: relationships, career, family, finance
- Building AI agents that need an ethical reasoning layer
- Auditing past decisions for ethical blind spots

Do not use for:
- Purely aesthetic choices with zero external impact
- Decisions already governed by a functioning ethical review board with audit trail
- Trivial daily preferences where evaluation cost exceeds decision impact
- Emergencies requiring immediate action (evaluate post-action as an audit instead)
- Decisions with no agency, where the decision-maker is mandated by law with no discretion

## The Pipeline

1. **Intent clarification** — restate the proposed action in plain language; surface ambiguity.
2. **Stakeholder mapping** — identify direct, indirect, and systemic stakeholders.
3. **Module evaluation** — score each *relevant* module (0-100) against its rubric.
4. **Conflict resolution** — surface tensions when modules disagree materially (spread of 40+ points).
5. **Decision** — apply strictness thresholds to the mean of relevant module scores.
6. **Audit** — append a permanent JSONL record of every evaluation.

### Module relevance

Modules fire only when the decision context matches. Rules:

| Module | Fires when |
|---|---|
| Environmental | Decision involves physical resources, manufacturing, transport, energy, waste, emissions, etc. |
| Fairness | Decision affects other people (skipped only for explicitly personal, stakeholder-free decisions) |
| Transparency | Decision is non-trivial (skipped only for trivial personal preferences) |
| Conscious Leadership | Decision involves values, relationships, integrity, or moral weight |
| Ethical Framework | Always fires when enabled — the meta-ethical lens |
| Compliance | Legal, regulatory, or certification obligations exist |

Relevance is keyword-based and deliberately conservative: the ethical-framework module always fires as a backstop, and the LLM-driven prompt path asks the model to score every enabled module.

### Modules

| Module | File | Core question |
|---|---|---|
| Environmental | `modules/environmental.md` | What is the impact on the natural world? |
| Fairness | `modules/fairness.md` | Who is treated fairly or unfairly? |
| Transparency | `modules/transparency.md` | Would you publish this decision? |
| Conscious Leadership | `modules/conscious-leadership.md` | Is this from above or below the line? |
| Ethical Framework | `modules/ethical-framework.md` | What would each ethical lens say? |
| Compliance | `modules/compliance.md` | Does this breach any standard or law? |

Each module file contains its criteria, scoring rubric, questions, and edge cases, grounded in established frameworks (B Corp, IFOAM, Markkula Center, Conscious Capitalism, F-A-T-H-E-R).

## Constitution Configuration

A "constitution" is the set of enabled modules plus a strictness level. Presets live in `constitution/templates.json`:

| Preset | Use case | Strictness |
|---|---|---|
| personal-reflection | Individual life decisions | moderate |
| small-business-ethical | Values-driven SMEs | moderate |
| corporate-governance | Larger organizations | strict |
| startup-quick | Lightweight early-stage check | relaxed |
| maximalist | High-stakes decisions | strict |
| minimal-safe | Baseline fairness + compliance | moderate |

Thresholds per strictness level:

| Level | RED (block) | AMBER (flag) | GREEN (proceed) |
|---|---|---|---|
| Relaxed | < 30 | 30-69 | >= 70 |
| Moderate | < 50 | 50-79 | >= 80 |
| Strict | < 70 | 70-89 | >= 90 |

## Using the Engine

### Python SDK

```python
from ethics_filter import evaluate, build_evaluation_prompt, parse_evaluation_response

# Deterministic path: you (or an LLM) supply module scores.
result = evaluate(
    action="Publish salary bands",
    context="50-person company, pay equity review",
    module_scores={"fairness": 90, "transparency": 85, "ethical-framework": 88},
    constitution_name="small-business-ethical",
)
print(result.decision, result.overall_score)  # green 87.7

# LLM-assisted path: build a brief, let a model score it, parse + audit it.
brief = build_evaluation_prompt("Approve this supplier", "organic farm, 3 quotes")
llm_response = llm_complete(brief["prompt"])  # whatever model you use
result = parse_evaluation_response(llm_response, "Approve this supplier")
```

`evaluate()` requires a score for every enabled module; missing scores raise `ValueError`. Audit records are appended to `$ETHICS_FILTER_AUDIT` or `~/.ethics-filter/audit.jsonl` (disable with `audit=False`).

### CLI

```bash
# Brief mode — print the evaluation prompt for an LLM
ethics-filter evaluate "Hire this supplier" --context "organic farm, 3 quotes"

# Verdict mode — supply module scores, get the decision + audit record
ethics-filter evaluate "Fix prices with competitors" \
  --scores '{"fairness": 5, "transparency": 10, "ethical-framework": 5, "compliance": 5}'

# Inspect the audit trail
ethics-filter audit --tail 10
```

### MCP server

```bash
uv sync --extra mcp
uv run ethics-filter-mcp            # stdio transport
uv run ethics-filter-mcp --transport sse   # remote hosting
```

Tools: `determine_relevant_modules`, `get_module_details`, `list_constitutions`, `get_constitution_details`, `build_prompt`, `evaluate`, `audit_tail`. Resources: `ethics://modules`, `ethics://module/{name}`, `ethics://constitutions`, `ethics://constitution/{name}`.

### Hermes plugin

The repo bundles a Hermes plugin (`plugin/`) that registers:
- the `ethics-filter` skill (loadable as `plugin:ethics-filter`)
- the `/ethics` slash command
- the `ethics_evaluate` tool (auto-scores via the user's model when scores are omitted)

Install with `hermes plugins install RegeneratusLabs/ethics-filter --enable`, or copy `plugin/` into `~/.hermes/plugins/` and run `hermes plugins enable ethics-filter`. See `docs/hermes-integration.md`.

### Any other agent

Point your MCP host at the server, or read the module rubrics and run the pipeline directly — the methodology is framework-agnostic by design.

## Common Mistakes

1. **Applying all 6 modules when only 1-2 are relevant** — let the relevance engine gate.
2. **Confusing compliance with ethics** ("it is legal so it is fine") — a decision can be perfectly legal and deeply unethical. The "borderline legal" trap (structuring decisions to avoid legal definitions while producing the same harm) is the most common version.
3. **Treating scores as objective truth** — scores are structured thinking aids, not measurements. The value is in the reasoning.
4. **Skipping stakeholder mapping** — the most skipped step and the one that catches the most blind spots.
5. **Using relaxed strictness to greenlight decisions that should be amber** — strictness should match stakes, not desired outcome.
6. **Evaluating retroactively to justify** rather than prospectively to guide.
7. **Letting urgency bypass the pipeline** — urgency does not absolve ethical responsibility.
8. **Assuming "obviously ethical" decisions need no evaluation** — hidden stakeholder impacts and reputational cover are real.

## Testing

```bash
uv sync --all-extras
uv run pytest          # ~190 tests: unit, CLI, MCP, audit, 52-scenario corpus
```

The scenario corpus (`tests/scenarios.json`) is the regression spine: 52 real decisions with expected verdicts, including 11 scenarios where the corpus intentionally under-scores (keyword relevance over-fires; the corpus encodes intended relevance through score coverage — see `tests/test_scenarios.py`).

## License

MIT — free to use, fork, modify, and distribute.

## Bigger Picture

This skillset is the ethical conscience layer for any AI agent interacting with the world: businesses plug it into procurement, hiring, and compliance pipelines; individuals plug it into personal assistants. The long game is that every AI runs decisions through an ethics filter by default.
