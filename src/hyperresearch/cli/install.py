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
    serve_after: bool = typer.Option(
        False,
        "--serve",
        help="After install completes, automatically start the interactive UI server (binds 127.0.0.1:9089 and opens your browser). Recommended for one-command setup. Foreground process — Ctrl+C to stop.",
    ),
    serve_port: int = typer.Option(
        9089,
        "--serve-port",
        help="Port the auto-launched UI binds to (only used with --serve).",
    ),
) -> None:
    """Install hyperresearch: init vault + inject CLAUDE.md + install Claude Code hooks."""
    import sys

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
        if serve_after:
            console.print(
                "[dim]--serve ignored for --steps-only (no vault context). "
                "Run `hyperresearch serve` from the project root after install.[/]"
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

        if json_output:
            output(
                success(
                    {
                        "global": True,
                        "home": str(home),
                        "hooks_installed": hook_actions,
                        "prd_skills_installed": prd_result["skills_installed"],
                        "prd_agents_installed": prd_result["agents_installed"],
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
        console.print(
            "\n[bold]Ready.[/] /hyperresearch and /hyperresearch-prd are now available in every Claude Code session."
        )
        console.print(
            "[dim]On first /hyperresearch run in a project, the vault, research/ folder, "
            "and the 16 step skills are created in that project's .claude/. "
            "PRD step skills + agents are installed globally and ready to use immediately.[/]"
        )
        if serve_after:
            console.print(
                "[dim]--serve ignored for --global (no vault context). "
                "Run `hyperresearch serve` inside a project that has the vault initialized.[/]"
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

    # Step 5: Report
    data = {
        "vault_path": str(vault.root),
        "vault": vault_action,
        "agent_docs": doc_actions,
        "hooks_installed": hook_actions,
        "prd_skills_installed": prd_result["skills_installed"],
        "prd_agents_installed": prd_result["agents_installed"],
        "crawl4ai": crawl4ai_status,
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

        console.print("\n[bold]Ready.[/] Agents will now check the research base before web searches.")
        console.print(
            "[dim]/hyperresearch generates a research report; /hyperresearch-prd then turns "
            "a feature request + that research into a PRD.[/]"
        )
        console.print("[dim]Tip: Run 'hyperresearch setup' for interactive configuration (profile, stealth, etc.)[/]")
        if not serve_after:
            console.print(
                f"[dim]UI tip: pass --serve next time to auto-launch the browser, or run "
                f"`hyperresearch serve --open` (port {serve_port}) now.[/]"
            )

    if serve_after:
        console.print(
            f"\n[bold]Starting UI:[/] http://127.0.0.1:{serve_port} "
            "[dim](Ctrl+C to stop)[/]"
        )
        vault.auto_sync()
        from hyperresearch.serve.server import run_server
        run_server(vault, port=serve_port, open_browser=True)


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
