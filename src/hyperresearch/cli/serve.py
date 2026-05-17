"""Serve CLI command — browse vault in a web browser."""

from __future__ import annotations

import typer

from hyperresearch.cli._output import console


def serve(
    port: int = typer.Option(9089, "--port", "-p", help="Port to serve on"),
    open_browser: bool = typer.Option(False, "--open", "-o", help="Open browser automatically"),
) -> None:
    """Start a web server to browse the vault."""
    from hyperresearch.core.vault import Vault, VaultError

    try:
        vault = Vault.discover()
    except VaultError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)

    vault.auto_sync()

    from hyperresearch.serve.server import run_server
    run_server(vault, port=port, open_browser=open_browser)


def serve_stop() -> None:
    """Stop a UI server previously launched via `install --serve --detach`.

    Reads the pidfile at ``<vault>/.hyperresearch/serve.pid`` and signals
    the process. Cleans up the pidfile after termination.
    """
    import os
    import signal

    from hyperresearch.core.vault import Vault, VaultError

    try:
        vault = Vault.discover()
    except VaultError as exc:
        console.print(f"[red]Error:[/] {exc}")
        raise typer.Exit(1)

    pid_path = vault.root / ".hyperresearch" / "serve.pid"
    if not pid_path.exists():
        console.print("[yellow]No serve.pid file — nothing to stop.[/]")
        raise typer.Exit(0)

    try:
        pid = int(pid_path.read_text().strip())
    except (OSError, ValueError) as exc:
        console.print(f"[red]Could not read pidfile:[/] {exc}")
        raise typer.Exit(1)

    try:
        os.kill(pid, signal.SIGTERM)
        console.print(f"[green]Stopped UI server[/] (pid {pid}).")
    except ProcessLookupError:
        console.print(f"[dim]Process {pid} already gone.[/]")
    except PermissionError:
        console.print(f"[red]No permission to stop pid {pid}.[/]")
        raise typer.Exit(1)

    try:
        pid_path.unlink()
    except OSError:
        pass
