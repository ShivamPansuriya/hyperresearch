"""Exa MCP server installer.

Adds the Exa hosted MCP server entry to ~/.claude.json so the
hyperresearch-fetcher and hyperresearch-corpus-critic agents can use
the mcp__exa__* tools. Uses Exa's hosted HTTP MCP endpoint
(https://mcp.exa.ai/mcp) so no Node.js / npx dependency is required —
just a query-param API key.

Idempotent: if any existing mcpServers entry with a name starting
with 'exa' is already present, this function leaves it alone.

Get an API key at https://exa.ai (dashboard -> API keys).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

# Tools exposed by the Exa hosted MCP. We enable the same set the
# fetcher / corpus-critic agents reference. Order is preserved when
# building the URL so the resulting config matches what users see in
# Exa's documentation.
_EXA_TOOLS: tuple[str, ...] = (
    "web_search_exa",
    "web_search_advanced_exa",
    "get_code_context_exa",
    "crawling_exa",
    "company_research_exa",
    "people_search_exa",
    "deep_researcher_start",
    "deep_researcher_check",
    "deep_search_exa",
)

_EXA_MCP_BASE_URL = "https://mcp.exa.ai/mcp"

InstallStatus = Literal[
    "installed",
    "already_configured",
    "skipped_no_key",
    "skipped_no_claude_config",
    "error",
]


def resolve_api_key(explicit: str | None = None) -> str | None:
    """Return the API key from the explicit arg or the EXA_API_KEY env var.

    Empty / whitespace-only strings are treated as missing.
    """
    for candidate in (explicit, os.environ.get("EXA_API_KEY")):
        if candidate and candidate.strip():
            return candidate.strip()
    return None


def existing_exa_entry(mcp_servers: dict) -> str | None:
    """Return the name of any existing 'exa*' MCP server entry, or None."""
    for name in mcp_servers:
        if name.lower().startswith("exa"):
            return name
    return None


def build_server_entry(api_key: str) -> dict:
    """Build the mcpServers entry for the Exa hosted MCP."""
    tools_param = ",".join(_EXA_TOOLS)
    url = f"{_EXA_MCP_BASE_URL}?exaApiKey={api_key}&tools={tools_param}"
    return {"type": "http", "url": url}


def install_exa_mcp(
    api_key: str | None = None,
    claude_json_path: Path | None = None,
) -> tuple[InstallStatus, str]:
    """Install the Exa MCP server entry into ~/.claude.json.

    Args:
        api_key: explicit API key. If None, falls back to EXA_API_KEY env var.
                 If still empty/missing, the install is skipped.
        claude_json_path: override the path to claude.json (for testing).

    Returns a tuple of (status, human_readable_message):
        ('installed', 'Added Exa MCP entry to <path>')
        ('already_configured', 'Existing entry: <name>')
        ('skipped_no_key', 'No API key supplied (--exa-api-key or EXA_API_KEY)')
        ('skipped_no_claude_config', '~/.claude.json does not exist yet')
        ('error', '<reason>')
    """
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
    existing = existing_exa_entry(mcp_servers)
    if existing is not None:
        return ("already_configured", f"existing entry '{existing}' left unchanged")

    resolved_key = resolve_api_key(api_key)
    if not resolved_key:
        return (
            "skipped_no_key",
            "no API key — pass --exa-api-key or set EXA_API_KEY in your shell. "
            "Get a key at https://exa.ai",
        )

    mcp_servers["exa"] = build_server_entry(resolved_key)

    # Pretty-print to preserve readability of the user's config file.
    target.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ("installed", f"added 'exa' MCP entry to {target}")
