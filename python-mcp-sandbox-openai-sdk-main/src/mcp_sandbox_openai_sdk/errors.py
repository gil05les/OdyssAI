from .mcp_manifest import Permission
from .runtime_permissions import RuntimePermission


class InvalidRuntimePermission(Exception):
    def __init__(
        self,
        manifest_permissions: list[Permission],
        illegal_runtime_permissions: list[RuntimePermission],
    ):
        super().__init__(
            f"Illegal runtime permissions detected: {illegal_runtime_permissions}\nDeclared manifest permissions: {manifest_permissions}"
        )
