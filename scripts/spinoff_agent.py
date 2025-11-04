#!/usr/bin/python3
"""Parallel Agent Runner - Run AI agents on isolated repo copies.

Examples:
%(prog)s auth-system -p "Add JWT authentication"
%(prog)s payment-flow -d postgres,redis --source-dir /path/to/repo
%(prog)s refactor-api --source-dir ../other-repo -p "Refactor API"

Environment Variables:
WORKSPACES_DIR    Directory for workspaces (default: ./workspaces)

"""

import argparse
import glob
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from safeify_compose import safeify_compose

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# def copy_with_gitignore(src_dir: Path, dst_dir: Path) -> None:
#     """Copy directory while respecting .gitignore rules using git and tar.

#     Args:
#         src_dir: Source directory (must be a git repository)
#         dst_dir: Destination directory to copy to

#     """
#     src_dir = Path(src_dir)
#     dst_dir = Path(dst_dir)

#     logger.info(f"Copying {src_dir} to {dst_dir} respecting .gitignore")

#     dst_dir.mkdir(parents=True, exist_ok=True)

#     original_cwd = os.getcwd()
#     try:
#         os.chdir(src_dir)

#         # Copy files respecting git ignore rules using tar pipeline
#         cmd = f"(git ls-files; git ls-files --others --exclude-standard) | tar -T - -cf - | tar -xf - -C {dst_dir}"
#         subprocess.run(cmd, shell=True, check=True)

#         logger.info("Successfully copied respecting .gitignore rules")

#     except subprocess.CalledProcessError as e:
#         logger.error(f"Failed to copy: {e}")
#         raise
#     finally:
#         os.chdir(original_cwd)


def run_cmd(cmd, check=True, capture=False, cwd=None):
    """Run a command."""
    if capture:
        return subprocess.run(cmd, check=check, capture_output=True, text=True, cwd=cwd)
    return subprocess.run(cmd, check=check, cwd=cwd)


def get_repo_root(input_dir):
    """Get the git repository root directory."""
    result = run_cmd(
        ["git", "rev-parse", "--show-toplevel"],
        capture=True,
        cwd=input_dir,
    )
    return Path(result.stdout.strip())


def checkout_branch(workspace_path, branch_name, base_branch) -> None:
    """Create or checkout a branch in the workspace."""
    logger.info(f"Checking out branch: {branch_name}")

    # Check if branch exists
    result = run_cmd(
        ["git", "rev-parse", "--verify", branch_name],
        check=False,
        capture=True,
        cwd=workspace_path,
    )

    if result.returncode == 0:
        logger.info(f"Branch '{branch_name}' exists, checking it out")
        run_cmd(["git", "checkout", branch_name], cwd=workspace_path)
    else:
        logger.info(f"Creating new branch '{branch_name}' from '{base_branch}'")
        run_cmd(["git", "checkout", "-b", branch_name, base_branch], cwd=workspace_path)

    logger.info("✓ Branch ready")


def setup_docker(workspace_path, workspace_id, docker_services) -> bool:
    """Setup and start docker services."""
    logger.info("Setting up Docker environment")

    # Find docker-compose file
    compose_file = None
    for name in glob.glob("*compose.y*ml"):
        if (workspace_path / name).exists():
            compose_file = name
            break

    if not compose_file:
        logger.warning("No docker-compose file found, skipping docker setup")
        return False

    safe_compose_path = workspace_path / "docker-compose.safe.yml"

    safeify_compose(workspace_path / compose_file, output_path=safe_compose_path)
    # Start docker services
    docker_cmd = [
        "docker",
        "compose",
        "-f",
        "docker-compose.safe.yml",
        "-p",
        workspace_id,
        "up",
        "--build",
        "--force-recreate",
        "-d",
    ]

    if docker_services and docker_services != "all":
        logger.info(f"Starting services: {', '.join(docker_services)}")
        docker_cmd.extend(docker_services)
    else:
        logger.info("Starting all services")

    run_cmd(docker_cmd, cwd=workspace_path)
    logger.info("✓ Docker services started")

    # Show running containers
    run_cmd(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.safe.yml",
            "-p",
            workspace_id,
            "ps",
        ],
        cwd=workspace_path,
    )

    return True


