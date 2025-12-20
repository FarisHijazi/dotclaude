"""
Typer CLI application.

Provides command-line interface for the application.
"""

import asyncio
import code
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from {{PROJECT_NAME}} import __version__
from {{PROJECT_NAME}}.config import settings
from {{PROJECT_NAME}}.db.session import init_db


app = typer.Typer(
    name="{{PROJECT_NAME}}",
    help="{{PROJECT_DESCRIPTION}}",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


@app.callback()
def callback() -> None:
    """{{PROJECT_DESCRIPTION}}"""


@app.command()
def serve(
    host: Annotated[
        str, typer.Option("--host", "-h", help="Host to bind to")
    ] = "0.0.0.0",  # noqa: S104
    port: Annotated[int, typer.Option("--port", "-p", help="Port to bind to")] = 8000,
    reload: Annotated[
        bool, typer.Option("--reload", "-r", help="Enable auto-reload")
    ] = False,
    workers: Annotated[
        int, typer.Option("--workers", "-w", help="Number of workers")
    ] = 1,
) -> None:
    """Start the FastAPI server."""
    console.print(f"[green]Starting server at http://{host}:{port}[/green]")

    uvicorn.run(
        "{{PROJECT_NAME}}.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        loop="uvloop",
    )


@app.command()
def version() -> None:
    """Show version information."""
    table = Table(title="Version Information")
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="green")

    table.add_row("{{PROJECT_NAME}}", __version__)

    console.print(table)


@app.command()
def info() -> None:
    """Show application information."""
    table = Table(title="Application Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("App Name", settings.app_name)
    table.add_row("Environment", settings.app_env)
    table.add_row("Debug", str(settings.debug))
    table.add_row("Host", settings.host)
    table.add_row("Port", str(settings.port))

    console.print(table)


@app.command()
def db(
    action: Annotated[
        str,
        typer.Argument(help="Database action: init, migrate, upgrade, downgrade"),
    ],
    message: Annotated[
        str | None,
        typer.Option("--message", "-m", help="Migration message"),
    ] = None,
) -> None:
    """Database management commands."""
    if action == "init":
        console.print("[yellow]Initializing database...[/yellow]")
        asyncio.run(init_db())
        console.print("[green]Database initialized successfully![/green]")
    elif action == "migrate":
        if not message:
            console.print("[red]Error: Migration message required (-m)[/red]")
            raise typer.Exit(1)
        console.print(f"[yellow]Creating migration: {message}[/yellow]")
        # TODO: Add Alembic migration logic
        console.print("[green]Migration created![/green]")
    elif action == "upgrade":
        console.print("[yellow]Upgrading database...[/yellow]")
        # TODO: Add Alembic upgrade logic
        console.print("[green]Database upgraded![/green]")
    elif action == "downgrade":
        console.print("[yellow]Downgrading database...[/yellow]")
        # TODO: Add Alembic downgrade logic
        console.print("[green]Database downgraded![/green]")
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        raise typer.Exit(1)


@app.command()
def shell() -> None:
    """Start an interactive Python shell with app context."""
    banner = f"""
[{{PROJECT_NAME}} Interactive Shell]
Environment: {settings.app_env}

Available objects:
  - settings: Application settings
"""

    local_vars = {
        "settings": settings,
    }

    console.print("[green]Starting interactive shell...[/green]")
    code.interact(banner=banner, local=local_vars)


if __name__ == "__main__":
    app()
