# Ethics Filter — Universal Ethics Evaluation Engine

A modular, composable ethics skillset that any AI agent can use to evaluate decisions through structured ethical reasoning. Works as an MCP server, Python SDK, or prompt-based tool — no agent framework lock-in.

## Pipeline

Every decision passes through six steps:

1. **Intent Clarification** — What exactly is being proposed?
2. **Stakeholder Mapping** — Who is affected?
3. **Module Evaluation** — Run through relevant ethical lenses
4. **Conflict Resolution** — Harmonise tensions between modules
5. **Decision** — GREEN (proceed) / AMBER (flag) / RED (block)
6. **Audit** — Permanent, traceable record of every evaluation

## The 6 Modules

| Module | Core Question |
|--------|---------------|
| Environmental | What is the impact on the natural world? |
| Fairness | Who is treated fairly or unfairly? |
| Transparency | Would you publish this decision? |
| Conscious Leadership | Is this from above or below the line? |
| Ethical Framework | What do different ethical lenses say? |
| Compliance | Does this breach any standard or law? |

Modules only fire when relevant to the decision context. A personal apology does not need environmental evaluation. The relevance engine gates automatically.

---

## Getting Started

### MCP Server (works with any MCP host)

```bash
git clone https://github.com/RegeneratusLabs/ethics-filter
cd ethics-filter
uv sync
uv run ethics-filter-mcp
```

Point your MCP host at the server. Tools auto-discover on connection.

**Tools exposed:**

| Tool | What it Does |
|------|-------------|
| `determine_relevant_modules` | Keyword analysis to determine which modules apply |
| `get_module_details` | Full criteria and scoring rubric for any module |
| `list_constitutions` | All constitution presets and strictness levels |
| `get_constitution_details` | Specific preset configuration |
| `build_prompt` | Complete structured prompt for LLM evaluation |

**Resources exposed:**

| Resource | What it Serves |
|----------|---------------|
| `ethics://modules` | List of all available modules |
| `ethics://module/{name}` | Full markdown content for a specific module |
| `ethics://constitutions` | All constitution presets |
| `ethics://constitution/{name}` | Specific preset JSON configuration |

Platform-specific setup (Claude Code, Claude Desktop, Cursor, Copilot, Cline, OpenAI Agents SDK, CrewAI, LangChain, Google ADK, and more): see [`docs/platform-setup.md`](docs/platform-setup.md).

---

### Python SDK

```python
from ethics_filter.engine import (
    determine_relevant_modules,   # check which modules apply
    get_module_content,           # read a module's criteria
    build_evaluation_prompt,      # build a structured LLM prompt
    list_available_modules,       # list all modules
)
```

No Hermes, no MCP, no agent framework required. Pure Python.

### Prompt-Based (any LLM, any platform)

The module markdown files in [`modules/`](modules/) contain complete evaluation criteria and scoring rubrics. Any LLM can evaluate a decision by reading the relevant modules and applying the methodology. No special software needed.

### Standalone Test Runner

```bash
cd ethics-filter
uv run python tests/evaluate_v2.py         # Run all 52 test scenarios
uv run python tests/generate_report_v2.py  # Generate audit report
```

### Hermes Agent

See [`docs/hermes-integration.md`](docs/hermes-integration.md) for the native Hermes Agent skill setup.

---

## How It Works

The Ethics Filter uses a relevance engine that scans the decision context for keywords to determine which of the 6 modules apply. The host LLM then evaluates each relevant module using the criteria in the corresponding markdown file, assigns scores (0-100), and produces an overall verdict.

**Evaluation pipeline:**

1. **Action + Context** — You provide what is being decided and the background
2. **Relevance Check** — Engine determines which modules apply
3. **Module Scoring** — LLM scores each relevant module using its rubric
4. **Aggregation** — Scores are averaged and compared against strictness thresholds
5. **Verdict** — GREEN / AMBER / RED

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

**Strictness levels:**

| Level | RED threshold | AMBER threshold | GREEN threshold |
|-------|---------------|-----------------|-----------------|
| Relaxed | <30 | 30–70 | >70 |
| Moderate | <50 | 50–74 | >74 |
| Strict | <70 | 70–89 | >89 |

**Presets:**

| Preset | Use Case |
|--------|----------|
| Personal Reflection | Individual life decisions |
| Small Ethical Business | Values-driven enterprises |
| Corporate Governance | Enterprise compliance |
| Startup Quick | Early-stage lightweight check |
| Maximalist | High-stakes decisions |
| Minimal Safe | Baseline fairness + compliance |

Full presets: [`constitution/templates.json`](constitution/templates.json)

---

## What Makes This Different

| Dimension | Existing Guardrails | This Skillset |
|-----------|-------------------|---------------|
| Focus | AI safety (hallucinations, PII) | Holistic ethics |
| Scope | LLM output safety | Any decision |
| Audience | Developers | Everyone |
| Source | Technical research | B Corp, Markkula Center, Conscious Capitalism |
| Modularity | One-size-fits-all | Per-person constitution |
| Integration | Single platform | MCP, SDK, prompt-based |

## Test Results

52 scenarios evaluated across 9 categories:

- **Score range**: 5.0 (price fixing) to 100.0 (returning lost wallet)
- **GREEN (80+)**: 23 — ethical decisions correctly recognized
- **AMBER (50-79)**: 14 — tensions flagged for human judgment
- **RED (0-49)**: 15 — unethical decisions correctly blocked

Full report: [`docs/audit-report.md`](docs/audit-report.md)

## Project Structure

```
ethics-filter/
├── LICENSE                       # MIT
├── README.md                     # This file
├── pyproject.toml                # Python package with MCP entry point
├── ethics_filter/
│   ├── __init__.py
│   ├── engine.py                 # Core evaluation engine (framework-agnostic)
│   └── mcp_server.py             # MCP server (uses engine.py)
├── constitution/
│   └── templates.json            # 6 presets, 3 strictness levels
├── modules/
│   ├── environmental.md          # Full module criteria and rubric
│   ├── fairness.md
│   ├── transparency.md
│   ├── conscious-leadership.md
│   ├── ethical-framework.md
│   └── compliance.md
├── docs/
│   ├── audit-report.md           # 52-scenario evaluation results
│   ├── brief.md                  # Original project brief
│   └── hermes-integration.md     # Hermes Agent setup
└── tests/
    ├── scenarios_v2.json
    ├── evaluate_v2.py            # Test runner
    ├── generate_report_v2.py
    └── results_v2.json
```

## License

MIT — free to use, fork, modify, and distribute.

## Contributing

- **Bug reports**: Open an issue
- **Feature requests**: Open a discussion
- **Module contributions**: New ethical lenses are especially valued

## The Bigger Picture

This skillset is the ethical conscience layer for any AI agent interacting with the world. Businesses plug it into procurement, hiring, and compliance pipelines. Individuals plug it into their personal AI assistants.

The long game: every AI runs decisions through an ethics filter by default. This is the first step.
