#!/usr/bin/env python3
"""Prepare docker-compose for running multiple instances without conflicts.

Converts ports to environment variables with fallbacks,
removes container names and explicit networks.
Generates environment variables and appends them to .env file.
Saves output to a new file without modifying the original.
"""

import argparse
import glob
import hashlib
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def transform_volumes(
    data: dict[str, Any],
    volumes_option: str = "keep",
) -> tuple[dict[str, Any], dict[str, str]]:
    services = data.get("services", {})
    volume_env_vars = {}

    # Handle volumes based on option
    if volumes_option == "remove":
        # Remove all volumes to make ephemeral
        for service_config in services.values():
            if "volumes" in service_config:
                del service_config["volumes"]
        # Also remove top-level volumes section
        data.pop("volumes", None)

    elif volumes_option == "convert-to-named":
        named_volumes = {}
        for service_name, service_config in services.items():
            if "volumes" not in service_config:
                continue
            new_volumes = []
            bind_mount_count = 0
            for vol in service_config["volumes"]:
                if isinstance(vol, str) and ":" in vol and vol[0] in "./":
                    vol_hash = hashlib.sha256(
                        f"{service_name}:{vol}".encode(),
                    ).hexdigest()[:8]
                    default_vol_name = f"{service_name}-{vol_hash}"

                    # Count bind mounts for this service to determine naming
                    total_bind_mounts = sum(
                        1
                        for v in service_config["volumes"]
                        if isinstance(v, str) and ":" in v and v[0] in "./"
                    )

                    # Create environment variable name
                    if total_bind_mounts == 1:
                        env_var_name = f"{service_name.upper()}_VOLUME"
                    else:
                        env_var_name = (
                            f"{service_name.upper()}_VOLUME_{bind_mount_count}"
                        )
                        bind_mount_count += 1

                    # Add to volume environment variables
                    volume_env_vars[env_var_name] = default_vol_name

                    # Use environment variable with fallback
                    vol_name_with_fallback = f"${{{env_var_name}:-{default_vol_name}}}"
                    new_volumes.append(
                        f"{vol_name_with_fallback}:{':'.join(vol.split(':')[1:])}",
                    )
                    named_volumes[default_vol_name] = None
                else:
                    new_volumes.append(vol)
            service_config["volumes"] = new_volumes
        if named_volumes:
            data.setdefault("volumes", {}).update(named_volumes)
    elif volumes_option == "keep":
        pass
    else:
        msg = f"Invalid volumes option: {volumes_option}"
        raise ValueError(msg)
    return data, volume_env_vars


def make_multi_instance_safe(
    data: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Transform compose data to allow multiple instances without conflicts.

    Args:
        data: Parsed docker-compose data

    Returns:
        Tuple of (modified compose data, environment variables dict)

    """
    services = data.get("services", {})
    env_vars = {}

    # Convert ports to environment variables with fallbacks
    for service_name, service_config in services.items():
        if "ports" in service_config:
            ports = service_config["ports"]
            new_ports = []
            for i, port in enumerate(ports):
                # Extract container port from "host:container" or "port"
                container_port = (
                    str(port).split(":")[-1] if isinstance(port, str) else str(port)
                )

                # Create environment variable name
                if len(ports) == 1:
                    env_var_name = f"{service_name.upper()}_PORT"
                else:
                    env_var_name = f"{service_name.upper()}_PORT_{i}"

                # Add to environment variables with default value
                env_vars[env_var_name] = container_port

                # Transform port to use environment variable with fallback
                new_ports.append(
                    f"${{{env_var_name}:-{container_port}}}:{container_port}",
                )

            service_config["ports"] = new_ports

        # Remove explicit container names
        if "container_name" in service_config:
            del service_config["container_name"]

    # Remove explicit networks
    data.pop("networks", None)

    return data, env_vars


def safeify_compose(
    input_path,
    volumes_option="convert-to-named",
    output_path: str | None = None,
):
    output_path = Path(output_path or f"{input_path.stem}.safe.yml")
    # Read, transform, and write
    with open(input_path) as f:
        data = yaml.safe_load(f)

    data, volume_env_vars = transform_volumes(data, volumes_option=volumes_option)
    data, port_env_vars = make_multi_instance_safe(data)

    # Combine volume and port environment variables
    env_vars = {**volume_env_vars, **port_env_vars}

    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    # Print and append environment variables to .env and .safecompose.env files
    if env_vars:
        env_file_path = Path(".env")
        safecompose_env_path = Path(".safecompose.env")
        logger.info("\n📝 Generated environment variables:")
        env_lines = []
        for var_name, default_value in env_vars.items():
            env_line = f"{var_name}={default_value}"
            logger.info(f"  {env_line}")
            env_lines.append(env_line)

        # Append to .env file
        with open(env_file_path, "a") as f:
            f.write("\n# Generated by safeify_compose.py\n")
            f.writelines(f"{line}\n" for line in env_lines)
        logger.info(f"✅ Appended to {env_file_path}")

        # Write to .safecompose.env file
        with open(safecompose_env_path, "w") as f:
            f.write("# Generated by safeify_compose.py\n")
            f.writelines(f"{line}\n" for line in env_lines)
        logger.info(f"✅ Created {safecompose_env_path}")

    logger.info(f"✅ Created {output_path}")
    logger.info(
        f"\nRun with: docker-compose -f {output_path.name} -p <instance-name> up",
    )
    return str(output_path)


def cli() -> None:
    """Command line interface for the script."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(
        description="Prepare docker-compose for running multiple instances",
        epilog="Example: %(prog)s docker-compose.yml -o docker-compose.multi.yml",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="compose_file",
        default="*compose.*ml",
        help="Path to docker-compose.yml file",
    )
    parser.add_argument(
        "--volumes",
        choices=["remove", "keep", "convert-to-named"],
        default="keep",
        help='How to handle docker compose volumes: "remove" (make ephemeral), "keep" (no changes), or "convert-to-named" (transform bind mounts to named volumes)',
    )
    parser.add_argument(
        "-o",
        "--output",
        default="{input_stem}.safe.yml",
        help="Output file",
    )

    args = parser.parse_args()

    # Handle glob pattern for compose file
    compose_files = glob.glob(args.compose_file)
    if not compose_files:
        logger.error(f"Error: No files found matching pattern: {args.compose_file}")
        sys.exit(1)

    if len(compose_files) > 1:
        logger.error(
            f"Error: Multiple files found matching pattern: {args.compose_file}",
        )
        logger.error("Found files: %s", compose_files)
        sys.exit(1)

    input_path = Path(compose_files[0])
    if not input_path.exists():
        logger.error(f"Error: File not found: {input_path}")
        sys.exit(1)

    return safeify_compose(input_path, args.output_path, args.volumes)


if __name__ == "__main__":
    cli()
