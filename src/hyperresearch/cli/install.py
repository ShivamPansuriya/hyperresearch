"""Install command — one-step setup: vault init + agent hooks + docs injection."""

from __future__ import annotations

from pathlib import Path

import typer

from hyperresearch.cli._output import console, output
from hyperresearch.models.output import error, success


def install(
    path: str = typer.Argument(".", help="Path to install in"),
    name: str = typer.Option("Research Base", "--name", "-n", help="Vault name"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
    global_install: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Install Claude Code entry skill + agents to ~/.claude/ so /hyperresearch works in every Claude Code session anywhere. Skips vault init, CLAUDE.md, and the 16 step skills (those happen per-project on first /hyperresearch run).",
    ),
    steps_only: bool = typer.Option(
        False,
        "--steps-only",
        help="Install only the 16 step skills to <PATH>/.claude/skills/. Used internally by the entry skill bootstrap on first /hyperresearch invocation in a project. Not normally invoked by users.",
    ),
    exa_api_key: str = typer.Option(
        "",
        "--exa-api-key",
        help="Exa MCP API key (https://exa.ai). If omitted, falls back to the EXA_API_KEY environment variable. If neither is set, the Exa MCP install step is skipped silently — the pipeline still works using WebSearch + academic APIs.",
    ),
    no_reddit: bool = typer.Option(
        False,
        "--no-reddit",
        help="Skip installing the Reddit MCP server (eliasbiondo/reddit-no-auth-mcp-server). By default the installer adds it to ~/.claude.json so agents can read real-world community discussion. Requires `uvx` (Astral uv) on PATH; otherwise skipped automatically with a hint.",
    ),
) -> None:
    """Install hyperresearch: init vault + inject CLAUDE.md + install Claude Code hooks."""
    import sys

    from hyperresearch.core.exa_mcp import install_exa_mcp
    from hyperresearch.core.reddit_mcp import install_reddit_mcp
    from hyperresearch.core.hooks import (
        _install_hyperresearch_step_skills,
        install_global_hooks,
        install_hooks,
    )
    from hyperresearch.core.prd_install import install_prd_extension
    from hyperresearch.core.vault import Vault, VaultError

    # Steps-only path: lazy install of the 16 step skills to a project's
    # .claude/skills/. Called by the entry skill's bootstrap on first
    # /hyperresearch in a project (after a global install). Cheap no-op
    # on subsequent invocations.
    if steps_only:
        target = Path(path).resolve()
        result = _install_hyperresearch_step_skills(target)
        # Also install the PRD extension's 12 step skills + 9 subagents so
        # /hyperresearch-prd and the per-step PRD slash commands work right
        # alongside the research steps.
        prd_result = install_prd_extension(target)
        if json_output:
            output(
                success(
                    {
                        "steps_installed": result,
                        "prd_skills_installed": prd_result["skills_installed"],
                        "prd_agents_installed": prd_result["agents_installed"],
                        "target": str(target),
                    },
                    vault=None,
                ),
                json_mode=True,
            )
            return
        if result:
            console.print(f"[green]Step skills installed:[/] {target}/.claude/skills/")
            console.print(f"  {result}")
        else:
            console.print(f"[dim]Step skills already installed at {target}/.claude/skills/[/]")
        console.print(
            f"[green]PRD extension:[/] {len(prd_result['skills_installed'])} skills, "
            f"{len(prd_result['agents_installed'])} agents installed at {target}/.claude/"
        )
        return

    # Global install path: only the user-level Claude Code entry skill +
    # agents. No vault, no CLAUDE.md, no step skills — pure "make the
    # slash command available everywhere" mode. Step skills install
    # per-project, lazily, when the entry skill bootstrap calls
    # `hyperresearch install --steps-only .` on first invocation.
    if global_install:
        from hyperresearch.core.agent_docs import _resolve_executable
        from hyperresearch.core.prd_install import install_prd_extension_global

        hpr_path = _resolve_executable()
        home = Path.home()
        hook_actions = install_global_hooks(home, hpr_path=hpr_path)
        # Global-install also installs the PRD extension globally so the
        # /hyperresearch-prd entry router and all 12 per-step slash commands
        # work in every Claude Code session.
        prd_result = install_prd_extension_global(home)
        # Add the Exa MCP server entry to ~/.claude.json. Resolves the key
        # from --exa-api-key, then EXA_API_KEY env, then (if interactive and
        # not already configured) prompts the user. Skips silently if no key
        # is available — the pipeline still works with WebSearch only.
        resolved_key = _resolve_exa_key_with_optional_prompt(exa_api_key, json_output)
        exa_status, exa_message = install_exa_mcp(resolved_key or None)
        # Reddit MCP: no API key needed; install unconditionally unless --no-reddit
        # was passed or uvx is missing (in which case skip with a hint).
        reddit_status, reddit_message = install_reddit_mcp(skip=no_reddit)

        if json_output:
            output(
                success(
                    {
                        "global": True,
                        "home": str(home),
                        "hooks_installed": hook_actions,
                        "prd_skills_installed": prd_result["skills_installed"],
                        "prd_agents_installed": prd_result["agents_installed"],
                        "exa_mcp": {"status": exa_status, "message": exa_message},
                        "reddit_mcp": {"status": reddit_status, "message": reddit_message},
                    },
                    vault=None,
                ),
                json_mode=True,
            )
            return

        console.print(f"[green]Global install:[/] {home}/.claude/")
        if hook_actions:
            for action in hook_actions:
                console.print(f"  {action}")
        else:
            console.print("[dim]All skills and agents already installed.[/]")
        console.print(
            f"[green]PRD extension:[/] {len(prd_result['skills_installed'])} skills, "
            f"{len(prd_result['agents_installed'])} agents installed globally."
        )
        _print_exa_status(exa_status, exa_message)
        _print_reddit_status(reddit_status, reddit_message)
        console.print(
            "\n[bold]Ready.[/] /hyperresearch and /hyperresearch-prd are now available in every Claude Code session."
        )
        console.print(
            "[dim]On first /hyperresearch run in a project, the vault, research/ folder, "
            "and the 16 step skills are created in that project's .claude/. "
            "PRD step skills + agents are installed globally and ready to use immediately.[/]"
        )
        return

    root = Path(path).resolve()

    # First-time install in an interactive terminal → run the setup TUI instead
    is_new = not (root / ".hyperresearch").exists()
    is_interactive = not json_output and sys.stdin.isatty()
    if is_new and is_interactive:
        from hyperresearch.cli.setup import setup

        setup(path=path, json_output=False)
        return

    # Step 1: Init vault (skip if already exists)
    try:
        vault = Vault.discover(root)
        vault_action = "existing"
    except VaultError:
        try:
            vault = Vault.init(root, name=name)
            vault_action = "created"
        except VaultError as e:
            if json_output:
                output(error(str(e), "INIT_ERROR"), json_mode=True)
            else:
                console.print(f"[red]Error:[/] {e}")
            raise typer.Exit(1)

    # Step 2: Resolve the hyperresearch executable path
    from hyperresearch.core.agent_docs import _resolve_executable, inject_agent_docs

    hpr_path = _resolve_executable()

    # Step 3: Always re-inject CLAUDE.md (updates blurb + path)
    doc_actions = inject_agent_docs(root)

    # Step 4: Install Claude Code hook + skills + subagents
    hook_actions = install_hooks(root, hpr_path=hpr_path)

    # Step 4b: Install the PRD extension (12 step skills + 9 subagents).
    # The PRD pipeline runs after a research run completes.
    prd_result = install_prd_extension(root)

    # Step 3: Auto-configure crawl4ai if installed
    crawl4ai_status = _setup_crawl4ai(vault)

    # Step 4c: Add Exa MCP server entry to ~/.claude.json. Resolves the key
    # from --exa-api-key, then EXA_API_KEY env, then (if interactive and
    # not already configured) prompts the user. Skipped silently if no key.
    resolved_key = _resolve_exa_key_with_optional_prompt(exa_api_key, json_output)
    exa_status, exa_message = install_exa_mcp(resolved_key or None)

    # Step 4d: Reddit MCP — community-driven discovery (no API key required).
    # Install unconditionally unless --no-reddit was passed or uvx is missing.
    reddit_status, reddit_message = install_reddit_mcp(skip=no_reddit)

    # Step 5: Report
    data = {
        "vault_path": str(vault.root),
        "vault": vault_action,
        "agent_docs": doc_actions,
        "hooks_installed": hook_actions,
        "prd_skills_installed": prd_result["skills_installed"],
        "prd_agents_installed": prd_result["agents_installed"],
        "crawl4ai": crawl4ai_status,
        "exa_mcp": {"status": exa_status, "message": exa_message},
        "reddit_mcp": {"status": reddit_status, "message": reddit_message},
    }

    if json_output:
        output(success(data, vault=str(vault.root)), json_mode=True)
    else:
        if vault_action == "created":
            console.print(f"[green]Vault created:[/] {vault.root}")
        else:
            console.print(f"[dim]Vault exists:[/] {vault.root}")

        if doc_actions:
            console.print("[green]Agent docs:[/]")
            for action in doc_actions:
                console.print(f"  {action}")

        if hook_actions:
            console.print("[green]Hooks installed:[/]")
            for action in hook_actions:
                console.print(f"  {action}")
        else:
            console.print("[dim]All hooks already installed.[/]")

        console.print(
            f"[green]PRD extension:[/] {len(prd_result['skills_installed'])} skills, "
            f"{len(prd_result['agents_installed'])} agents at {root}/.claude/"
        )

        if crawl4ai_status == "configured":
            console.print("[green]crawl4ai:[/] detected, set as default provider + browser ready")
        elif crawl4ai_status == "browser_installed":
            console.print("[green]crawl4ai:[/] browser installed + set as default provider")
        elif crawl4ai_status == "not_installed":
            console.print(
                "[dim]crawl4ai:[/] not installed. "
                "For local headless browsing: pip install hyperresearch[crawl4ai]"
            )

        _print_exa_status(exa_status, exa_message)
        _print_reddit_status(reddit_status, reddit_message)

        console.print("\n[bold]Ready.[/] Agents will now check the research base before web searches.")
        console.print(
            "[dim]/hyperresearch generates a research report; /hyperresearch-prd then turns "
            "a feature request + that research into a PRD.[/]"
        )
        console.print("[dim]Tip: Run 'hyperresearch setup' for interactive configuration (profile, stealth, etc.)[/]")


