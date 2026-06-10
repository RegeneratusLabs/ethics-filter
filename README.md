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

The Ethics Filter can be used from **any AI platform** — pick your path below.

---

### 🐍 Hermes Agent (Native Skill)

If you use [Hermes Agent](https://hermes-agent.nousresearch.com), load the skill directly:

```bash
# Load the skill
skill_view(name="ethics-filter")

# Then evaluate any decision
"Run this through the ethics filter: [decision]. Use maximalist constitution at moderate strictness."
```

---

### 🔌 MCP Server (Universal — works with 15+ platforms)

The Ethics Filter exposes an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that any MCP-compatible host can connect to. One server, universal reach.

**MCP-compatible platforms:**

| Platform | How to Connect |
|----------|---------------|
| **Claude Desktop** | Add to `claude_desktop_config.json` → `mcpServers` |
| **Claude Code** | `claude mcp add ethics-filter -- uv run ethics-filter-mcp` |
| **Cursor** | Add to `~/.cursor/mcp.json` or `.cursor/mcp.json` (committable) |
| **GitHub Copilot** | VS Code settings → Copilot → MCP → Add server |
| **Cline / Roo Code** | MCP configuration UI or ask agent to add it |
| **Continue.dev** | Add YAML block to `.continue/mcpServers/` |
| **Aider** | Add `mcp-servers:` to `~/.aider.conf.yml` |
| **OpenAI Agents SDK** | `Agent(mcp_servers=[MCPServerStdio(...)])` |
| **ChatGPT** | Connect as an MCP App in Developer Mode |
| **CrewAI** | `Agent(mcps=["https://ethics-filter.example.com/mcp"])` |
| **AutoGPT** | MCP Tool Block → enter server URL |
| **Dify** | Tools → MCP → Add MCP Server (HTTP) |
| **n8n** | MCP Client node (v1.88+ native) |
| **Semantic Kernel** | `MCPStdioPlugin` or `MCPSsePlugin` |
| **Google ADK** | `Agent(tools=[McpToolset(...)])` |

#### Quick Start (MCP)

```bash
# Clone and install
git clone https://github.com/RegeneratusLabs/ethics-filter
cd ethics-filter
pip install -r requirements.txt

# Run the MCP server
uv run ethics-filter-mcp
```

Then point your MCP host at it. For example, in **Claude Code**:

```bash
claude mcp add ethics-filter -- uv run ethics-filter-mcp
```

Or in **Cursor**, add to `.cursor/mcp.json`:

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

---

### 📦 Python SDK

Import the evaluation engine directly into any Python project:

```bash
pip install ethics-filter
```

```python
from ethics_filter import evaluate

result = evaluate(
    decision="Should we switch to biodegradable packaging?",
    constitution="maximalist",
    strictness="moderate"
)

print(result.score)    # 87.5
print(result.verdict)  # GREEN
print(result.reasoning)  # Per-module breakdown
```

Works directly with:
- **OpenAI Agents SDK** — `@function_tool` decorator
- **LangChain / LangGraph** — `@tool` decorator
- **CrewAI** — `@tool` `BaseTool` subclass
- **Semantic Kernel** — `@kernel_function` decorator
- **AutoGPT** — Python agent plugin

---

### 🧪 Standalone Tool

```bash
# Clone and run test scenarios
git clone https://github.com/RegeneratusLabs/ethics-filter
cd ethics-filter

# Evaluate all 52 test scenarios
python3 tests/evaluate_v2.py

# Generate audit report
python3 tests/generate_report_v2.py
```

---

## Per-Platform Configuration Examples

### Claude Code (Plugin Mode)

Package as a `.claude-plugin/` directory with a bundled MCP server. Drop-in compatible since the Hermes SKILL.md format is nearly identical to Claude Code's skill format. Or use:

```bash
claude mcp add ethics-filter -- uv run ethics-filter-mcp
claude "Run this through the ethics filter: should I partner with this supplier?"
```

### Claude Desktop

Edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ethics-filter": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/ethics-filter", "ethics-filter-mcp"]
    }
  }
}
```

### Cursor

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

### OpenAI Agents SDK

```python
from agents import Agent, Runner, MCPServerStdio

async with MCPServerStdio(
    name="ethics-filter",
    params={"command": "uv", "args": ["run", "ethics-filter-mcp"]}
) as server:
    agent = Agent(
        name="Assistant",
        instructions="You have access to an ethics evaluation tool.",
        mcp_servers=[server]
    )
    result = await Runner.run(agent, "Run this through the ethics filter: launch a new product line")
```

### LangChain / LangGraph

```python
from langchain_core.tools import tool
from ethics_filter import evaluate

@tool
def ethics_evaluation(decision: str, constitution: str = "maximalist") -> str:
    """Evaluate a decision through 6 ethical modules (Environmental, Fairness, Transparency, Conscious Leadership, Ethical Framework, Compliance) and return GREEN/AMBER/RED with detailed reasoning."""
    result = evaluate(decision, constitution)
    return f"Verdict: {result.verdict}\nScore: {result.score}\nReasoning: {result.reasoning}"

# Use in any LangChain agent
from langchain.agents import create_react_agent, AgentExecutor
agent = create_react_agent(llm, tools=[ethics_evaluation])
```

### CrewAI

```python
from crewai import Agent
from crewai_tools import tool
from ethics_filter import evaluate

@tool("Ethics Evaluation")
def ethics_evaluation(decision: str) -> str:
    """Evaluate a decision through 6 ethical modules."""
    result = evaluate(decision)
    return f"{result.verdict}: {result.reasoning}"

ethics_officer = Agent(
    role="Ethics Officer",
    goal="Ensure all decisions pass ethical review",
    tools=[ethics_evaluation]
)
```

Or use MCP directly:

```python
ethics_officer = Agent(
    role="Ethics Officer",
    goal="Ensure all decisions pass ethical review",
    mcps=["https://ethics-filter.example.com/mcp"]
)
```

### Google ADK

```python
from google.adk.tools.mcp_toolset import McpToolset, StdioServerParameters

tools = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "ethics-filter-mcp"]
    )
)
agent = Agent(
    model="gemini-2.5-pro",
    tools=[tools]
)
```

---

## MCP Tools Exposed

Once connected, the Ethics Filter exposes these tools:

| Tool | Description |
|------|-------------|
| `evaluate_decision` | Run a decision through ethical modules and get GREEN/AMBER/RED verdict |
| `get_audit_trail` | Retrieve a permanent audit record for any past evaluation |
| `list_constitutions` | List available constitution presets |
| `get_constitution` | View the full configuration of a specific preset |

---

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
