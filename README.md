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

The Ethics Filter is **framework-agnostic** — use it from any agent, any platform, any programming language.

---

### 🔌 MCP Server (Universal — works with any MCP host)

The Ethics Filter exposes an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that any MCP-compatible host can connect to.

#### Quick Start

```bash
# Clone the repo
git clone https://github.com/RegeneratusLabs/ethics-filter
cd ethics-filter

# Install dependencies and start the MCP server
uv sync
uv run ethics-filter-mcp
```

Then point your MCP host at it. The server auto-discovers tools on connection.

#### Tools Exposed

| Tool | What it Does |
|------|-------------|
| `determine_relevant_modules` | Keyword analysis to see which modules apply to a decision |
| `get_module_details` | Returns the full criteria and scoring rubric for any module |
| `list_constitutions` | Lists all constitution presets and strictness levels |
| `get_constitution_details` | Returns a specific preset's full configuration |
| `build_prompt` | Builds a complete structured prompt the LLM can use to score the decision |

#### Resources Exposed

| Resource | What it Serves |
|----------|---------------|
| `ethics://modules` | List of all available modules |
| `ethics://module/{name}` | Full markdown content for a specific module |
| `ethics://constitutions` | All constitution presets |
| `ethics://constitution/{name}` | Specific preset JSON configuration |

#### Platform Config Examples

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add ethics-filter -- uv run ethics-filter-mcp
```
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ethics-filter": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ethics-filter", "ethics-filter-mcp"]
    }
  }
}
```
</details>

<details>
<summary><b>Cursor</b></summary>

Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "ethics-filter": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ethics-filter", "ethics-filter-mcp"]
    }
  }
}
```
</details>

<details>
<summary><b>GitHub Copilot</b></summary>

VS Code → Settings → Copilot → MCP → Add server:
- Name: `ethics-filter`
- Type: `stdio`
- Command: `uv run ethics-filter-mcp`
</details>

<details>
<summary><b>Cline / Roo Code</b></summary>

In the MCP configuration UI, add a new server:
- Name: `ethics-filter`
- Command: `uv run ethics-filter-mcp`
</details>

<details>
<summary><b>OpenAI Agents SDK</b></summary>

```python
from agents import Agent, MCPServerStdio

async with MCPServerStdio(
    name="ethics-filter",
    params={"command": "uv", "args": ["run", "ethics-filter-mcp"]}
) as server:
    agent = Agent(
        name="Assistant",
        instructions="You can evaluate decisions through the ethics filter.",
        mcp_servers=[server]
    )
    result = await Runner.run(agent, "Run this through the ethics filter: launch a new product line")
```
</details>

<details>
<summary><b>CrewAI</b></summary>

```python
from crewai import Agent

ethics_officer = Agent(
    role="Ethics Officer",
    goal="Ensure all decisions pass ethical review",
    mcps=["https://ethics-filter.example.com/mcp"]
)
```
</details>

<details>
<summary><b>LangChain / LangGraph</b></summary>

```python
from langchain_core.tools import tool
from ethics_filter import evaluate

@tool
def ethics_evaluation(decision: str, constitution: str = "maximalist") -> str:
    """Evaluate a decision through 6 ethical modules."""
    result = evaluate(decision, constitution)
    return f"Verdict: {result.verdict}\nScore: {result.score}"

agent = create_react_agent(llm, tools=[ethics_evaluation])
```
</details>

<details>
<summary><b>Google ADK</b></summary>

```python
from google.adk.tools.mcp_toolset import McpToolset, StdioServerParameters

tools = McpToolset(
    connection_params=StdioServerParameters(
        command="uv", args=["run", "ethics-filter-mcp"]
    )
)
agent = Agent(model="gemini-2.5-pro", tools=[tools])
```
</details>

---

### 🐍 Python SDK

Import the engine directly into any Python project:

```python
from ethics_filter.engine import (
    determine_relevant_modules,   # check which modules apply
    get_module_content,           # read a module's criteria
    build_evaluation_prompt,      # build a structured LLM prompt
    list_available_modules,       # list all modules
)
```

No Hermes, no MCP, no agent framework required. Pure Python.

### ⚡ Prompt-Based (any LLM, any platform)

The module markdown files in [`modules/`](modules/) contain the complete evaluation criteria and scoring rubrics. Any LLM can evaluate a decision by reading the relevant modules and applying the methodology. No special software needed.

### 🧪 Standalone Test Runner

```bash
cd ethics-filter
uv run python tests/evaluate_v2.py     # Run all 52 test scenarios
uv run python tests/generate_report_v2.py  # Generate audit report
```

### 🧙 Hermes Agent

If you use [Hermes Agent](https://hermes-agent.nousresearch.com), see [`docs/hermes-integration.md`](docs/hermes-integration.md) for the native skill setup.

---

## How It Works

The Ethics Filter uses a **relevance engine** that scans the decision context for keywords to determine which of the 6 modules apply. The host LLM then evaluates each relevant module using the criteria in the corresponding markdown file, assigns scores (0-100), and produces an overall verdict.

The evaluation pipeline is:

1. **Action + Context** → You provide what's being decided and the background
2. **Relevance Check** → Engine determines which modules apply
3. **Module Scoring** → LLM scores each relevant module using its rubric
4. **Aggregation** → Scores are averaged and compared against strictness thresholds
5. **Verdict** → 🟢 GREEN / 🟡 AMBER / 🔴 RED

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

Full presets: [`constitution/templates.json`](constitution/templates.json)

## What Makes This Different

| Dimension | Existing Guardrails | This Skillset |
|-----------|-------------------|---------------|
| Focus | AI safety (hallucinations, PII) | **Holistic ethics** |
| Scope | LLM output safety | **Any decision** |
| Audience | Developers | **Everyone** |
| Source | Technical research | **B Corp, Markkula Center, Conscious Capitalism** |
| Modularity | One-size-fits-all | **Per-person constitution** |
| Integration | Single platform | **MCP, SDK, prompt-based** |

## Test Results

52 scenarios evaluated across 9 categories:

- **Score range**: 5.0 (price fixing) → 100.0 (returning lost wallet)
- **GREEN (80+)**: 23 — ethical decisions correctly recognized
- **AMBER (50-79)**: 14 — tensions flagged for human judgment
- **RED (0-49)**: 15 — unethical decisions correctly blocked

Full report: [`docs/audit-report.md`](docs/audit-report.md)

## Project Structure

```
ethics-filter/
├── LICENSE                  # MIT
├── README.md                # You are here
├── pyproject.toml           # Python package with MCP entry point
├── ethics_filter/
│   ├── __init__.py
│   ├── engine.py            # Core evaluation engine (framework-agnostic)
│   └── mcp_server.py        # MCP server (uses engine.py)
├── constitution/
│   └── templates.json       # 6 presets, 3 strictness levels
├── modules/
│   ├── environmental.md     # Full module criteria & rubric
│   ├── fairness.md
│   ├── transparency.md
│   ├── conscious-leadership.md
│   ├── ethical-framework.md
│   └── compliance.md
├── docs/
│   ├── audit-report.md      # 52-scenario evaluation results
│   ├── brief.md             # Original project brief
│   └── hermes-integration.md # Hermes Agent setup (reframed from SKILL.md)
└── tests/
    ├── scenarios_v2.json
    ├── evaluate_v2.py       # Test runner
    ├── generate_report_v2.py
    └── results_v2.json
```

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
