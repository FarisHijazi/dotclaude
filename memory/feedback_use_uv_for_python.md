---
name: Always use uv/uvx for Python tooling
description: Never use pip/pipx — always use uv for packages and uvx for CLI tools (pre-commit, ruff, etc.)
type: feedback
---

Always use `uv` and `uvx` for all Python-related tooling — never `pip`, `pipx`, or bare `python -m`.

**Why:** User standardizes on uv across all projects for speed, reproducibility, and avoiding global pip installs.

**How to apply:** When installing Python CLI tools (pre-commit, ruff, mypy, pytest, etc.), use `uvx <tool>` to run them or `uv tool install <tool>` for persistent installs. For project dependencies, use `uv add` / `uv sync`. For creating projects, use `uv init`. Never suggest `pip install` or `pipx`.