def _resolve_exa_key_with_optional_prompt(cli_arg: str, json_output: bool) -> str:
    """Resolve the Exa API key from --exa-api-key, then EXA_API_KEY env, then
    (if interactive and not already configured) prompt the user.

    Returns the resolved key, or an empty string to signal 'skip Exa install'.

    Skips the prompt when:
      - A key was already supplied via flag or env.
      - We are in --json mode or stdin is not a TTY.
      - ~/.claude.json already has an exa* entry (idempotent).
    """
    import json as _json
    import sys
    from hyperresearch.core.exa_mcp import existing_exa_entry, resolve_api_key

    # Already have a key from flag or env?
    resolved = resolve_api_key(cli_arg or None)
    if resolved:
        return resolved

    # Non-interactive (JSON / piped / CI) — skip prompt, let installer skip.
    if json_output or not sys.stdin.isatty():
        return ""

    # Exa already configured? Skip prompt — installer is idempotent and will
    # report 'already_configured' downstream.
    claude_json_path = Path.home() / ".claude.json"
    if claude_json_path.exists():
        try:
            data = _json.loads(claude_json_path.read_text(encoding="utf-8"))
            if existing_exa_entry(data.get("mcpServers", {})):
                return ""
        except _json.JSONDecodeError:
            pass

    # Interactive prompt.
    from rich.prompt import Prompt

    console.print()
    console.print(
        "[bold cyan]Exa MCP — neural web search (optional)[/]"
    )
    console.print(
        "[dim]With an Exa API key, the fetcher and corpus-critic agents use[/]"
    )
    console.print(
        "[dim]neural search for higher-signal discovery. Get a key at https://exa.ai[/]"
    )
    console.print(
        "[dim]Press Enter to skip — the pipeline still works with WebSearch only.[/]"
    )
    return Prompt.ask("  Exa API key (blank to skip)", default="").strip()


