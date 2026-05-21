"""Interactive setup TUI — first-time onboarding and settings configuration."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table

console = Console()


def setup(
    path: str = typer.Argument(".", help="Path to set up"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output (non-interactive)"),
) -> None:
    """Interactive setup — configure hyperresearch step by step."""
    if json_output or not sys.stdin.isatty():
        import subprocess

        cmd = [sys.executable, "-m", "hyperresearch", "install", path]
        if json_output:
            cmd.append("--json")
        raise typer.Exit(subprocess.call(cmd))

    root = Path(path).resolve()

    console.print()
    console.print(
        Panel(
            "[bold cyan]hyperresearch[/]\n"
            "[dim]Agent-driven research knowledge base[/]\n\n"
            "[dim]Your AI agents will collect, search, and synthesize\n"
            "web research into a persistent, searchable wiki.[/]",
            border_style="cyan",
            padding=(1, 4),
        )
    )

    vault_name = "Research Base"

    # ── Step 1: Web Provider ──────────────────────────────────────
    console.print()
    console.print(Rule("[bold]Step 1[/]  Web Provider", style="cyan"))
    console.print()

    has_crawl4ai = _check_crawl4ai()
    if has_crawl4ai:
        console.print("  [green]crawl4ai detected[/] — local headless Chromium browser")
        console.print()
        console.print("  crawl4ai fetches web pages using a real browser. It handles")
        console.print("  JavaScript, bypasses bot detection, and saves full content.")
        console.print()
        console.print("  [dim]Without it, your agent's built-in WebFetch is used instead —[/]")
        console.print("  [dim]which often gets blocked, returns incomplete content,[/]")
        console.print("  [dim]and doesn't persist across sessions.[/]")
        console.print()
        use_crawl4ai = Confirm.ask("  Use crawl4ai as the default web provider?", default=True)
    else:
        console.print("  [yellow]crawl4ai not installed[/]")
        console.print("  Your agent's built-in WebFetch will be used instead.")
        console.print("  [dim]For headless browser support: pip install hyperresearch[crawl4ai][/]")
        use_crawl4ai = False

    provider = "crawl4ai" if use_crawl4ai else "builtin"

    # ── Step 2: Browser Profile ───────────────────────────────────
    profile = ""
    if use_crawl4ai:
        console.print()
        console.print(Rule("[bold]Step 2[/]  Browser Profile", style="cyan"))
        console.print()
        console.print("  A login profile lets hyperresearch access sites you're")
        console.print("  logged into — LinkedIn, Twitter, paywalled news, etc.")
        console.print()

        existing_profiles = _list_profiles()

        table = Table(show_header=False, box=None, padding=(0, 2, 0, 4))
        table.add_column(style="bold cyan", width=3)
        table.add_column()

        opt_num = 1
        use_existing_opt = None
        if existing_profiles:
            use_existing_opt = str(opt_num)
            table.add_row(use_existing_opt, "Use an existing profile")
            opt_num += 1
        create_opt = str(opt_num)
        table.add_row(create_opt, "Create a new profile [dim]— opens browser, ~2 min[/]")
        opt_num += 1
        skip_opt = str(opt_num)
        table.add_row(skip_opt, "Skip [dim]— public pages only[/]")
        console.print(table)
        console.print()

        valid = [create_opt, skip_opt]
        if use_existing_opt:
            valid.insert(0, use_existing_opt)
        default = use_existing_opt if existing_profiles else skip_opt

        choice = Prompt.ask("  Choose", choices=valid, default=default)

        if choice == use_existing_opt and existing_profiles:
            profile = _pick_existing_profile(existing_profiles)
        elif choice == create_opt:
            profile = _create_profile_interactive()
        # else: skip, profile stays ""

    # Skip MCP key prompts if the corresponding entry already exists in
    # ~/.claude.json — the installers are idempotent and won't overwrite
    # an existing entry, so asking for the key would be wasted typing.
    from hyperresearch.core.exa_mcp import existing_exa_entry
    from hyperresearch.core.firecrawl_mcp import existing_firecrawl_entry
    _mcp_servers = _read_mcp_servers()
    exa_already = existing_exa_entry(_mcp_servers) is not None
    firecrawl_already = existing_firecrawl_entry(_mcp_servers) is not None

    # ── Step 3: Exa MCP API key (optional) ────────────────────────
    console.print()
    console.print(Rule("[bold]Step 3[/]  Exa MCP API key (optional)", style="cyan"))
    console.print()
    if exa_already:
        console.print("  [dim]Exa MCP already configured in ~/.claude.json — skipping prompt.[/]")
        exa_api_key = ""
    else:
        console.print("  [dim]Exa is a neural web-search engine. With an API key, the[/]")
        console.print("  [dim]fetcher + corpus-critic agents use Exa's hosted MCP for[/]")
        console.print("  [dim]higher-signal discovery. Get a key at https://exa.ai[/]")
        console.print()
        console.print("  [dim]Press Enter to skip — pipeline still works with WebSearch.[/]")
        console.print()
        exa_api_key = Prompt.ask("  Exa API key (or blank to skip)", default="").strip()

    # ── Step 3b: Firecrawl MCP API key (optional) ─────────────────
    console.print()
    console.print(Rule("[bold]Step 3b[/]  Firecrawl MCP API key (optional)", style="cyan"))
    console.print()
    if firecrawl_already:
        console.print("  [dim]Firecrawl MCP already configured in ~/.claude.json — skipping prompt.[/]")
        firecrawl_api_key = ""
    else:
        console.print("  [dim]Firecrawl scrapes JS-heavy pages, crawls whole domains, and[/]")
        console.print("  [dim]extracts structured data via LLM schemas. Highly complementary[/]")
        console.print("  [dim]to Exa: Exa finds URLs, Firecrawl extracts their full content.[/]")
        console.print("  [dim]Get a key at https://firecrawl.dev[/]")
        console.print()
        console.print("  [dim]Press Enter to skip — pipeline still works with `hyperresearch fetch`.[/]")
        console.print()
        firecrawl_api_key = Prompt.ask("  Firecrawl API key (or blank to skip)", default="").strip()

    # ── Execute ───────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold]Setting up", style="green"))
    console.print()

    from hyperresearch.core.agent_docs import _resolve_executable, inject_agent_docs
    from hyperresearch.core.exa_mcp import install_exa_mcp
    from hyperresearch.core.firecrawl_mcp import install_firecrawl_mcp
    from hyperresearch.core.reddit_mcp import install_reddit_mcp
    from hyperresearch.core.hooks import install_hooks
    from hyperresearch.core.vault import Vault, VaultError

    # Init vault
    try:
        vault = Vault.discover(root)
        console.print(f"  [dim]Vault:[/] {vault.root}")
    except VaultError:
        vault = Vault.init(root, name=vault_name)
        console.print(f"  [green]Vault created:[/] {vault.root}")

    # Write config — magic always on when crawl4ai is used
    magic = use_crawl4ai
    vault.config.web_provider = provider
    vault.config.web_profile = profile
    vault.config.web_magic = magic
    vault.config.name = vault_name
    vault.config.save(vault.config_path)

    # Inject CLAUDE.md
    hpr_path = _resolve_executable()
    doc_actions = inject_agent_docs(root)
    for action in doc_actions:
        console.print(f"  [green]Docs:[/] {action}")

    # Install Claude Code hook + skills + subagents
    hook_actions = install_hooks(root, hpr_path=hpr_path)
    for action in hook_actions:
        console.print(f"  [green]Hook:[/] {action}")
    if not hook_actions:
        console.print("  [dim]Hooks already installed[/]")

    # Install Exa MCP entry if the user supplied a key (or EXA_API_KEY is set).
    exa_status, exa_message = install_exa_mcp(exa_api_key or None)
    if exa_status == "installed":
        console.print(f"  [green]Exa MCP:[/] {exa_message}")
    elif exa_status == "already_configured":
        console.print(f"  [dim]Exa MCP:[/] {exa_message}")
    elif exa_status == "skipped_no_key":
        console.print("  [dim]Exa MCP:[/] skipped — re-run setup to add a key later")
    else:
        console.print(f"  [yellow]Exa MCP:[/] {exa_message}")

    # Install Reddit MCP entry — no API key required. Runs via uvx (Astral uv).
    reddit_status, reddit_message = install_reddit_mcp()
    if reddit_status == "installed":
        console.print(f"  [green]Reddit MCP:[/] {reddit_message}")
    elif reddit_status == "already_configured":
        console.print(f"  [dim]Reddit MCP:[/] {reddit_message}")
    elif reddit_status == "skipped_no_uvx":
        console.print(f"  [yellow]Reddit MCP:[/] {reddit_message}")
    else:
        console.print(f"  [yellow]Reddit MCP:[/] {reddit_message}")

    # Install Firecrawl MCP entry if the user supplied a key (or env var set).
    firecrawl_status, firecrawl_message = install_firecrawl_mcp(firecrawl_api_key or None)
    if firecrawl_status == "installed":
        console.print(f"  [green]Firecrawl MCP:[/] {firecrawl_message}")
    elif firecrawl_status == "already_configured":
        console.print(f"  [dim]Firecrawl MCP:[/] {firecrawl_message}")
    elif firecrawl_status == "skipped_no_key":
        console.print("  [dim]Firecrawl MCP:[/] skipped — re-run setup to add a key later")
    else:
        console.print(f"  [yellow]Firecrawl MCP:[/] {firecrawl_message}")

    # Install browser if needed
    if use_crawl4ai:
        _ensure_browser()

    # ── Summary ───────────────────────────────────────────────────
    console.print()
    profile_desc = profile or "none (public pages only)"

    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column(style="dim", width=12)
    summary.add_column()
    summary.add_row("Provider", f"[bold]{provider}[/]")
    summary.add_row("Profile", f"[bold]{profile_desc}[/]")
    summary.add_row("Stealth", "[bold]on[/]" if magic else "[dim]off[/]")
    summary.add_row("Platform", "[bold]Claude Code[/]")
    summary.add_row("CLI", f"[dim]{hpr_path}[/]")

    console.print(
        Panel(
            summary,
            title="[green bold]Setup complete[/]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()
    console.print(f"  [dim]Start researching:[/]  {hpr_path} fetch \"https://...\" --tag topic -j")
    console.print("  [dim]Change settings:[/]    hyperresearch config show")
    console.print("  [dim]Re-run setup:[/]       hyperresearch setup")
    console.print()


# ── Helpers ─────────────────────────────────────────────────────


def _read_mcp_servers() -> dict:
    """Return the mcpServers dict from ~/.claude.json, or {} if missing/unreadable."""
    import json
    target = Path.home() / ".claude.json"
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8")).get("mcpServers", {}) or {}
    except (json.JSONDecodeError, OSError):
        return {}


def _pick_existing_profile(profiles: list[str]) -> str:
    """Show a numbered list of profiles and let the user pick one."""
    console.print()
    table = Table(show_header=False, box=None, padding=(0, 2, 0, 4))
    table.add_column(style="bold cyan", width=3)
    table.add_column()
    for i, name in enumerate(profiles, 1):
        table.add_row(str(i), name)
    console.print(table)
    console.print()

    choices = [str(i) for i in range(1, len(profiles) + 1)]
    choice = Prompt.ask("  Select profile", choices=choices, default="1")
    selected = profiles[int(choice) - 1]
    console.print(f"  [green]Using profile:[/] {selected}")
    return selected


def _list_profiles() -> list[str]:
    """List existing crawl4ai browser profiles."""
    profiles_dir = Path.home() / ".crawl4ai" / "profiles"
    if not profiles_dir.exists():
        return []
    return sorted(
        d.name for d in profiles_dir.iterdir()
        if d.is_dir() and (d / "Default").exists()
    )


def _create_profile_interactive() -> str:
    """Walk the user through creating a crawl4ai browser profile."""
    import subprocess

    profile_name = Prompt.ask("  Profile name", default="research")

    console.print()
    console.print(
        Panel(
            "[bold]A browser window will open.[/]\n\n"
            "Log in to the sites you want hyperresearch to access:\n\n"
            "  [cyan]linkedin.com[/]       profiles, posts, company pages\n"
            "  [cyan]x.com / twitter.com[/] tweets, threads, profiles\n"
            "  [cyan]reddit.com[/]         full thread content, user profiles\n"
            "  [cyan]medium.com[/]         paywalled articles\n"
            "  [cyan]news sites[/]         any paywalled publications you subscribe to\n"
            "  [cyan]github.com[/]         private repos (if needed)\n\n"
            "Take your time. Log into as many sites as you want.\n"
            "[bold]When finished, press q in the terminal to save.[/]\n\n"
            "[dim]Sessions are saved permanently. You only do this once per site.[/]",
            title="[cyan bold]Login Profile Setup[/]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    ready = Confirm.ask("  Ready to open the browser?", default=True)
    if not ready:
        console.print("  [dim]Skipped. Run 'hyperresearch setup' later to create a profile.[/]")
        return ""

    try:
        result = subprocess.run(
            [sys.executable, "-c", f"""
