"""Scanner for PRD output files in <vault_root>/prd/.

PRDs live OUTSIDE the vault SQLite DB (they are free-floating markdown
files produced by the hyperresearch-PRD pipeline). This module reads
them from disk and builds a lightweight in-memory index with cross-links
to research notes via the ``research_final_report_path`` frontmatter
field.

Read paths:
- ``<root>/prd/notes/final_prd_<tag>.md``    — primary PRD output
- ``<root>/prd/request-<tag>.md``            — canonical feature request
- ``<root>/prd/prd-decomposition.json``      — pipeline metadata (best-effort)
- ``<root>/prd/scaffold.md``                 — planning context (best-effort)

The scanner is read-only and safe to invoke per request (cheap; one
filesystem walk over a small directory). For very large vaults a future
caller can wrap it in functools.lru_cache or an mtime-based cache.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_FINAL_PRD_RE = re.compile(r"^final_prd_(.+)\.md$")
_FINAL_REPORT_RE = re.compile(r"final_report_(.+?)(?:\.md)?$")


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a minimal YAML frontmatter block. Returns empty dict if absent.

    Intentionally simple: scalar key/value lines only. We don't pull in PyYAML
    because the rest of the serve module is stdlib-only.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    out: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, val = line.partition(":")
        out[key.strip()] = val.strip().strip("'\"")
    return out


def _first_h1(text: str) -> str | None:
    body = _FRONTMATTER_RE.sub("", text, count=1)
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _research_note_id(research_path: str | None) -> str | None:
    if not research_path:
        return None
    stem = Path(research_path).stem
    return stem or None


@dataclass(frozen=True)
class PrdRecord:
    prd_tag: str
    path: Path
    title: str
    research_path: str | None
    research_note_id: str | None
    research_tag: str | None
    feature_request: str | None
    feature_request_path: Path | None
    modality: str | None
    tier: str | None
    word_count: int
    mtime: float


@dataclass(frozen=True)
class FeatureGroup:
    """A feature instance: one PRD plus its driving research + request."""

    tag: str
    title: str
    prd: PrdRecord
    research_note_id: str | None
    feature_request_snippet: str | None


def _load_request(vault_root: Path, prd_tag: str) -> tuple[str | None, Path | None]:
    request_path = vault_root / "prd" / f"request-{prd_tag}.md"
    if not request_path.exists():
        return None, None
    try:
        text = request_path.read_text(encoding="utf-8")
    except OSError:
        return None, None
    body = _FRONTMATTER_RE.sub("", text, count=1).strip()
    return body or None, request_path


def _load_decomposition(vault_root: Path) -> dict:
    """Return PRD decomposition JSON if present, else empty dict.

    The decomposition holds tier_rationale, response_format, etc. We use it
    as a fallback for tier/modality when not in PRD frontmatter.
    """
    decomp_path = vault_root / "prd" / "prd-decomposition.json"
    if not decomp_path.exists():
        return {}
    try:
        return json.loads(decomp_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def scan_prds(vault_root: Path) -> list[PrdRecord]:
    """Walk ``<vault_root>/prd/`` and return all PRD records found.

    Sorted newest-first by file mtime.
    """
    prd_dir = vault_root / "prd"
    if not prd_dir.exists():
        return []

    decomposition = _load_decomposition(vault_root)
    fallback_tier = decomposition.get("pipeline_tier")
    fallback_modality = decomposition.get("response_format")

    records: list[PrdRecord] = []
    seen: set[str] = set()

    for path in prd_dir.rglob("final_prd_*.md"):
        if not path.is_file():
            continue
        name_match = _FINAL_PRD_RE.match(path.name)
        if not name_match:
            continue
        prd_tag = name_match.group(1)
        if prd_tag in seen:
            continue
        seen.add(prd_tag)

        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        front = _parse_frontmatter(text)
        title = front.get("title") or _first_h1(text) or f"PRD: {prd_tag}"
        research_path = front.get("research_final_report_path") or None
        research_tag = None
        if research_path:
            report_match = _FINAL_REPORT_RE.search(research_path)
            if report_match:
                research_tag = report_match.group(1)

        feature_request, request_path = _load_request(vault_root, prd_tag)
        word_count = len(text.split())

        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0

        records.append(
            PrdRecord(
                prd_tag=prd_tag,
                path=path,
                title=title,
                research_path=research_path,
                research_note_id=_research_note_id(research_path),
                research_tag=research_tag,
                feature_request=feature_request,
                feature_request_path=request_path,
                modality=front.get("response_format") or fallback_modality,
                tier=front.get("pipeline_tier") or fallback_tier,
                word_count=word_count,
                mtime=mtime,
            )
        )

    records.sort(key=lambda r: r.mtime, reverse=True)
    return records


def prds_for_research(records: list[PrdRecord], research_note_id: str) -> list[PrdRecord]:
    """Return PRDs whose research_final_report_path resolves to a research note id."""
    matches: list[PrdRecord] = []
    for record in records:
        if record.research_note_id == research_note_id:
            matches.append(record)
            continue
        if record.research_path and research_note_id in record.research_path:
            matches.append(record)
    return matches


def feature_groups(records: list[PrdRecord]) -> list[FeatureGroup]:
    """One feature group per PRD — each /hyperresearch-prd run is per-feature."""
    groups: list[FeatureGroup] = []
    for record in records:
        snippet: str | None = None
        if record.feature_request:
            text = record.feature_request.strip()
            snippet = text if len(text) <= 280 else text[:277].rstrip() + "..."
        groups.append(
            FeatureGroup(
                tag=record.prd_tag,
                title=record.title,
                prd=record,
                research_note_id=record.research_note_id,
                feature_request_snippet=snippet,
            )
        )
    return groups


def find_prd(records: list[PrdRecord], prd_tag: str) -> PrdRecord | None:
    for record in records:
        if record.prd_tag == prd_tag:
            return record
    return None


def read_prd_body(record: PrdRecord) -> str:
    """Return the PRD body with frontmatter stripped."""
    try:
        text = record.path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return _FRONTMATTER_RE.sub("", text, count=1).strip()