def _print_exa_status(status: str, message: str) -> None:
    """Pretty-print the Exa MCP install result to the console."""
    if status == "installed":
        console.print(f"[green]Exa MCP:[/] {message}")
    elif status == "already_configured":
        console.print(f"[dim]Exa MCP:[/] {message}")
    elif status == "skipped_no_key":
        console.print(
            "[dim]Exa MCP:[/] skipped (no API key). "
            "Re-run with --exa-api-key <KEY> or set EXA_API_KEY to enable neural web search. "
            "Get a key at https://exa.ai"
        )
    elif status == "skipped_no_claude_config":
        console.print(f"[yellow]Exa MCP:[/] {message}")
    else:
        console.print(f"[yellow]Exa MCP:[/] {message}")


def _print_reddit_status(status: str, message: str) -> None:
    """Pretty-print the Reddit MCP install result to the console."""
    if status == "installed":
        console.print(f"[green]Reddit MCP:[/] {message}")
    elif status == "already_configured":
        console.print(f"[dim]Reddit MCP:[/] {message}")
    elif status == "skipped_no_uvx":
        console.print(f"[yellow]Reddit MCP:[/] {message}")
    elif status == "skipped_by_flag":
        console.print("[dim]Reddit MCP:[/] skipped (--no-reddit)")
    elif status == "skipped_no_claude_config":
        console.print(f"[yellow]Reddit MCP:[/] {message}")
    else:
        console.print(f"[yellow]Reddit MCP:[/] {message}")


def _setup_crawl4ai(vault) -> str:
    """Detect crawl4ai, install browser if needed, set as default provider.

    Returns: 'configured' (already ready), 'browser_installed' (just set up),
             'not_installed' (crawl4ai not available).
    """
    try:
        import crawl4ai  # noqa: F401
    except ImportError:
        return "not_installed"

    # Set crawl4ai as the default provider if still on builtin
    if vault.config.web_provider == "builtin":
        vault.config.web_provider = "crawl4ai"
        vault.config.save(vault.config_path)

    # Check if browser is already installed
    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        browser.close()
        pw.stop()
        return "configured"
    except Exception:
        pass

    # Try to install the browser
    import subprocess
    import sys

    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
        )
        return "browser_installed"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "configured"  # best effort — user can install manually
