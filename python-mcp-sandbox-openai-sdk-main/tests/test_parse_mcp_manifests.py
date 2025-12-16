from mcp_sandbox_openai_sdk import MCPManifest, Permission, Registry


def test_parse_mcp_manifest():
    manifest = MCPManifest.from_json(
        {
            "name": "example-mcp",
            "description": "An example MCP manifest",
            "registry": "pypi",
            "package_name": "example-package",
            "permissions": ["mcp.ac.filesystem.read", "mcp.ac.network.client"],
        }
    )
    assert manifest.name == "example-mcp"
    assert manifest.description == "An example MCP manifest"
    assert manifest.registry == Registry.PYPI
    assert manifest.package_name == "example-package"
    assert Permission.MCP_AC_FILESYSTEM_READ in manifest.permissions
    assert Permission.MCP_AC_NETWORK_CLIENT in manifest.permissions


def test_parse_mcp_manifest_from_file():
    import tempfile

    with tempfile.NamedTemporaryFile("w+") as tmpfile:
        tmpfile.write(
            """{
            "name": "example-mcp",
            "description": "An example MCP manifest",
            "registry": "pypi",
            "package_name": "example-package",
            "permissions": ["mcp.ac.filesystem.read", "mcp.ac.network.client"]
        }"""
        )
        tmpfile.flush()
        manifest = MCPManifest.from_file(tmpfile.name)
        assert manifest.name == "example-mcp"
        assert manifest.description == "An example MCP manifest"
        assert manifest.registry == Registry.PYPI
        assert manifest.package_name == "example-package"
        assert Permission.MCP_AC_FILESYSTEM_READ in manifest.permissions
        assert Permission.MCP_AC_NETWORK_CLIENT in manifest.permissions
