# Ethics Filter — Universal Ethics Evaluation Engine

A **modular, composable ethics skillset** that any AI agent — running inside a corporation, a small business, or someone's personal life — can use to evaluate decisions through structured ethical reasoning.

Not "ethics for ethical businesses." **Ethics for everyone who wants to be on the right side of AI.**

## The 6-Step Pipeline

Every decision passes through:

1. **Intent Clarification** — What exactly is being proposed?
2. **Stakeholder Mapping** — Who is affected?
3. **Module Evaluation** — Run through relevant ethical modules
4. **Conflict Resolution** — Harmonise tensions between modules
5. **Decision** — 🟢 GREEN / 🟡 AMBER / 🔴 RED
6. **Audit** — Permanent, traceable record of every evaluation

## The 6 Modules

| Module | Core Question |
|--------|--------------|
| 🌏 **Environmental** | What is the impact on the natural world? |
| 🤝 **Fairness** | Who is treated fairly or unfairly? |
| 🔓 **Transparency** | Would you publish this decision? |
| 🧘 **Conscious Leadership** | Is this from above or below the line? |
| ⚖️ **Ethical Framework** | What do different ethical lenses say? |
| 📋 **Compliance** | Does this breach any standard or law? |

## Module Relevance

Modules only fire when relevant to the decision context. A personal apology doesn't need environmental evaluation. A breakfast choice doesn't need compliance checking. The engine intelligently applies only the modules that matter.

## Getting Started

### As a Hermes Skill
```bash
# Load the skill
skill_view(name="ethics-filter")

# Evaluate a decision
"Run this through the ethics filter: [decision]. Use maximalist constitution at moderate strictness."
```

### As a Standalone Tool
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/ethics-filter
cd ethics-filter

# Run test scenarios
python3 tests/evaluate_v2.py

# Generate audit report
python3 tests/generate_report_v2.py
```

### As an MCP Tool
The ethics filter exposes an MCP server interface for any MCP-compatible agent.

### As an SDK Import
Drop the evaluation engine into any Python or TypeScript agent project.

## Constitution Configuration

A "constitution" is the set of modules you enable plus strictness levels:

```json
{
  "modules": {
    "environmental": true,
    "fairness": true,
    "transparency": true,
    "conscious-leadership": true,
    "ethical-framework": true,
    "compliance": true
  },
  "strictness": "moderate"
}
```

Strictness levels:
| Level | RED threshold | GREEN threshold |
|-------|---------------|-----------------|
| Relaxed | <30 | >70 |
| Moderate | <50 | >80 |
| Strict | <70 | >89 |

### Presets
| Preset | Use Case |
|--------|----------|
| **Personal Reflection** | Individual life decisions |
| **Small Ethical Business** | Values-driven enterprises |
| **Corporate Governance** | Enterprise compliance |
| **Startup Quick** | Early-stage lightweight check |
| **Maximalist** | High-stakes decisions |
| **Minimal Safe** | Baseline fairness + compliance |

## What Makes This Different

| Dimension | Existing Guardrails | This Skillset |
|-----------|-------------------|---------------|
| Focus | AI safety (hallucinations, PII) | **Holistic ethics** |
| Scope | LLM output safety | **Any decision** |
| Audience | Developers | **Everyone** |
| Source | Technical research | **B Corp, Markkula Center, Conscious Capitalism** |
| Modularity | One-size-fits-all | **Per-person constitution** |

## Test Results

52 scenarios evaluated across 9 categories:

- **Score range**: 5.0 (price fixing) → 100.0 (returning lost wallet)
- **GREEN (80+)**: 23 — ethical decisions correctly recognized
- **AMBER (50-79)**: 14 — tensions flagged for human judgment
- **RED (0-49)**: 15 — unethical decisions correctly blocked

Full report: [`docs/audit-report.md`](docs/audit-report.md)

## License

MIT — free to use, fork, modify, and distribute.

## Contributing

This is an open-source project built for the common good. PRs welcome.

- **Bug reports**: Open an issue
- **Feature requests**: Open a discussion
- **Module contributions**: New ethical lenses are especially valued

## The Bigger Picture

This skillset is the ethical conscience layer for *any* AI agent interacting with the world. Businesses plug it into procurement, hiring, and compliance pipelines. Individuals plug it into their personal AI assistants.

The long game: every AI runs decisions through an ethics filter by default. This is the first step.