import asyncio
from crawl4ai import BrowserProfiler
async def main():
    profiler = BrowserProfiler()
    path = await profiler.create_profile("{profile_name}")
    print(f"PROFILE_PATH={{path}}")
asyncio.run(main())
"""],
            capture_output=False,
            timeout=600,
        )
        if result.returncode == 0:
            console.print(f"  [green]Profile '{profile_name}' saved.[/]")
            return profile_name
        else:
            console.print("  [yellow]Profile creation exited. Run 'hyperresearch setup' to retry.[/]")
            return ""
    except subprocess.TimeoutExpired:
        console.print("  [yellow]Timed out. Run 'hyperresearch setup' to try again.[/]")
        return ""
    except Exception as e:
        console.print(f"  [red]Error:[/] {e}")
        console.print("  [dim]Run 'crwl profiles' manually to create a profile.[/]")
        return ""


def _check_crawl4ai() -> bool:
    try:
        import crawl4ai  # noqa: F401
        return True
    except ImportError:
        return False


def _ensure_browser() -> None:
    """Check if Chromium is installed, install if needed."""
    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        browser.close()
        pw.stop()
        console.print("  [dim]Browser ready[/]")
    except Exception:
        console.print("  [yellow]Installing Chromium browser...[/]")
        import subprocess

        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
                capture_output=True,
            )
            console.print("  [green]Chromium installed[/]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print(
                "  [red]Could not install browser automatically.[/]\n"
                "  Run: playwright install chromium"
            )
