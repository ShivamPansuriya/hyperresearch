"""Remove an MCP server (exa | firecrawl | reddit) installed by `hyperresearch install`.

Two-step cleanup:
  1. Delete the matching `mcpServers` entry from ~/.claude.json
  2. Strip every `mcp__<name>__*` token from the `tools:` frontmatter line of
     each ~/.claude/agents/hyperresearch-*.md (so agents don't try to call
     tools that no longer exist).

Prose inside agent bodies is left untouched — fallback ladders like
"Exa → WebSearch" still read sensibly even when Exa is gone.

Idempotent: re-running on an already-removed MCP is a no-op and reports so.
Reversible: re-running `hyperresearch install --global` re-adds everything
from the template.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

console = Console()

_KNOWN = ("exa", "firecrawl", "reddit")

Action = Literal["removed", "not_present", "error"]


def uninstall_mcp(
    name: str = typer.Argument(..., help=f"MCP to remove: {' | '.join(_KNOWN)}"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Remove an MCP server entry and its tool registrations from installed agents."""
    name = name.lower().strip()
    if name not in _KNOWN:
        msg = f"unknown MCP '{name}'. Choose one of: {', '.join(_KNOWN)}"
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": msg}))
        else:
            console.print(f"  [red]error:[/] {msg}")
        raise typer.Exit(2)

    server_action, server_msg = _remove_server_entry(name)
    agents_changed, agents_total = _strip_agent_tools(name)

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "ok": True,
                    "name": name,
                    "server": {"action": server_action, "message": server_msg},
                    "agents": {"updated": agents_changed, "scanned": agents_total},
                }
            )
        )
        return

    _print_summary(name, server_action, server_msg, agents_changed, agents_total)


# ── server entry ────────────────────────────────────────────────


def _remove_server_entry(name: str) -> tuple[Action, str]:
    target = Path.home() / ".claude.json"
    if not target.exists():
        return ("not_present", f"{target} does not exist")

    try:
        config = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ("error", f"failed to parse {target}: {e}")

    servers = config.get("mcpServers", {})
    matched = [k for k in servers if k.lower().startswith(name)]
    if not matched:
        return ("not_present", f"no '{name}*' entry in mcpServers")

    for key in matched:
        del servers[key]

    target.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ("removed", f"removed entries: {', '.join(matched)}")


# ── agent tools: lines ─────────────────────────────────────────


_TOOLS_LINE = re.compile(r"^(tools:\s*)(.+)$", re.MULTILINE)


def _strip_agent_tools(name: str) -> tuple[int, int]:
    """Scan ~/.claude/agents/hyperresearch-*.md and strip mcp__<name>__* tokens.

    Returns (files_changed, files_scanned).
    """
    agents_dir = Path.home() / ".claude" / "agents"
    if not agents_dir.exists():
        return (0, 0)

    files = sorted(agents_dir.glob("hyperresearch-*.md"))
    prefix = f"mcp__{name}__"
    changed = 0

    for path in files:
        text = path.read_text(encoding="utf-8")
        match = _TOOLS_LINE.search(text)
        if not match:
            continue
        tools_csv = match.group(2)
        tokens = [t.strip() for t in tools_csv.split(",")]
        filtered = [t for t in tokens if not t.startswith(prefix)]
        if len(filtered) == len(tokens):
            continue
        new_line = match.group(1) + ", ".join(filtered)
        new_text = text[: match.start()] + new_line + text[match.end():]
        path.write_text(new_text, encoding="utf-8")
        changed += 1

    return (changed, len(files))


# ── output ──────────────────────────────────────────────────────


def _print_summary(
    name: str,
    server_action: Action,
    server_msg: str,
    agents_changed: int,
    agents_total: int,
) -> None:
    color = {"removed": "green", "not_present": "yellow", "error": "red"}[server_action]
    console.print()
    console.print(f"  [bold]Removing {name} MCP[/]")
    console.print(f"  [{color}]~/.claude.json:[/] {server_msg}")
    if agents_total == 0:
        console.print("  [yellow]~/.claude/agents/:[/] no agent files found (was hyperresearch installed?)")
    elif agents_changed == 0:
        console.print(f"  [dim]~/.claude/agents/:[/] no `mcp__{name}__*` tokens found in {agents_total} agent file(s)")
    else:
        console.print(
            f"  [green]~/.claude/agents/:[/] stripped `mcp__{name}__*` tokens from "
            f"{agents_changed}/{agents_total} agent file(s)"
        )
    console.print()
    console.print("  [dim]Restart Claude Code (full quit) so the change takes effect.[/]")
    console.print(f"  [dim]To restore:[/] hyperresearch install --global")
    console.print()
