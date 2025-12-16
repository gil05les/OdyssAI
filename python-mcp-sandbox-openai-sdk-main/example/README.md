# Example Sandbox Agent

The example in `main.py` shows how the sandbox can be utilized to
encapsulate any MCP server (NPM or Python based) without changing the
code of the original MPC servers.

To run this example, keep in mind to fetch an OpenAI API key since it
directly works with GPT-5.

The utilized openAI Agent SDK also allows employing other LLMs.

## Run

To run the example, simply execute:

```bash
export OPENAI_API_KEY="sk-..."
uv run main.py
```

Of course, you can also run this in any Python environment of your choice,
`uv` is just an example.
