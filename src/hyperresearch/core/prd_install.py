"""PRD extension installer.

Installs the 12 hyperresearch-prd step skills and 9 PRD subagents to a
target project's `.claude/` directory so the `/hyperresearch-prd` slash
command becomes available to Claude Code.

Mirrors the layout used by `core/hooks.py` for the research pipeline,
but kept as a separate module so the extension stays drop-in and does
not entangle with the core hyperresearch installer.
"""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

# Step skills that constitute the PRD pipeline. Order matters only for
# documentation purposes; the entry router skill (`hyperresearch-prd`)
# drives sequencing at runtime.
PRD_STEP_SKILLS: list[str] = [
    "hyperresearch-prd",                                  # entry router
    "hyperresearch-prd-17-initialize",
    "hyperresearch-prd-18-product-inventory",
    "hyperresearch-prd-19-feature-decomposition",
    "hyperresearch-prd-20-integration-map",
    "hyperresearch-prd-21-personas-stories",
    "hyperresearch-prd-22-flows-entities",
    "hyperresearch-prd-23-triple-draft",
    "hyperresearch-prd-24-synthesize",
    "hyperresearch-prd-25-critics",
    "hyperresearch-prd-26-patcher",
    "hyperresearch-prd-27-polish",
    "hyperresearch-prd-28-readability-audit",
    "hyperresearch-prd-29-author-diagrams",
    "hyperresearch-prd-30-render-html",
]

# Subagents that the step skills spawn. Each lives in
# `hyperresearch/agents/prd/<name>.md` inside the package.
PRD_SUBAGENTS: list[str] = [
    "prd-draft-orchestrator",
    "prd-synthesizer",
    "prd-business-value-critic",
    "prd-scope-creep-critic",
    "prd-integration-feasibility-critic",
    "prd-instruction-critic",
    "prd-patcher",
    "prd-polish-auditor",
    "prd-readability-recommender",
]


def _package_skills_dir() -> Path:
    """Resolve the in-package skills directory."""
    return Path(str(resources.files("hyperresearch") / "skills"))


def _package_agents_dir() -> Path:
    """Resolve the in-package PRD agents directory."""
    return Path(str(resources.files("hyperresearch") / "agents" / "prd"))


def install_prd_extension(target: Path) -> dict[str, list[str]]:
    """Install PRD skills and agents into `<target>/.claude/`.

    Returns a dict with two lists: `skills_installed` and `agents_installed`.
    Both contain the absolute paths written. Idempotent: re-running on an
    already-installed target overwrites the files (so updates flow through).
    """
    target = target.resolve()
    skills_root = target / ".claude" / "skills"
    agents_root = target / ".claude" / "agents"
    skills_root.mkdir(parents=True, exist_ok=True)
    agents_root.mkdir(parents=True, exist_ok=True)

    pkg_skills = _package_skills_dir()
    pkg_agents = _package_agents_dir()

    skills_installed: list[str] = []
    for skill_name in PRD_STEP_SKILLS:
        src = pkg_skills / f"{skill_name}.md"
        if not src.exists():
            continue
        dst_dir = skills_root / skill_name
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / "SKILL.md"
        shutil.copyfile(src, dst)
        skills_installed.append(str(dst))

    agents_installed: list[str] = []
    for agent_name in PRD_SUBAGENTS:
        src = pkg_agents / f"{agent_name}.md"
        if not src.exists():
            continue
        dst = agents_root / f"{agent_name}.md"
        shutil.copyfile(src, dst)
        agents_installed.append(str(dst))

    return {
        "skills_installed": skills_installed,
        "agents_installed": agents_installed,
    }


def install_prd_extension_global(home: Path | None = None) -> dict[str, list[str]]:
    """Install PRD skills and agents into the user-level Claude Code dirs
    (`~/.claude/skills/` and `~/.claude/agents/`), so the `/hyperresearch-prd`
    slash command is available globally.
    """
    base = (home or Path.home()).resolve()
    return install_prd_extension(base)


def prd_extension_status(target: Path) -> dict[str, dict[str, bool]]:
    """Return a snapshot of which PRD skills and agents are installed at
    `<target>/.claude/`.
    """
    target = target.resolve()
    skills_root = target / ".claude" / "skills"
    agents_root = target / ".claude" / "agents"
    return {
        "skills": {
            name: (skills_root / name / "SKILL.md").exists()
            for name in PRD_STEP_SKILLS
        },
        "agents": {
            name: (agents_root / f"{name}.md").exists()
            for name in PRD_SUBAGENTS
        },
    }
