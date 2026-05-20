"""Firecrawl MCP server installer.

Adds the firecrawl/firecrawl-mcp-server entry to ~/.claude.json so the
hyperresearch-fetcher, corpus-critic, and depth-investigator agents
can use mcp__firecrawl__* tools for high-fidelity scraping, multi-page
crawling, structured extraction, and combined search+extract — the
gaps that Exa (neural-search-only) and the built-in `WebSearch` (no
content, just snippets) leave open.

Firecrawl runs locally via `npx -y firecrawl-mcp` (stdio transport).
A `FIRECRAWL_API_KEY` is required; get one at https://firecrawl.dev.
No hosted HTTP endpoint exists (unlike Exa), so we always use stdio.

Idempotent: any existing mcpServers entry whose name starts with
'firecrawl' or 'mcp-server-firecrawl' is left untouched.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Literal

# Tools the hyperresearch pipeline actually uses. We DO NOT enable
# firecrawl_agent / firecrawl_agent_status (that's a parallel deep-
# research pipeline that would conflict with hyperresearch's own
# synthesis), nor the deprecated firecrawl_browser_* tools, nor
# firecrawl_search_feedback (housekeeping for refunds).
_FIRECRAWL_TOOLS: tuple[str, ...] = (
    "firecrawl_scrape",
    "firecrawl_batch_scrape",
    "firecrawl_check_batch_status",
    "firecrawl_map",
    "firecrawl_search",
    "firecrawl_crawl",
    "firecrawl_check_crawl_status",
    "firecrawl_extract",
)

_FIRECRAWL_PACKAGE = "firecrawl-mcp"
_FIRECRAWL_ENTRY_NAME = "firecrawl"

InstallStatus = Literal[
    "installed",
    "already_configured",
    "skipped_no_key",
    "skipped_no_npx",
    "skipped_no_claude_config",
    "error",
]


def resolve_api_key(explicit: str | None = None) -> str | None:
    """Return the API key from the explicit arg or the FIRECRAWL_API_KEY env var.

    Empty / whitespace-only strings are treated as missing.
    """
    for candidate in (explicit, os.environ.get("FIRECRAWL_API_KEY")):
        if candidate and candidate.strip():
            return candidate.strip()
    return None


def existing_firecrawl_entry(mcp_servers: dict) -> str | None:
    """Return the name of any existing 'firecrawl*' MCP server entry, or None."""
    for name in mcp_servers:
        lowered = name.lower()
        if lowered.startswith("firecrawl") or lowered == "mcp-server-firecrawl":
            return name
    return None


def npx_available() -> bool:
    """True if `npx` is on PATH (ships with Node.js)."""
    return shutil.which("npx") is not None


def build_server_entry(api_key: str) -> dict:
    """Build the mcpServers stdio entry for firecrawl-mcp."""
    return {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", _FIRECRAWL_PACKAGE],
        "env": {
            "FIRECRAWL_API_KEY": api_key,
            # Conservative retry / credit thresholds — the upstream README's
            # defaults are reasonable, but encode them explicitly so users
            # see how to tune retries without re-reading docs.
            "FIRECRAWL_RETRY_MAX_ATTEMPTS": "5",
            "FIRECRAWL_RETRY_INITIAL_DELAY": "2000",
            "FIRECRAWL_RETRY_MAX_DELAY": "30000",
            "FIRECRAWL_RETRY_BACKOFF_FACTOR": "3",
            "FIRECRAWL_CREDIT_WARNING_THRESHOLD": "2000",
            "FIRECRAWL_CREDIT_CRITICAL_THRESHOLD": "500",
        },
    }


def install_firecrawl_mcp(
    api_key: str | None = None,
    claude_json_path: Path | None = None,
) -> tuple[InstallStatus, str]:
    """Install the Firecrawl MCP server entry into ~/.claude.json.

    Args:
        api_key: explicit API key. If None, falls back to FIRECRAWL_API_KEY env
                 var. If still empty/missing, the install is skipped.
        claude_json_path: override the path to claude.json (for testing).

    Returns a tuple of (status, human_readable_message).
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
    existing = existing_firecrawl_entry(mcp_servers)
    if existing is not None:
        return ("already_configured", f"existing entry '{existing}' left unchanged")

    resolved_key = resolve_api_key(api_key)
    if not resolved_key:
        return (
            "skipped_no_key",
            "no API key — pass --firecrawl-api-key or set FIRECRAWL_API_KEY in your shell. "
            "Get a key at https://firecrawl.dev",
        )

    if not npx_available():
        return (
            "skipped_no_npx",
            "npx not on PATH — install Node.js LTS "
            "(https://nodejs.org or `nvm install --lts`) then re-run "
            "`hyperresearch install` to add the Firecrawl MCP",
        )

    mcp_servers[_FIRECRAWL_ENTRY_NAME] = build_server_entry(resolved_key)
    target.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ("installed", f"added '{_FIRECRAWL_ENTRY_NAME}' MCP entry to {target}")
