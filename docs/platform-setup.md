# Platform Setup Guide

The Ethics Filter MCP server works with any MCP-compatible host. Here's how to connect it to each platform.

## Prerequisites

```bash
git clone https://github.com/RegeneratusLabs/ethics-filter
cd ethics-filter
uv sync
```

The MCP server entry point is: `uv run ethics-filter-mcp`

---

## Claude Code

```bash
claude mcp add ethics-filter -- uv run ethics-filter-mcp
```

## Claude Desktop

Add to `claude_desktop_config.json` (Settings → Developer → Edit Config):

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

## Cursor

Add to `.cursor/mcp.json` (project-level, committable):

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

## GitHub Copilot

VS Code → Settings → Copilot → MCP → Add server:

| Field | Value |
|-------|-------|
| Name | `ethics-filter` |
| Type | `stdio` |
| Command | `uv run ethics-filter-mcp` |
| Directory | `/path/to/ethics-filter` |

## Cline / Roo Code

In the MCP configuration UI, add a new server:

| Field | Value |
|-------|-------|
| Name | `ethics-filter` |
| Command | `uv run ethics-filter-mcp` |
| Path | `/path/to/ethics-filter` |

## Continue.dev

Add a YAML file in `.continue/mcpServers/ethics-filter.yaml`:

```yaml
command: uv
args: ["run", "ethics-filter-mcp"]
cwd: /path/to/ethics-filter
```

## Aider

Add to `~/.aider.conf.yml`:

```yaml
mcp-servers:
  ethics-filter:
    command: uv
    args: ["run", "ethics-filter-mcp"]
```

## OpenAI Agents SDK

```python
from agents import Agent, Runner, MCPServerStdio

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

## ChatGPT (MCP App)

ChatGPT supports connecting remote MCP servers as Apps. If you deploy the Ethics Filter server to a public URL, connect it via Developer Mode → MCP Apps.

## CrewAI

```python
from crewai import Agent

ethics_officer = Agent(
    role="Ethics Officer",
    goal="Ensure all decisions pass ethical review",
    mcps=["https://ethics-filter.example.com/mcp"]
)
```

## LangChain / LangGraph

Using the Python SDK directly (no MCP dependency):

```python
from langchain_core.tools import tool
from ethics_filter.engine import build_evaluation_prompt

@tool
def ethics_evaluation(decision: str, constitution: str = "maximalist") -> str:
    """Evaluate a decision through 6 ethical modules and return a structured verdict."""
    prompt = build_evaluation_prompt(decision, constitution=constitution)
    return prompt["prompt"]

agent = create_react_agent(llm, tools=[ethics_evaluation])
```

## Semantic Kernel (Python)

Using the MCP plugin:

```python
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.mcp import MCPStdioPlugin

kernel = Kernel()
async with MCPStdioPlugin(
    name="ethics",
    command="uv",
    args=["run", "ethics-filter-mcp"]
) as plugin:
    kernel.add_plugin(plugin)
```

## Google Agent Development Kit (ADK)

```python
from google.adk.tools.mcp_toolset import McpToolset, StdioServerParameters

tools = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "ethics-filter-mcp"]
    )
)
agent = Agent(model="gemini-2.5-pro", tools=[tools])
```

## AutoGPT

Use the MCP Tool Block in the AutoGPT builder:
1. Add an MCP Tool Block node
2. Enter the server URL
3. Browse available tools
4. Select the ones you need

## Dify

Dify v1.6.0+ supports MCP:
1. Go to Tools → MCP → Add MCP Server
2. Enter the server URL (HTTP transport)
3. Tools are auto-discovered

## n8n

n8n v1.88+ has native MCP Client nodes:
1. Add an MCP Client node to your workflow
2. Configure the connection to the Ethics Filter server
3. The AI Agent node will auto-select MCP tools