def cleanup_docker(workspace_path, workspace_id) -> None:
    """Stop and remove docker containers."""
    safe_compose = workspace_path / "docker-compose.safe.yml"

    if safe_compose.exists():
        logger.info("Stopping docker services")
        run_cmd(
            [
                "docker",
                "compose",
                "-f",
                "docker-compose.safe.yml",
                "-p",
                workspace_id,
                "down",
                "-v",
            ],
            check=False,
            cwd=workspace_path,
        )


def cleanup_workspace(workspace_path) -> None:
    """Remove workspace directory."""
    if workspace_path.exists():
        logger.info("Removing workspace directory")
        shutil.rmtree(workspace_path)


def run_agent(agent_cmd, agent_prompt, workspace_path) -> None:
    """Run the AI agent."""
    logger.info(f"Starting agent: {agent_cmd}")
    logger.info(f"Prompt: {agent_prompt}")

    run_cmd([agent_cmd, agent_prompt], cwd=workspace_path)


def show_summary(branch_name, workspace_path, base_branch) -> None:
    """Show completion summary."""
    logger.info("=== Agent completed ===")
    logger.info("Branch: %s", branch_name)
    logger.info("Workspace: %s", workspace_path)
    logger.info("Base branch: %s", base_branch)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        default=None,
        type=Path,
        help="Source directory/repository to copy from (default: current git repo root)",
    )
    parser.add_argument("feature_name", help="Name of the feature to build")
    parser.add_argument(
        "-a",
        "--agent",
        default="claude-code",
        help="Agent command",
    )
    parser.add_argument(
        "-d",
        "--docker-services",
        default=["all"],
        type=lambda x: x.split(","),
        help="Comma-separated services to run or 'all'",
    )
    parser.add_argument("-p", "--prompt", help="Prompt for the agent")
    parser.add_argument(
        "--workspaces-dir",
        type=Path,
        default=os.getenv("WORKSPACES_DIR", "./workspaces"),
        help="Workspaces directory",
    )

    return parser


def main() -> None:
    args = get_parser().parse_args()
    # Generate unique workspace ID
    workspace_id = f"{args.feature_name}_{int(time.time())}_{os.getpid()}"
    workspace_path = args.workspaces_dir / workspace_id
    branch_name = f"feat/{args.feature_name}"
    base_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    # Track state for cleanup
    docker_started = False

    def cleanup_handler(signum=None, frame=None) -> None:
        """Cleanup on exit or interrupt."""
        logger.info("\n=== Cleaning up ===")
        if docker_started:
            cleanup_docker(workspace_path, workspace_id)
        cleanup_workspace(workspace_path)
        logger.info("✓ Cleanup completed")
        sys.exit(0 if signum is None else 128 + signum)

    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)

    try:
        # Print header
        logger.info("=== Parallel Agent Runner ===")
        logger.info("Feature: %s", args.feature_name)
        logger.info("Branch: %s", branch_name)
        logger.info("Workspace: %s", workspace_path)

        # Get repo root
        repo_root = args.input_dir or get_repo_root(".")

        # Create workspaces directory
        args.workspaces_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Copying repo from %s to %s", repo_root, workspace_path)
        shutil.copytree(repo_root, workspace_path, symlinks=True)
        logger.info("✓ Repo copied")

        # Checkout branch
        checkout_branch(workspace_path, branch_name, base_branch)

        # Setup docker if needed
        if args.docker_services:
            docker_started = setup_docker(
                workspace_path,
                workspace_id,
                args.docker_services,
            )

        # Run agent
        run_agent(args.agent, args.prompt, workspace_path)

        # Show summary
        show_summary(branch_name, workspace_path, base_branch)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        cleanup_handler()
    except subprocess.CalledProcessError as e:
        logger.exception("Command failed with exit code %s", e.returncode)
        cleanup_handler()
        sys.exit(e.returncode)
    except Exception:
        logger.exception("Error occurred")
        cleanup_handler()
        sys.exit(1)

    # Normal cleanup
    cleanup_handler()


if __name__ == "__main__":
    main()
