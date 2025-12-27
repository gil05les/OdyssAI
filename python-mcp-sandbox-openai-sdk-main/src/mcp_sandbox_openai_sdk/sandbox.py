import os
import platform

from agents.mcp import MCPServerStdio

from ._utils import _id_generator
from .errors import InvalidRuntimePermission
from .mcp_manifest import DevMCPManifest, MCPManifest
from .runtime_permissions import (
    DomainPort,
    EnvironmentVariable,
    FSAccess,
    HostPort,
    RuntimePermission,
)

_sandbox_version = "latest"


def set_sandbox_version(version: str) -> None:
    """
    Set a specific version for the sandbox docker image.
    Defaults to "latest".
    """
    global _sandbox_version
    _sandbox_version = version


class SandboxedMCPStdio(MCPServerStdio):
    def __init__(
        self,
        manifest: MCPManifest,
        name: str | None = None,
        runtime_args: list[str] | None = None,
        runtime_permissions: list[RuntimePermission] = [],
        static_environment_vars: dict[str, str] = {},
        client_session_timeout_seconds: int = 60,
        remove_container_after_run: bool = True,
    ):
        # Check the permissions in the manifest against the runtime permissions.
        # If some are off, throw an error.
        illegal = [
            p
            for p in runtime_permissions
            if not p.validate_with_manifest_perms(manifest.permissions)
        ]
        if illegal:
            raise InvalidRuntimePermission(manifest.permissions, illegal)

        # Then, for each runtime permission, ask the user via input, if the permission is allowed or not.
        # Only attach the permissions that the user gave the consent to.
        consented_perms = [p for p in runtime_permissions if p.get_user_consent()]

        allowed_egress = ",".join(
            [
                f"{p.domain}:{p.port}"
                for p in consented_perms
                if isinstance(p, DomainPort)
            ]
            + [f"{p.host}:{p.port}" for p in consented_perms if isinstance(p, HostPort)]
        )

        add_args = []
        if isinstance(manifest, DevMCPManifest):
            code_mount = manifest.code_mount
            add_args.extend(
                [
                    "-v",
                    f"{code_mount}:/sandbox",
                    "-e",
                    f"EXE={manifest.exec_command}",
                ]
            )
            # Only skip package installation if preinstalled=True
            if manifest.preinstalled:
                add_args.extend(["-e", "PRE_INSTALLED=true"])

        # Detect platform for Apple Silicon (ARM64) support
        # Docker Desktop on Mac with Apple Silicon can run both ARM64 and AMD64 via emulation
        # Allow override via environment variable, otherwise auto-detect
        # Note: GuardiAgent sandbox images may only support AMD64, so we use AMD64 with emulation on ARM64
        platform_flag = []
        docker_platform = os.getenv("DOCKER_PLATFORM")
        if docker_platform:
            platform_flag = ["--platform", docker_platform]
        else:
            machine = platform.machine().lower()
            if machine in ('arm64', 'aarch64'):
                # On Apple Silicon, use AMD64 with emulation (sandbox images may not support ARM64)
                # This avoids platform mismatch warnings and ensures compatibility
                platform_flag = ["--platform", "linux/amd64"]
            elif machine in ('x86_64', 'amd64'):
                platform_flag = ["--platform", "linux/amd64"]

        # Extract network-related flags from runtime_args and place them before the image
        # Docker requires --network to come before the image name
        network_flags = []
        remaining_runtime_args = []
        if runtime_args:
            i = 0
            while i < len(runtime_args):
                if runtime_args[i] == "--network" and i + 1 < len(runtime_args):
                    network_flags.extend(["--network", runtime_args[i + 1]])
                    i += 2
                elif isinstance(runtime_args[i], str) and runtime_args[i].startswith("--network="):
                    network_flags.append(runtime_args[i])
                    i += 1
                else:
                    remaining_runtime_args.append(runtime_args[i])
                    i += 1

        args = [
            "run",
            *(["--rm"] if remove_container_after_run else []),
            *platform_flag,
            "-i",
            "--cap-add=NET_ADMIN",
            "-e",
            f"PACKAGE={manifest.package_name}",
            *sum(
                [
                    [
                        "-v",
                        f"{fs.path}:{fs.container_path or fs.path}" + ("" if fs.write else ":ro"),
                    ]
                    for fs in consented_perms or []
                    if isinstance(fs, FSAccess)
                ],
                [],
            ),
            *(["-e", f"ALLOWED_EGRESS={allowed_egress}"] if allowed_egress else []),
            *sum(
                [
                    ["-e", f"{p.name}={os.environ.get(p.name)}"]
                    for p in consented_perms or []
                    if isinstance(p, EnvironmentVariable)
                ],
                [],
            ),
            *sum(
                [["-e", f"{k}={v}"] for k, v in static_environment_vars.items()],
                [],
            ),
            *add_args,
            *network_flags,  # Network flags must come BEFORE the image name
            f"ghcr.io/guardiagent/mcp-sandbox-{manifest.registry.value}:{_sandbox_version}",
            *remaining_runtime_args,  # Remaining args come AFTER the image name
        ]

        # Debug: print the full docker command
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Docker command: docker {' '.join(repr(a) for a in args)}")

        super().__init__(
            name=name or f"{manifest.name} - {_id_generator()}",
            params={
                "command": "docker",
                "args": args,
            },
            client_session_timeout_seconds=client_session_timeout_seconds,
        )
