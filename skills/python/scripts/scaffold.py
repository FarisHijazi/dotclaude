#!/usr/bin/env python3
"""
Project scaffolding script.

Creates a new Python project from templates.

Usage:
    python scaffold.py <project_name> [options]

Example:
    python scaffold.py myapp --author "John Doe" --email "john@example.com"
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def to_snake_case(name: str) -> str:
    """Convert string to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower().replace("-", "_")


def to_kebab_case(name: str) -> str:
    """Convert string to kebab-case."""
    return to_snake_case(name).replace("_", "-")


def replace_placeholders(content: str, replacements: dict[str, str]) -> str:
    """Replace all placeholders in content."""
    for placeholder, value in replacements.items():
        content = content.replace(f"{{{{{placeholder}}}}}", value)
    return content


def scaffold_project(
    project_name: str,
    target_dir: Path,
    author_name: str = "Author",
    author_email: str = "author@example.com",
    github_user: str = "username",
    description: str = "A Python project",
) -> None:
    """Scaffold a new project from templates."""
    templates_dir = Path(__file__).parent.parent / "templates"

    if not templates_dir.exists():
        print(f"Error: Templates directory not found: {templates_dir}")
        sys.exit(1)

    # Normalize names
    project_name_snake = to_snake_case(project_name)
    project_name_kebab = to_kebab_case(project_name)

    # Replacements
    replacements = {
        "PROJECT_NAME": project_name_snake,
        "PROJECT_DESCRIPTION": description,
        "AUTHOR_NAME": author_name,
        "AUTHOR_EMAIL": author_email,
        "GITHUB_USER": github_user,
    }

    # Create project directory
    project_dir = target_dir / project_name_kebab
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    src_dir = project_dir / "src" / project_name_snake
    directories = [
        src_dir,
        src_dir / "api" / "routes",
        src_dir / "cli",
        src_dir / "db",
        src_dir / "models",
        src_dir / "services",
        project_dir / "tests",
        project_dir / ".github" / "workflows",
    ]

    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
        if "tests" not in str(d) and ".github" not in str(d):
            (d / "__init__.py").touch()

    # Template to destination mapping
    file_mapping: dict[str, Path] = {
        "pyproject.toml": project_dir / "pyproject.toml",
        "ruff.toml": project_dir / "ruff.toml",
        ".pre-commit-config.yaml": project_dir / ".pre-commit-config.yaml",
        ".gitignore": project_dir / ".gitignore",
        ".env.example": project_dir / ".env.example",
        "Dockerfile": project_dir / "Dockerfile",
        "docker-compose.yml": project_dir / "docker-compose.yml",
        "__init__.py": src_dir / "__init__.py",
        "main.py": src_dir / "main.py",
        "config.py": src_dir / "config.py",
        "deps.py": src_dir / "api" / "deps.py",
        "health.py": src_dir / "api" / "routes" / "health.py",
        "cli.py": src_dir / "cli" / "main.py",
        "session.py": src_dir / "db" / "session.py",
        "models.py": src_dir / "models" / "base.py",
        "conftest.py": project_dir / "tests" / "conftest.py",
        "test_health.py": project_dir / "tests" / "test_health.py",
        "ci.yml": project_dir / ".github" / "workflows" / "ci.yml",
    }

    # Copy and process templates
    for template_name, dest_path in file_mapping.items():
        template_path = templates_dir / template_name
        if template_path.exists():
            content = template_path.read_text()
            processed = replace_placeholders(content, replacements)
            dest_path.write_text(processed)
            print(f"  Created: {dest_path.relative_to(project_dir)}")

    # Create api/routes/__init__.py
    routes_init = src_dir / "api" / "routes" / "__init__.py"
    routes_init.write_text('"""API routes."""\n')

    # Create tests/__init__.py
    (project_dir / "tests" / "__init__.py").touch()

    # Create README.md
    readme_content = f"""# {project_name_kebab}

{description}

## Quick Start

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn src.{project_name_snake}.main:app --reload

# Or use CLI
uv run {project_name_kebab} serve --reload

# Run tests (install dev deps first)
uv sync --extra dev
uv run pytest

# Lint
uv run ruff check . --fix
uv run ruff format .
```

## Docker

```bash
# Development
docker compose --profile dev up

# Production
docker compose up --build
```

## Project Structure

```
{project_name_kebab}/
├── src/{project_name_snake}/
│   ├── api/           # FastAPI routes
│   ├── cli/           # Typer CLI
│   ├── db/            # Database
│   ├── models/        # SQLModel models
│   └── services/      # Business logic
├── tests/             # Tests
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```
"""
    (project_dir / "README.md").write_text(readme_content)
    print(f"  Created: README.md")

    print(f"\nProject created at: {project_dir}")
    print("\nNext steps:")
    print(f"  cd {project_name_kebab}")
    print("  uv sync --extra dev")
    print("  uv run pre-commit install")
    print("  cp .env.example .env")
    print(f"  uv run {project_name_kebab} serve --reload")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scaffold a new Python project")
    parser.add_argument("name", help="Project name")
    parser.add_argument("--target", "-t", default=".", help="Target directory")
    parser.add_argument("--author", "-a", default="Author", help="Author name")
    parser.add_argument("--email", "-e", default="author@example.com", help="Author email")
    parser.add_argument("--github", "-g", default="username", help="GitHub username")
    parser.add_argument("--description", "-d", default="A Python project", help="Project description")

    args = parser.parse_args()

    scaffold_project(
        project_name=args.name,
        target_dir=Path(args.target).resolve(),
        author_name=args.author,
        author_email=args.email,
        github_user=args.github,
        description=args.description,
    )
