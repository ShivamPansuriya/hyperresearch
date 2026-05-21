"""Remove an MCP (exa | firecrawl | reddit) from hyperresearch's agents.

Edits ONLY the hyperresearch-installed agent files in ~/.claude/agents/.
The MCP server entry in ~/.claude.json is intentionally LEFT IN PLACE —
Claude Code keeps the MCP available for other agents, slash commands, or
direct user calls; hyperresearch's own pipeline just stops referencing it.

Two-step cleanup:
  1. Strip every `mcp__<name>__*` token from the `tools:` frontmatter
     line of each ~/.claude/agents/hyperresearch-*.md.
  2. Strip MCP-specific prose: numbered `### N. <McpName>` sections,
     code fences mentioning the tool, and table rows / bullets keyed
     on the tool.

Idempotent: re-running on an already-removed MCP is a no-op.
Reversible: re-running `hyperresearch install --global` re-adds
everything from the template.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich.console import Console

console = Console()

_KNOWN = ("exa", "firecrawl", "reddit")


def uninstall_mcp(
    name: str = typer.Argument(..., help=f"MCP to remove: {' | '.join(_KNOWN)}"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Strip an MCP from hyperresearch's agent files. Leaves ~/.claude.json untouched."""
    name = name.lower().strip()
    if name not in _KNOWN:
        msg = f"unknown MCP '{name}'. Choose one of: {', '.join(_KNOWN)}"
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": msg}))
        else:
            console.print(f"  [red]error:[/] {msg}")
        raise typer.Exit(2)

    tools_changed, agents_total = _strip_agent_tools(name)
    prose_changed = _strip_agent_prose(name)

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "ok": True,
                    "name": name,
                    "agents": {
                        "tools_updated": tools_changed,
                        "prose_updated": prose_changed,
                        "scanned": agents_total,
                    },
                }
            )
        )
        return

    _print_summary(name, tools_changed, prose_changed, agents_total)


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


# ── agent prose blocks ─────────────────────────────────────────


def _strip_agent_prose(name: str) -> int:
    """Strip MCP-specific prose from each ~/.claude/agents/hyperresearch-*.md.

    Three removal units, each delimiter-bounded so the surrounding markdown
    structure is never broken:

      A. Numbered `### N. <McpName>` sections — header to next `### ` header.
      B. Triple-backtick fenced blocks whose body contains `mcp__<name>__`.
      C. Single bullet lines whose first non-blank token starts with
         `mcp__<name>__`, AND markdown table rows (`| ... |`) containing
         a `mcp__<name>__` token in any cell. Both are removed whole-line
         so the table layout stays valid.

    Returns the number of agent files whose body changed.
    """
    agents_dir = Path.home() / ".claude" / "agents"
    if not agents_dir.exists():
        return 0

    token = f"mcp__{name}__"
    # Header pattern: `### <digits>. <McpName-or-mcp__name__-prefix>`
    # The name may appear as `Exa`, `Reddit`, `Firecrawl`, or as the
    # raw `mcp__name__*` form depending on how the template wrote it.
    name_alts = [name.capitalize(), token]
    header_alt_re = "(?:" + "|".join(re.escape(a) for a in name_alts) + ")"
    section_header_re = re.compile(
        rf"^### \d+\.\s+`?{header_alt_re}", re.IGNORECASE
    )
    any_h3_re = re.compile(r"^### ")
    fence_re = re.compile(r"^```")
    # Bullet whose first non-blank token starts with the MCP prefix.
    bullet_token_re = re.compile(
        rf"^\s*(?:[-*+]\s+)?`?{re.escape(token)}"
    )
    # Markdown table row containing the MCP token in ANY cell.
    table_row_re = re.compile(rf"^\s*\|.*{re.escape(token)}")

    changed = 0
    for path in sorted(agents_dir.glob("hyperresearch-*.md")):
        original = path.read_text(encoding="utf-8")
        lines = original.splitlines(keepends=True)
        out: list[str] = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]

            # (A) numbered MCP section — skip until next `### `
            if section_header_re.match(line):
                i += 1
                while i < n and not any_h3_re.match(lines[i]):
                    i += 1
                continue

            # (B) fenced block — buffer until close fence, drop if matched
            if fence_re.match(line):
                start = i
                buf = [line]
                i += 1
                while i < n and not fence_re.match(lines[i]):
                    buf.append(lines[i])
                    i += 1
                if i < n:
                    buf.append(lines[i])  # closing fence
                    i += 1
                if any(token in b for b in buf):
                    continue  # drop the whole fence
                out.extend(buf)
                continue

            # (C) single bullet starting with the MCP token, OR table
            # row containing the MCP token in any cell
            if bullet_token_re.match(line) or table_row_re.match(line):
                i += 1
                continue

            out.append(line)
            i += 1

        new_text = "".join(out)
        if new_text != original:
            path.write_text(new_text, encoding="utf-8")
            changed += 1

    return changed


# ── output ──────────────────────────────────────────────────────


def _print_summary(
    name: str,
    tools_changed: int,
    prose_changed: int,
    agents_total: int,
) -> None:
    console.print()
    console.print(f"  [bold]Removing {name} from hyperresearch agents[/]")
    console.print("  [dim]~/.claude.json:[/] left unchanged (MCP stays available to Claude Code)")
    if agents_total == 0:
        console.print("  [yellow]~/.claude/agents/:[/] no agent files found (was hyperresearch installed?)")
    else:
        tools_color = "green" if tools_changed else "dim"
        prose_color = "green" if prose_changed else "dim"
        console.print(
            f"  [{tools_color}]agent tools:[/] stripped `mcp__{name}__*` from "
            f"{tools_changed}/{agents_total} `tools:` line(s)"
        )
        console.print(
            f"  [{prose_color}]agent prose:[/] removed sections / fences / rows from "
            f"{prose_changed}/{agents_total} agent body file(s)"
        )
    console.print()
    console.print("  [dim]Restart Claude Code (full quit) so the change takes effect.[/]")
    console.print(f"  [dim]To restore:[/] hyperresearch install --global")
    console.print()
