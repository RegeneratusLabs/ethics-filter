# Ethics Filter — Universal Ethics Evaluation Engine

A modular, composable ethics evaluation engine that any AI agent or human can use to evaluate decisions through structured ethical reasoning. Ships as a Python SDK, CLI, MCP server, and Hermes plugin — no agent framework lock-in.

Every decision passes through six ethical modules, gated by a relevance engine. The output is a scored verdict with thresholds (GREEN / AMBER / RED), detected tensions between modules, and a permanent audit trail.

Verified against a 52-scenario corpus covering 9 decision categories (23 GREEN, 14 AMBER, 15 RED), pinned by regression tests.

## The Pipeline

1. **Intent clarification** — what exactly is being proposed?
2. **Stakeholder mapping** — who is affected?
3. **Module evaluation** — score each relevant module (0-100) against its rubric
4. **Conflict resolution** — surface material disagreements between modules
5. **Decision** — GREEN (proceed) / AMBER (flag for human judgment) / RED (block)
6. **Audit** — permanent JSONL record of every evaluation

## The 6 Modules

| Module | Core question | Fires when |
|---|---|---|
| Environmental | What is the impact on the natural world? | Physical resources, manufacturing, transport, energy, waste, emissions |
| Fairness | Who is treated fairly or unfairly? | Any decision affecting other people |
| Transparency | Would you publish this decision? | Non-trivial decisions with consequences |
| Conscious Leadership | Is this from above or below the line? | Values, relationships, integrity, moral weight |
| Ethical Framework | What would each ethical lens say? | Always (the meta-ethical lens) |
| Compliance | Does this breach any standard or law? | Legal, regulatory, or certification obligations |

Each module file (`ethics_filter/modules/*.md`) contains full criteria, scoring rubrics, questions, and edge cases, grounded in established frameworks: B Corp, IFOAM, Markkula Center, Conscious Capitalism, F-A-T-H-E-R.

Modules only fire when relevant. A personal apology does not get an environmental evaluation; the relevance engine gates automatically, with the ethical-framework module as the always-on backstop.

## Getting Started

### Install

```bash
uv pip install ethics-filter            # SDK + CLI (zero runtime deps)
uv pip install "ethics-filter[mcp]"     # + MCP server
```

Or from source:

```bash
git clone git@github.com:RegeneratusLabs/ethics-filter.git
cd ethics-filter
uv sync --all-extras
```

### CLI

```bash
# Brief mode — print the evaluation prompt any LLM can answer
ethics-filter evaluate "Hire this supplier" --context "organic farm, three quotes"

# Verdict mode — supply module scores, get the decision + audit record
ethics-filter evaluate "Fix prices with competitors" \
  --scores '{"fairness": 5, "transparency": 10, "ethical-framework": 5, "compliance": 5}'

# Explore
ethics-filter modules
ethics-filter constitutions
ethics-filter audit --tail 10
```

### Python SDK

```python
from ethics_filter import evaluate, build_evaluation_prompt, parse_evaluation_response

# Deterministic path: you supply module scores.
result = evaluate(
    action="Publish salary bands",
    context="50-person company, pay equity review",
    module_scores={"fairness": 90, "transparency": 85, "ethical-framework": 88},
    constitution_name="small-business-ethical",
)
print(result.decision, result.overall_score)  # green 87.7
print(result.to_dict())                       # full audit-ready record

# LLM-assisted path: build a brief, let a model score it, parse + audit it.
brief = build_evaluation_prompt("Approve this supplier", "organic farm, 3 quotes")
llm_response = your_llm(brief["prompt"])      # must match brief["json_schema"]
result = parse_evaluation_response(llm_response, "Approve this supplier")
```

`evaluate()` requires a score for every enabled module — no silent skips. Audit records append to `$ETHICS_FILTER_AUDIT` or `~/.ethics-filter/audit.jsonl` (disable with `audit=False`).

### MCP server (any MCP-compatible agent)

```bash
uv sync --extra mcp
uv run ethics-filter-mcp            # stdio (default)
uv run ethics-filter-mcp --transport sse   # remote deployment
```

**Tools:** `determine_relevant_modules`, `get_module_details`, `list_constitutions`, `get_constitution_details`, `build_prompt`, `evaluate`, `audit_tail`

