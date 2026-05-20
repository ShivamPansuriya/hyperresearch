"""Reddit MCP server installer.

Adds the eliasbiondo/reddit-mcp-server entry to ~/.claude.json so the
hyperresearch-fetcher, hyperresearch-corpus-critic, and depth-investigator
agents can use mcp__reddit__* tools for community-driven discovery —
current real-world problems, user pain points, open-community workarounds,
and emerging-technology chatter that academic sources and indexed web
search miss.

The server runs locally via `uvx reddit-no-auth-mcp-server` with no API
keys, no OAuth, and no browser required (per the upstream README at
https://github.com/eliasbiondo/reddit-mcp-server).

Idempotent: if any existing mcpServers entry with a name starting with
'reddit' is already present, this function leaves it alone. If uvx is not
on PATH the install is skipped with a clear message — uvx ships with
Astral's uv (`pipx install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Literal

# Tools exposed by reddit-no-auth-mcp-server. Listed here purely for
# documentation / agent-prompt cross-reference — the MCP itself advertises
# them at handshake time, the installer doesn't need to enumerate them in
# the config entry.
_REDDIT_TOOLS: tuple[str, ...] = (
    "search",
    "search_subreddit",
    "get_post",
    "get_subreddit_posts",
    "get_user",
    "get_user_posts",
)

_REDDIT_PACKAGE = "reddit-no-auth-mcp-server"

InstallStatus = Literal[
    "installed",
    "already_configured",
    "skipped_no_uvx",
    "skipped_no_claude_config",
    "skipped_by_flag",
    "error",
]


def existing_reddit_entry(mcp_servers: dict) -> str | None:
    """Return the name of any existing 'reddit*' MCP server entry, or None."""
    for name in mcp_servers:
        if name.lower().startswith("reddit"):
            return name
    return None


def uvx_available() -> bool:
    """True if `uvx` is on PATH (ships with Astral's uv)."""
    return shutil.which("uvx") is not None


def build_server_entry() -> dict:
    """Build the mcpServers stdio entry for reddit-no-auth-mcp-server."""
    return {
        "type": "stdio",
        "command": "uvx",
        "args": [_REDDIT_PACKAGE],
    }


def install_reddit_mcp(
    claude_json_path: Path | None = None,
    *,
    skip: bool = False,
) -> tuple[InstallStatus, str]:
    """Install the Reddit MCP server entry into ~/.claude.json.

    Args:
        claude_json_path: override the path to claude.json (for testing).
        skip: if True, the caller has opted out (e.g. --no-reddit) — return
              ('skipped_by_flag', ...) without touching the config.

    Returns a tuple of (status, human_readable_message):
        ('installed', 'Added reddit MCP entry to <path>')
        ('already_configured', "existing entry 'reddit' left unchanged")
        ('skipped_no_uvx', 'uvx not on PATH — install Astral uv to enable')
        ('skipped_no_claude_config', '~/.claude.json does not exist yet')
        ('skipped_by_flag', 'opt-out flag passed')
        ('error', '<reason>')
    """
    if skip:
        return ("skipped_by_flag", "--no-reddit passed; Reddit MCP not installed")

    target = claude_json_path or (Path.home() / ".claude.json")

    if not target.exists():
        return (
            "skipped_no_claude_config",
            f"{target} does not exist — run Claude Code at least once to create it",
        )

    try:
        config = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ("error", f"failed to parse {target}: {e}")

    mcp_servers = config.setdefault("mcpServers", {})
    existing = existing_reddit_entry(mcp_servers)
    if existing is not None:
        return ("already_configured", f"existing entry '{existing}' left unchanged")

    if not uvx_available():
        return (
            "skipped_no_uvx",
            "uvx not on PATH — install Astral uv "
            "(`curl -LsSf https://astral.sh/uv/install.sh | sh`) "
            "then re-run `hyperresearch install` to add the Reddit MCP",
        )

    mcp_servers["reddit"] = build_server_entry()
    target.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ("installed", f"added 'reddit' MCP entry to {target}")
