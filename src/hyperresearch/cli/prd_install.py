"""CLI command: `hyperresearch prd-install` — install PRD extension."""

from __future__ import annotations

from pathlib import Path

import typer

from hyperresearch.cli._output import console, output
from hyperresearch.core.prd_install import (
    install_prd_extension,
    install_prd_extension_global,
    prd_extension_status,
)
from hyperresearch.models.output import success


def prd_install(
    path: str = typer.Argument(".", help="Project root to install PRD extension in"),
    global_install: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Install to ~/.claude/ instead of <path>/.claude/ so the slash command is available everywhere.",
    ),
    status_only: bool = typer.Option(
        False,
        "--status",
        help="Print install status without modifying anything.",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Install the hyperresearch-PRD extension (12 step skills + 9 subagents).

    After this completes, the `/hyperresearch-prd` slash command becomes
    available to Claude Code in the target. Run AFTER a successful
    `/hyperresearch` session to generate a PRD from a feature request +
    the prior research final report.
    """
    target = Path.home() if global_install else Path(path).resolve()

    if status_only:
        status = prd_extension_status(target)
        if json_output:
            output(success(status), json_mode=True)
            return
        console.print(f"[bold]PRD extension status at {target}/.claude/[/]")
        console.print("[bold]Skills:[/]")
        for name, ok in status["skills"].items():
            mark = "[green]✓[/]" if ok else "[red]✗[/]"
            console.print(f"  {mark} {name}")
        console.print("[bold]Agents:[/]")
        for name, ok in status["agents"].items():
            mark = "[green]✓[/]" if ok else "[red]✗[/]"
            console.print(f"  {mark} {name}")
        return

    result = install_prd_extension_global() if global_install else install_prd_extension(target)
    if json_output:
        output(success({"target": str(target), **result}), json_mode=True)
        return
    console.print(f"[green]PRD extension installed:[/] {target}/.claude/")
    console.print(f"  skills: {len(result['skills_installed'])}")
    console.print(f"  agents: {len(result['agents_installed'])}")
    console.print("\n[bold]Ready.[/] Invoke `/hyperresearch-prd` after a `/hyperresearch` run.")
