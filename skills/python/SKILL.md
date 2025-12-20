---
name: python
description: Create Python projects with modern best practices. Use when asked to create a Python project, FastAPI app, CLI tool, or Python package. Includes uv for package management, Docker, pre-commit, ruff, FastAPI with uvloop, Typer CLI, SQLModel, and Pydantic.
---

# Python Project Skill

This skill helps you create modern Python projects with best practices.

## When to Use

Use this skill when the user asks to:
- Create a new Python project
- Set up a FastAPI application
- Create a CLI tool with Python
- Initialize a Python package with proper tooling
- Set up Docker for a Python project

## Stack Overview

| Component | Tool |
|-----------|------|
| Package Manager | uv (with uvx for tools) |
| Linting/Formatting | ruff |
| Pre-commit Hooks | pre-commit |
| HTTP Framework | FastAPI + uvloop |
| Validation | Pydantic v2 |
| Database ORM | SQLModel |
| CLI Framework | Typer |
| Containerization | Docker + docker-compose |

## Project Creation Steps

### 1. Create Project Structure

```bash
# Create project with uv
uv init <project-name>
cd <project-name>

# Create source layout
mkdir -p src/<project_name>/{api,cli,db,models,services}
touch src/<project_name>/__init__.py
touch src/<project_name>/api/__init__.py
touch src/<project_name>/cli/__init__.py
touch src/<project_name>/db/__init__.py
touch src/<project_name>/models/__init__.py
touch src/<project_name>/services/__init__.py
```

### 2. Configure pyproject.toml

Use the template at [templates/pyproject.toml](templates/pyproject.toml) as a base.

Key dependencies to include:
```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "uvloop>=0.21.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "sqlmodel>=0.0.22",
    "typer>=0.15.0",
    "rich>=13.9.0",
    "httpx>=0.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "ruff>=0.8.0",
    "pre-commit>=4.0.0",
    "mypy>=1.13.0",
]
```

### 3. Configure ruff.toml

Use the template at [templates/ruff.toml](templates/ruff.toml).

### 4. Configure pre-commit

Use the template at [templates/.pre-commit-config.yaml](templates/.pre-commit-config.yaml).

### 5. Create FastAPI Application

Use the template at [templates/main.py](templates/main.py) for the FastAPI entrypoint with uvloop.

Key patterns:
- Use lifespan context manager for startup/shutdown
- Configure uvloop before running
- Use dependency injection for database sessions
- Structure with APIRouter for modular routes

### 6. Create Typer CLI

Use the template at [templates/cli.py](templates/cli.py) for CLI structure.

### 7. Create Docker Configuration

Use templates:
- [templates/Dockerfile](templates/Dockerfile)
- [templates/docker-compose.yml](templates/docker-compose.yml)

### 8. Initialize and Install

```bash
# Install dependencies (including dev dependencies)
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install

# Run linting
uv run ruff check .
uv run ruff format .
```

## File Structure Reference

```
<project-name>/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── <project_name>/
│       ├── __init__.py
│       ├── main.py          # FastAPI app
│       ├── config.py         # Pydantic settings
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py       # Dependencies
│       │   └── routes/
│       │       ├── __init__.py
│       │       └── health.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py       # Typer app
│       ├── db/
│       │   ├── __init__.py
│       │   └── session.py    # Database session
│       ├── models/
│       │   ├── __init__.py
│       │   └── base.py       # SQLModel models
│       └── services/
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_health.py
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── ruff.toml
├── uv.lock
└── README.md
```

## Running the Application

```bash
# Development server
uv run uvicorn src.<project_name>.main:app --reload --host 0.0.0.0 --port 8000

# CLI
uv run <project-name> --help

# With Docker
docker compose up --build

# Run tests (requires dev dependencies)
uv sync --extra dev
uv run pytest

# Linting
uv run ruff check . --fix
uv run ruff format .
```

## Environment Variables

Create `.env` from `.env.example`:

```env
# Application
APP_NAME=myapp
APP_ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=1
```

## Best Practices Checklist

- [ ] Use `uv` for all package operations (never pip directly)
- [ ] Run `uv run ruff check . --fix` before commits
- [ ] Use type hints everywhere
- [ ] Use Pydantic for all external data validation
- [ ] Use SQLModel for database models (combines SQLAlchemy + Pydantic)
- [ ] Use async/await for I/O operations
- [ ] Use dependency injection in FastAPI
- [ ] Keep routes thin, logic in services
- [ ] Write tests for all endpoints
- [ ] Use environment variables for configuration
