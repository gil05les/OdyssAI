# MCP Sandbox SDK for Python OpenAI Agent SDK

This package provides an SDK to use the MCP sandbox in the python language
in conjunction with the OpenAI Agent SDK (https://openai.github.io/openai-agents-python/).

The agent SDK allows you to write agentic AI apps and interact with LLMs
in an easy way. The OpenAI SDK is not limited to ChatGPT, you may use other LLMs
in the background.

This package allows you, to use the MCP protocol in a safe and encapsulated way.
Instead of spawning and running any arbitrary MCP server locally, the MCP process
is encapsulated inside a Docker container. Thus, as the engineer of the agent,
you further must define which effective parts of the local environment you want to access.

This results in a question about the effective runtime permission to the user to
get the consent of the user.

This allows you to create trustworthy agents that interact with the local system in a
least privilege manner.

## Prerequisites

- Python 3.10+
- Docker installed and running
- Optionally: An OpenAI API key
- Recommended: the UV package manager for Python

## Example

This example assumes you use `uv`.
Find the example code in the [`example`](./example/) folder with a readme on
how to run the example agent.

## Usage

To use the package locally:

```bash
uv init
uv add https://github.com/GuardiAgent/python-mcp-sandbox-openai-sdk.git
```

This adds the package to your local environment.
