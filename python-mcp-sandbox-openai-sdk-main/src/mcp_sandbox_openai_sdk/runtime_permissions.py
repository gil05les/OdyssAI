import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import Final, Union

from .mcp_manifest import Permission


def _is_auto_consent_enabled() -> bool:
    """Check if auto-consent mode is enabled via environment variable."""
    return os.getenv("MCP_AUTO_CONSENT", "").lower() in ("true", "1", "yes")


class _Verifyable(ABC):
    """
    Interface for runtime permissions that can be verified against the manifest permissions.
    """

    @abstractmethod
    def validate_with_manifest_perms(
        self, manifest_permissions: list[Permission]
    ) -> bool:
        """
        Validate the permission against the manifest permissions.
        Returns True if the permission is valid, False otherwise.

        Example:
        If the list of manifest permissions does not contain MCP_AC_FILESYSTEM_WRITE,
        then a FSAccess permission with write=True is invalid.
        """
        raise NotImplementedError


class _Consentable(ABC):
    """
    Interface for consentable runtime permissions that require user approval.
    """

    def ask_user(self, title: str, description: str) -> bool:
        """
        Ask the user for consent to grant the permission.
        If MCP_AUTO_CONSENT environment variable is set, auto-approve all permissions.
        """
        # Check for auto-consent mode (useful for non-interactive environments like Docker)
        if _is_auto_consent_enabled():
            print(f"Runtime Permission (auto-consented): {title}")
            print(description)
            return True

        print(f"Runtime Permission: {title}")
        print(description)
        while True:
            user_input = (
                input("Do you want to give the agent the requested access? (yes/no): ")
                .strip()
                .lower()
            )
            if user_input in ["yes", "y"]:
                return True
            elif user_input in ["no", "n"]:
                return False
            else:
                print("Invalid input. Please enter 'yes' (y) or 'no' (n).")

    @abstractmethod
    def get_user_consent(self) -> bool:
        """
        Get user consent for the permission.
        """
        raise NotImplementedError


@dataclass
class FSAccess(_Verifyable, _Consentable):
    path: str
    container_path: str | None = None
    read: bool = True
    write: bool = False
    type: Final[str] = "filesystem"

    def validate_with_manifest_perms(
        self, manifest_permissions: list[Permission]
    ) -> bool:
        if self.read and Permission.MCP_AC_FILESYSTEM_READ not in manifest_permissions:
            return False
        if (
            self.write
            and Permission.MCP_AC_FILESYSTEM_WRITE not in manifest_permissions
        ):
            return False
        return True

    def get_user_consent(self) -> bool:
        return self.ask_user(
            "File System Access Permission",
            f"Allow access to file system path: {self.path} (read: {self.read}, write: {self.write})",
        )


@dataclass
class EnvironmentVariable(_Verifyable, _Consentable):
    name: str
    type: Final[str] = "env_var"

    def validate_with_manifest_perms(
        self, manifest_permissions: list[Permission]
    ) -> bool:
        # Checks for env read/write permissions
        if Permission.MCP_AC_SYSTEM_ENV_READ not in manifest_permissions:
            return False
        return True

    def get_user_consent(self) -> bool:
        return self.ask_user(
            "Environment Variable Access Permission",
            f"Allow (read) access to environment variable: {self.name}",
        )


@dataclass
class DomainPort(_Verifyable, _Consentable):
    domain: str
    port: int
    type: Final[str] = "egress_domain_port"

    def validate_with_manifest_perms(
        self, manifest_permissions: list[Permission]
    ) -> bool:
        if Permission.MCP_AC_NETWORK_CLIENT not in manifest_permissions:
            return False
        return True

    def get_user_consent(self) -> bool:
        return self.ask_user(
            "Network Access Permission",
            f"Allow access to network domain: {self.domain} (port: {self.port})",
        )


@dataclass
class HostPort(_Verifyable, _Consentable):
    host: IPv4Address
    port: int
    type: Final[str] = "egress_host_port"

    def validate_with_manifest_perms(
        self, manifest_permissions: list[Permission]
    ) -> bool:
        if Permission.MCP_AC_NETWORK_CLIENT not in manifest_permissions:
            return False
        return True

    def get_user_consent(self) -> bool:
        return self.ask_user(
            "Network Access Permission",
            f"Allow access to network host: {self.host} (port: {self.port})",
        )


Egress = Union[DomainPort, HostPort]

RuntimePermission = Union[FSAccess, Egress, EnvironmentVariable]
