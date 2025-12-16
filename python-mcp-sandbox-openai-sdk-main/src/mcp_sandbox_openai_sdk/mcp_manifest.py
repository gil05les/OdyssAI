from dataclasses import dataclass
from enum import Enum
from typing import Any


class Permission(str, Enum):
    """
    List of all possible permissions that can be requested by an MCP.
    This list is not exhaustive and may be extended in the future.
    The permissions in the manifest are creating an overall hint of what
    an MCP might do. The actual enforcement of these permissions
    is done by the sandbox environment and its (specific) configuration.
    """

    MCP_AC_FILESYSTEM_READ = "mcp.ac.filesystem.read"
    MCP_AC_FILESYSTEM_WRITE = "mcp.ac.filesystem.write"
    MCP_AC_FILESYSTEM_DELETE = "mcp.ac.filesystem.delete"
    MCP_AC_SYSTEM_ENV_READ = "mcp.ac.system.env.read"
    MCP_AC_SYSTEM_ENV_WRITE = "mcp.ac.system.env.write"
    MCP_AC_SYSTEM_EXEC = "mcp.ac.system.exec"
    MCP_AC_SYSTEM_PROCESS = "mcp.ac.system.process"
    MCP_AC_NETWORK_CLIENT = "mcp.ac.network.client"
    MCP_AC_NETWORK_SERVER = "mcp.ac.network.server"
    MCP_AC_NETWORK_BLUETOOTH = "mcp.ac.network.bluetooth"
    MCP_AC_PERIPHERAL_CAMERA = "mcp.ac.peripheral.camera"
    MCP_AC_PERIPHERAL_MICROPHONE = "mcp.ac.peripheral.microphone"
    MCP_AC_PERIPHERAL_SPEAKER = "mcp.ac.peripheral.speaker"
    MCP_AC_PERIPHERAL_SCREEN_CAPTURE = "mcp.ac.peripheral.screen.capture"
    MCP_AC_LOCATION = "mcp.ac.location"
    MCP_AC_NOTIFICATIONS_POST = "mcp.ac.notifications.post"
    MCP_AC_CLIPBOARD_READ = "mcp.ac.clipboard.read"
    MCP_AC_CLIPBOARD_WRITE = "mcp.ac.clipboard.write"


class Registry(str, Enum):
    NPM = "npm"
    PYPI = "pypi"


@dataclass
class MCPManifest:
    """
    Security manifest for an MCP Server (Model Context Protocol).
    Contains relevant metadata about the MCP server and its requested permissions.

    The effective permissions will be defined by the execution and the user's consent.
    """

    name: str
    description: str
    registry: Registry
    package_name: str
    permissions: list[Permission]

    @staticmethod
    def from_file(path: str) -> "MCPManifest":
        """
        Create an MCPManifest from a JSON file.
        """
        import json

        with open(path, "r") as f:
            data = json.load(f)
        return MCPManifest.from_json(data)

    @staticmethod
    def from_json(data: dict[str, Any]) -> "MCPManifest":
        """
        Create an MCPManifest from a JSON dictionary.
        """
        return MCPManifest(
            name=data["name"],
            description=data["description"],
            registry=Registry(data["registry"]),
            package_name=data["package_name"],
            permissions=[Permission(p) for p in data.get("permissions", [])],
        )


@dataclass
class DevMCPManifest(MCPManifest):
    """
    Special version of the MCP Manifest for local development.
    Mounts local code into the sandbox container.

    Args:
        code_mount: Path to mount as /sandbox in the container
        exec_command: Command to run the MCP server
        preinstalled: If True, skip package installation (assumes deps are in mounted dir).
                      If False (default), install the package_name before running.
    """

    code_mount: str
    exec_command: str
    preinstalled: bool = False
