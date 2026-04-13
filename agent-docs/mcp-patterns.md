---
title: "Mcp Patterns"
description: |
  Patterns for building, securing, and consuming MCP (Model Context Protocol) servers. Covers schema-first design, authentication, input validation, audit logging, and security best practices.
when: |
  Patterns for building, securing, and consuming MCP (Model Context Protocol) servers. Covers schema-first design, authentication, input validation, audit logging, and security best practices.
---

---

# MCP Server Patterns

Best practices for building and consuming MCP servers — the protocol that lets AI tools interact with external systems.

## When to Activate

- Building a new MCP server
- Configuring MCP servers in `.mcp.json`
- Reviewing MCP tool definitions
- Adding authentication or security to MCP servers
- Debugging MCP tool calls

## Core MCP Concepts

| Component | Purpose | Example |
|-----------|---------|---------|
| **Tools** | Callable actions (read/write) | "query_jira", "create_issue", "run_analysis" |
| **Resources** | Read-only data endpoints | Dataset schemas, model metadata, config values |
| **Prompts** | Reusable prompt templates | "Analyze this dataset", "Summarize this epic" |
| **Transport** | Communication channel | stdio (local), Streamable HTTP (remote) |

## Schema-First Tool Design

Always define input schemas with validation — never accept raw unvalidated input:

```python
# Python MCP server example
from mcp.server import Server
from pydantic import BaseModel, Field

class QueryInput(BaseModel):
    dataset: str = Field(description="Dataset identifier")
    filters: dict[str, str] = Field(default_factory=dict)
    limit: int = Field(default=100, le=10000, description="Max rows to return")

@server.tool("query_data", "Query a dataset with filters")
async def query_data(input: QueryInput):
    # Input is already validated by Pydantic
    results = db.query(input.dataset, input.filters, input.limit)
    return {"rows": len(results), "data": results}
```

### Tool Design Principles

- **One tool, one job** — don't combine read and write in one tool
- **Descriptive names** — `query_jira_issues` not `do_jira`
- **Document parameters** — every field needs a description
- **Set limits** — max results, max file size, allowed values
- **Return structured data** — JSON with consistent schema, not free text

## Security Patterns

### Authentication

```python
# Use principal-based auth (user's credentials, not server's)
# BAD: Server uses its own service account
headers = {"Authorization": f"Bearer {SERVER_TOKEN}"}

# GOOD: Server uses the calling user's credentials
headers = {"Authorization": f"Bearer {user_context.token}"}
```

### Input Validation

```python
# Validate and sanitize all inputs before use
import re

def validate_jira_key(key: str) -> str:
    """Only allow valid Jira key format."""
    if not re.match(r'^[A-Z][A-Z0-9]+-\d+$', key):
        raise ValueError(f"Invalid Jira key format: {key}")
    return key

# Never pass raw user input to shell commands
# BAD:
os.system(f"grep {user_input} data.json")
# GOOD:
subprocess.run(["grep", user_input, "data.json"], capture_output=True)
```

### User Approval for Risky Operations

```python
# Require confirmation for destructive or sensitive actions
RISKY_OPERATIONS = {"delete", "bulk_update", "export_pii", "drop_table"}

@server.tool("delete_record")
async def delete_record(record_id: str):
    # MCP framework handles approval — tool description should state:
    # "This tool deletes data permanently. Requires user confirmation."
    pass
```

### Audit Logging

```python
import logging

@server.tool("query_data")
async def query_data(input: QueryInput, context: RequestContext):
    logging.info(
        "MCP tool call",
        extra={
            "tool": "query_data",
            "user": context.user_id,
            "params": {"dataset": input.dataset, "limit": input.limit},
            "timestamp": datetime.now().isoformat(),
        }
    )
    # ... execute query
```

## Configuration (.mcp.json)

```json
{
  "mcpServers": {
    "jira": {
      "command": "uvx",
      "args": ["mcp-jira"],
      "env": {
        "JIRA_URL": "https://your-instance.atlassian.net",
        "JIRA_TOKEN": "${JIRA_TOKEN}"
      }
    },
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_TOKEN}",
        "GITLAB_API_URL": "https://gitlab.example.com"
      }
    }
  }
}
```

### Configuration Security

- **Never hardcode tokens** in `.mcp.json` — use `${ENV_VAR}` references
- **Add `.mcp.json` to `.gitignore`** if it contains environment-specific values
- **Use `.mcp.json.example`** with placeholder values for team distribution

## Transport Selection

| Transport | Best For | Setup |
|-----------|---------|-------|
| **stdio** | Local development, Claude Desktop, single user | Simplest — just run the server as a subprocess |
| **Streamable HTTP** | Remote teams, Cursor, cloud deployment, multiple clients | Single HTTP endpoint, supports auth headers |

## Common MCP Patterns for Data Science

### Data Source MCP

Expose datasets and queries as MCP tools:
- `list_datasets` — returns available datasets
- `query_dataset` — run filtered queries with limits
- `get_schema` — return column names, types, sample values
- `get_stats` — return row counts, null rates, distributions

### Model MCP

Expose ML models as MCP tools:
- `list_models` — available models and versions
- `predict` — run inference with input validation
- `get_model_info` — architecture, training date, metrics
- `compare_models` — side-by-side performance comparison

## Anti-Patterns to Avoid

| Anti-Pattern | Risk | Fix |
|-------------|------|-----|
| Server using its own credentials | Privilege escalation | Use principal-based auth (user's token) |
| No input validation | Injection attacks | Validate with Pydantic schemas |
| No audit logging | No accountability | Log every tool call with user + params |
| Hardcoded secrets in config | Credential exposure | Use environment variable references |
| Overly broad tool permissions | Excessive agency | Scope tools narrowly, require approval for writes |
| Returning raw error tracebacks | Information leakage | Return structured error messages |
