from agents.mcp import MCPServer


class MCPServers(list[MCPServer]):
    """
    Helperclass for the async with statement in agents.
    This class allows to define multiple MCP servers that
    will be started in the async with statement and then returns one
    iterable list that can be passed to the agent instead of
    defining a multitude and pass all one by one.
    """

    def __init__(self, *servers: MCPServer):
        super().__init__(servers)

    def __iter__(self):
        return super().__iter__()

    async def __aenter__(self) -> "MCPServers":
        for srv in self:
            await srv.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        for srv in reversed(self):
            await srv.cleanup()
