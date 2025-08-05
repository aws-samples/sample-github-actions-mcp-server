# GitHub Actions MCP Server

A Model Context Protocol (MCP) server for interacting with GitHub Actions workflows, secrets, environments, and more.

## Overview

The GitHub Actions MCP Server provides tools to help AI assistants interact with GitHub Actions workflows. It enables:

- Listing, viewing, and managing GitHub Actions workflows
- Validating workflow YAML syntax
- Getting workflow run history and status
- Managing GitHub Actions secrets and environments
- Generating workflow templates for common use cases

## Installation

### Prerequisites

- Python 3.10 or higher
- GitHub Personal Access Token with appropriate permissions
- MCP-compatible client (Amazon Q Developer CLI, Cursor, Cline, etc.)

### Install with uv

```bash
uv pip install awslabs.github-actions-mcp-server
```

### Install from source

```bash
git clone https://github.com/awslabs/mcp.git
cd mcp/src/github-actions-mcp-server
pip install -e .
```

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub Personal Access Token (required if not provided in tool calls)

### MCP Client Configuration

Add the following to your MCP client configuration file:

```json
{
  "mcpServers": {
    "awslabs.github-actions-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.github-actions-mcp-server@latest"],
      "env": {
        "GITHUB_TOKEN": "your-github-token",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

## Usage

### Available Tools

- `listWorkflows`: List GitHub Actions workflows in a repository
- `getWorkflow`: Get details and content of a specific workflow
- `listWorkflowRuns`: List workflow run history
- `createOrUpdateWorkflow`: Create or update a workflow file
- `listSecrets`: List GitHub Actions secrets (names only, not values)
- `listEnvironments`: List GitHub Actions environments
- `validateWorkflow`: Validate workflow YAML content
- `getWorkflowTemplates`: Get common workflow templates

### Example Prompts

- "List all GitHub Actions workflows in my repository"
- "Show me the details of my CI workflow"
- "Create a new workflow for deploying to AWS"
- "Validate this GitHub Actions workflow YAML"
- "Show me recent workflow runs for my repository"
- "Generate a Python package workflow template"

## Security

This MCP server requires a GitHub Personal Access Token to interact with GitHub repositories. For security:

- Use tokens with the minimum required permissions
- Store tokens securely (environment variables or secrets management)
- Never commit tokens to version control
- For repository secrets, only names are exposed (not values)

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/awslabs/mcp.git
cd mcp/src/github-actions-mcp-server

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## License

This project is licensed under the Apache-2.0 License.

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for details on how to contribute to this project.
