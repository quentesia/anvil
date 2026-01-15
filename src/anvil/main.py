import typer
from pathlib import Path
from typing import Optional
from anvil.core.upgrader import Upgrader

app = typer.Typer(help="Anvil - AI-powered dependency manager")

@app.command()
def check(
    path: str = typer.Argument(".", help="Path to project root"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Check for updates without applying")
):
    """
    Check for dependency updates and analyze risks.
    """
    typer.echo(f"Analyzing project at {path}...")
    upgrader = Upgrader(path)
    upgrader.check_updates(dry_run=dry_run)

@app.command()
def version():
    """
    Show Anvil version.
    """
    typer.echo("Anvil v0.1.0")

if __name__ == "__main__":
    app()