**Resources:** `ethics://modules`, `ethics://module/{name}`, `ethics://constitutions`, `ethics://constitution/{name}`

Platform-specific setup (Claude Code, Claude Desktop, Cursor, Copilot, Cline, Continue, Aider, OpenAI Agents SDK, LangChain, Semantic Kernel, Google ADK, n8n, and more): see [`docs/platform-setup.md`](docs/platform-setup.md).

### Hermes plugin

The repo bundles a Hermes plugin that registers the skill, a `/ethics` slash command, and the `ethics_evaluate` tool (returns a fast evaluation brief by default; pass `scores` for a deterministic audited verdict, or `auto_score: true` to have the user's model score it):

```bash
hermes plugins install RegeneratusLabs/ethics-filter --enable
```

Or copy `plugin/` into `~/.hermes/plugins/` and run `hermes plugins enable ethics-filter`. See [`docs/hermes-integration.md`](docs/hermes-integration.md).

### Prompt-based (any LLM)

The module markdown files contain complete evaluation criteria and scoring rubrics. Any LLM can evaluate a decision by reading the relevant modules and applying the methodology — no software needed.

## Constitution Configuration

A "constitution" is the set of enabled modules plus a strictness level. Presets live in `ethics_filter/constitution/templates.json`:

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

## How It Works

The relevance engine scans the decision context and fires only the modules that apply. Scores are judgments made by a human or an LLM using the module rubrics. The engine then:

1. Validates that every enabled module has a score (0-100)
2. Aggregates to the mean of relevant module scores
3. Applies the strictness thresholds for the verdict
4. Flags modules scoring RED and detects material tensions (spread of 40+ points)
5. Writes a timestamped audit record to JSONL

The engine never fabricates scores; it makes scoring honest, consistent, and auditable.

## Testing

```bash
uv sync --all-extras
uv run pytest
```

~220 tests: unit tests for relevance/thresholds/aggregation/audit, CLI and MCP smoke tests, plugin registration tests, and the 52-scenario regression corpus.

## Project Structure

```
ethics-filter/
├── LICENSE
├── README.md
├── SKILL.md                        # portable skill for any agent
├── pyproject.toml
├── ethics_filter/                  # the engine (zero runtime deps)
│   ├── __init__.py
│   ├── engine.py                   # relevance, evaluation, audit
│   ├── cli.py                      # ethics-filter CLI
│   ├── mcp_server.py               # MCP server (optional mcp extra)
│   ├── modules/                    # 6 module rubrics
│   └── constitution/templates.json # presets + strictness levels
├── plugin/                         # Hermes plugin (self-contained)
│   ├── plugin.yaml
│   ├── __init__.py                 # registers skill + /ethics + tool
│   ├── skills/ethics-filter/       # bundled skill bundle
│   └── ethics_filter/              # vendored engine
├── docs/
│   ├── audit-report.md
│   ├── brief.md                    # original project brief
│   ├── hermes-integration.md
│   └── platform-setup.md
├── references/                     # skill reference docs
├── scripts/sync_skill.py           # regenerate plugin bundle + local skill
└── tests/
    ├── test_*.py                   # ~220 pytest tests
    └── scenarios.json              # 52-scenario regression corpus
```

## What Makes This Different

| Dimension | Existing guardrails | This engine |
|---|---|---|
| Focus | AI safety (hallucinations, PII) | Holistic ethics |
| Scope | LLM output safety | Any decision |
| Audience | Developers | Everyone |
| Source | Technical research | B Corp, Markkula Center, Conscious Capitalism |
| Modularity | One-size-fits-all | Per-person constitution |
| Integration | Single platform | SDK, CLI, MCP, Hermes plugin |

## Contributing

- **Bug reports**: open an issue
- **Feature requests**: open a discussion
- **Module contributions**: new ethical lenses are especially valued — copy the structure of an existing module file and ground it in an established framework
- **Keeping the plugin bundle in sync**: after changing `SKILL.md`, module files, or the engine, run `python scripts/sync_skill.py` (CI enforces this with `--check`)

## License

MIT — free to use, fork, modify, and distribute.

## The Bigger Picture

This skillset is the ethical conscience layer for any AI agent interacting with the world. Businesses plug it into procurement, hiring, and compliance pipelines. Individuals plug it into personal AI assistants. The long game: every AI runs decisions through an ethics filter by default.
