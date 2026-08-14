# Platform Setup Guide

The Ethics Filter MCP server works with any MCP-compatible host. The server entry point is `ethics-filter-mcp`, run via `uv run ethics-filter-mcp` with stdio as the default transport. This guide shows how to connect it to each platform.

## Prerequisites

```bash
git clone https://github.com/RegeneratusLabs/ethics-filter
cd ethics-filter
uv sync
```

The MCP server entry point is: `uv run ethics-filter-mcp` (stdio is the default transport; use `--transport sse` or `--transport http` for remote deployment).

All examples below use `/path/to/ethics-filter` as the repo location — replace it with the path of your clone. Commands use `uv run --directory /path/to/ethics-filter ethics-filter-mcp` so they work from any directory; plain `uv run ethics-filter-mcp` works from inside the repo root.

---

## Claude Code

```bash
claude mcp add ethics-filter -- uv run --directory /path/to/ethics-filter ethics-filter-mcp
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
| Command | `uv run --directory /path/to/ethics-filter ethics-filter-mcp` |
| Directory | `/path/to/ethics-filter` |

## Cline / Roo Code

In the MCP configuration UI, add a new server:

| Field | Value |
|-------|-------|
| Name | `ethics-filter` |
| Command | `uv run --directory /path/to/ethics-filter ethics-filter-mcp` |
| Path | `/path/to/ethics-filter` |

## Continue.dev

Add a YAML file in `.continue/mcpServers/ethics-filter.yaml`:

```yaml
command: uv
args: ["run", "--directory", "/path/to/ethics-filter", "ethics-filter-mcp"]
cwd: /path/to/ethics-filter
```

## Aider

Add to `~/.aider.conf.yml`:

```yaml
mcp-servers:
  ethics-filter:
    command: uv
    args: ["run", "--directory", "/path/to/ethics-filter", "ethics-filter-mcp"]
```

## OpenAI Agents SDK

```python
from agents import Agent, Runner, MCPServerStdio

async with MCPServerStdio(
    name="ethics-filter",
    params={"command": "uv", "args": ["run", "--directory", "/path/to/ethics-filter", "ethics-filter-mcp"]}
) as server:
    agent = Agent(
        name="Assistant",
        instructions="You can evaluate decisions through the ethics filter.",
        mcp_servers=[server]
    )
    result = await Runner.run(agent, "Run this through the ethics filter: launch a new product line")
```

## ChatGPT (MCP app / remote hosting)

The ChatGPT MCP app connects to a remote server, so a locally spawned stdio process will not work. Deploy the Ethics Filter server with SSE or HTTP transport instead:

```bash
# Run from the repo root, or use: uv run --directory /path/to/ethics-filter ethics-filter-mcp --transport <sse|http>
uv run ethics-filter-mcp --transport sse
uv run ethics-filter-mcp --transport http
```

Then register the deployed server's URL in ChatGPT (Developer Mode → MCP Apps). The server must be reachable over the network from ChatGPT's environment.

## CrewAI

CrewAI can consume the Ethics Filter through the Python SDK directly (see the LangChain/LangGraph section for the SDK pattern), or point at an MCP server URL once a remote instance is deployed (`uv run --directory /path/to/ethics-filter ethics-filter-mcp --transport http`). Use the URL of your own deployed instance — there are no public hosted URLs.

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
    args=["run", "--directory", "/path/to/ethics-filter", "ethics-filter-mcp"]
) as plugin:
    kernel.add_plugin(plugin)
```

## Google Agent Development Kit (ADK)

```python
from google.adk.tools.mcp_toolset import McpToolset, StdioServerParameters

tools = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "--directory", "/path/to/ethics-filter", "ethics-filter-mcp"]
    )
)
agent = Agent(model="gemini-2.5-pro", tools=[tools])
```

## AutoGPT

Use the MCP Tool Block in the AutoGPT builder. The block connects to a remote MCP server URL, so the server must be deployed with HTTP transport and reachable over the network:

1. Add an MCP Tool Block node
2. Enter the server URL (e.g. the URL of a server started with `uv run --directory /path/to/ethics-filter ethics-filter-mcp --transport http`)
3. Browse available tools
4. Select the ones you need

## Dify

Dify v1.6.0+ supports MCP:
1. Go to Tools → MCP → Add MCP Server
2. Enter the server URL (HTTP transport). The server must be deployed with `uv run --directory /path/to/ethics-filter ethics-filter-mcp --transport http` and be reachable over the network from Dify.
3. Tools are auto-discovered

## n8n

n8n v1.88+ has native MCP Client nodes:
1. Add an MCP Client node to your workflow
2. Configure the connection to the Ethics Filter server — the server must be deployed with HTTP or SSE transport and be reachable over the network from n8n
3. The AI Agent node will auto-select MCP tools
