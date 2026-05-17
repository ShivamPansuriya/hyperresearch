"""HTML helpers + title-cleaning logic for the research-notes UI surfaces.

Split out of server.py so the file stays under the 800-line convention.
Three pieces of value live here:

1. ``clean_title`` — fixes slug-cased / kebab-prefix / double-dash titles
   that the vault stored verbatim (e.g. "Interim report -- foo-bar" →
   "Interim report: Foo Bar").

2. ``is_stub_note`` — detects the auto-generated tag-stub notes that
   pollute the main listing ("Stub for [[...]]" summaries). The main
   "All notes" view filters them out by default.

3. ``render_grouped_index`` — replaces the old flat <ul> All Notes page
   with a grouped, badged, summary-promoted layout. Final reports get
   their own section, interim reports get their own section, etc.

The card CSS is appended to the main stylesheet by server.py via
``RESEARCH_CSS``.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterable
from dataclasses import dataclass

RESEARCH_CSS = """
.note-section { margin-top: 2rem; }
.note-section h2 { display: flex; align-items: baseline; gap: 0.6rem;
                   border-bottom: 1px solid var(--border); padding-bottom: 0.4rem;
                   margin-bottom: 1rem; color: var(--accent); }
.note-section h2 .count { font-size: 0.78rem; font-weight: 400;
                          color: var(--fg-dim); letter-spacing: 0; }
.note-section h2 .blurb { font-size: 0.78rem; font-weight: 400;
                          color: var(--fg-dim); margin-left: auto;
                          font-style: italic; }
.note-list { list-style: none; padding: 0; margin: 0; }
.note-row { display: block; padding: 0.85rem 1rem; margin-bottom: 0.6rem;
            background: var(--bg-alt); border: 1px solid var(--border);
            border-radius: 6px; transition: border-color .12s, transform .12s; }
.note-row:hover { border-color: var(--accent-light); transform: translateX(2px); }
.note-row a.note-title { font-weight: 600; color: var(--fg); border: none;
                         font-size: 0.95rem; }
.note-row a.note-title:hover { color: var(--accent); }
.note-row .row-meta { font-size: 0.72rem; color: var(--fg-dim);
                      margin-top: 4px; font-family: -apple-system, sans-serif;
                      display: flex; flex-wrap: wrap; gap: 0.6rem;
                      align-items: center; }
.note-row .row-meta .type-badge { background: var(--bg); border: 1px solid var(--border);
                                  padding: 1px 7px; border-radius: 10px;
                                  font-size: 0.68rem; color: var(--accent);
                                  text-transform: uppercase; letter-spacing: 0.04em; }
.note-row .row-meta .type-badge.final-report { background: var(--accent);
                                               color: var(--nav-heading);
                                               border-color: var(--accent); }
.note-row .row-meta .type-badge.interim { background: #e8d5b8;
                                          color: #5a3e24; border-color: #c4956a; }
.note-row .row-meta .status-badge { padding: 1px 7px; border-radius: 10px;
                                    font-size: 0.68rem; }
.note-row .row-meta .status-badge.evergreen { background: #d4e4c4; color: #4a6b2a; }
.note-row .row-meta .status-badge.review { background: #f5e6c8; color: #7a5a2a; }
.note-row .row-meta .status-badge.draft { background: var(--bg); color: var(--fg-dim);
                                          border: 1px solid var(--border); }
.note-row .row-meta .tag-chip { background: var(--tag-bg); color: var(--tag-fg);
                                padding: 1px 7px; border-radius: 3px;
                                font-size: 0.68rem; }
.note-row .row-meta .tag-chip a { color: inherit; border: none; }
.note-row .summary { margin-top: 5px; color: var(--fg); font-size: 0.85rem;
                     line-height: 1.45; }
.note-row .summary.missing { color: var(--fg-dim); font-style: italic; }

.section-toggle { display: inline-block; margin-left: auto; font-size: 0.78rem;
                  color: var(--accent); cursor: pointer; }

.notes-toolbar { display: flex; justify-content: space-between; align-items: center;
                 margin: 1rem 0; flex-wrap: wrap; gap: 0.8rem; }
.notes-toolbar .filter-info { font-size: 0.82rem; color: var(--fg-dim); }
.notes-toolbar a.toggle { font-size: 0.82rem; color: var(--link);
                          padding: 4px 10px; border: 1px solid var(--border);
                          border-radius: 4px; }
.notes-toolbar a.toggle:hover { border-color: var(--accent); }

/* Meta header on individual note pages */
.note-meta-header { background: var(--bg-alt); border: 1px solid var(--border);
                    border-radius: 6px; padding: 0.9rem 1rem; margin-bottom: 1.2rem;
                    display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;
                    font-size: 0.78rem; color: var(--fg-dim);
                    font-family: -apple-system, sans-serif; }
.note-meta-header .type-pill { background: var(--accent); color: var(--nav-heading);
                               padding: 2px 9px; border-radius: 10px;
                               font-size: 0.7rem; text-transform: uppercase;
                               letter-spacing: 0.04em; }
.note-meta-header .type-pill.interim { background: #c4956a; }
.note-meta-header .type-pill.note { background: var(--bg); color: var(--accent);
                                    border: 1px solid var(--border); }
.note-meta-header .status-pill { padding: 2px 9px; border-radius: 10px;
                                 font-size: 0.7rem; }
.note-meta-header .status-pill.evergreen { background: #d4e4c4; color: #4a6b2a; }
.note-meta-header .status-pill.review { background: #f5e6c8; color: #7a5a2a; }
.note-meta-header .status-pill.draft { background: var(--bg); color: var(--fg-dim);
                                       border: 1px solid var(--border); }
.note-meta-header .tag-pill { background: var(--tag-bg); color: var(--tag-fg);
                              padding: 2px 9px; border-radius: 3px; font-size: 0.7rem; }
.note-meta-header .tag-pill a { color: inherit; border: none; }
.note-meta-header .word-count { margin-left: auto; }
"""


# ---------- Title cleaning ----------

_INTERIM_PREFIX = re.compile(r"^(interim\s+report)\s*[-—:]+\s*", re.IGNORECASE)
_FINAL_PREFIX = re.compile(r"^(final\s+report)\s*[-—:]+\s*", re.IGNORECASE)
_HASH_SUFFIX = re.compile(r"[\s-]+[0-9a-f]{6,}$")


def clean_title(raw: str) -> str:
    """Normalise vault titles for display.

    Examples:
        "Interim report -- audit-logging-paradigm-ferpa-vs-naac"
          -> "Interim report: Audit-Logging Paradigm (FERPA vs NAAC)"
        "Interim Adddrop Formality Comparison Usa Vs India"
          -> "Interim Adddrop Formality Comparison (USA vs India)"
        "final_report_erp-india-usa-47d42c"
          -> "ERP India vs USA"
    """
    if not raw:
        return ""

    title = raw.strip()

    # Drop the trailing 6+ char hex hash that the vault appends to slugs.
    title = _HASH_SUFFIX.sub("", title)

    # Normalise the "Interim report -- " / "Final report -- " prefix.
    m = _INTERIM_PREFIX.match(title)
    if m:
        rest = title[m.end():].strip()
        return f"Interim report: {_humanise_slug(rest)}"
    m = _FINAL_PREFIX.match(title)
    if m:
        rest = title[m.end():].strip()
        return f"Final report: {_humanise_slug(rest)}"

    # Generic cleanup: replace "Usa Vs India" -> "USA vs India", etc.
    return _humanise(title)


_ACRONYMS = {
    "usa", "uk", "us", "eu", "erp", "sis", "lms", "ferpa", "naac",
    "abha", "cghs", "dpdpa", "nsp", "sap", "iam", "api", "ui", "ux",
    "ai", "ml", "llm", "cbcs", "gpa", "cap", "josaa", "json", "html",
}
_CAMEL_CASE_RE = re.compile(r"[a-z][A-Z]")


def _humanise_word(word: str) -> str:
    """Normalise one token, preserving CamelCase and respecting acronyms."""
    if not word:
        return word
    low = word.lower()
    if low in _ACRONYMS:
        return low.upper()
    if low == "vs":
        return "vs"
    # Preserve genuine CamelCase / PascalCase tokens like 'ManageArk', 'iOS'.
    # Detected by an internal lowercase-then-uppercase transition.
    if _CAMEL_CASE_RE.search(word):
        return word
    # Preserve ALL-CAPS acronyms not in our list (e.g. 'NAAC', 'III').
    if word.isupper() and len(word) > 1:
        return word
    # Everything else: standard Title-case (first upper, rest lower).
    return word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()


def _humanise_slug(slug: str) -> str:
    """Turn a kebab/space-separated slug into a human-readable phrase."""
    # Split on dashes, underscores AND whitespace so titles that mix them
    # (e.g. 'ManageArk India-USA Dual-Region') normalise word-by-word.
    parts = re.split(r"[-_\s]+", slug)
    return " ".join(_humanise_word(p) for p in parts if p)


def _humanise(title: str) -> str:
    """Apply acronym + CamelCase preservation to an already-spaced title."""
    return " ".join(_humanise_word(p) for p in title.split())


# ---------- Stub detection ----------

_STUB_SUMMARY = re.compile(r"^stub for \[\[", re.IGNORECASE)


def is_stub_note(summary: str | None) -> bool:
    """True when the note is an auto-generated tag/cross-link stub."""
    if not summary:
        return False
    return bool(_STUB_SUMMARY.match(summary.strip()))


# ---------- Group renderer ----------

@dataclass(frozen=True)
class NoteRow:
    """Lightweight projection of a notes table row for the index renderer."""

    id: str
    raw_title: str
    type: str
    status: str
    summary: str
    word_count: int
    tags: list[str]


_TYPE_SECTIONS = [
    ("final-report", "Final reports", "Polished synthesis output from /hyperresearch runs"),
    ("interim", "Interim reports", "Depth-investigation notes that fed the final reports"),
    ("note", "Other notes", "Source notes, web fetches, and cross-link stubs"),
]


def _classify(row: NoteRow) -> str:
    """Map a vault row to its display section."""
    lowered_id = row.id.lower()
    if row.type == "final-report":
        return "final-report"
    if row.type == "interim":
        return "interim"
    if lowered_id.startswith("final_report_") or row.raw_title.lower().startswith("final report"):
        return "final-report"
    return "note"


def _esc(s: str | None) -> str:
    return html.escape(s) if s else ""


def _render_row(row: NoteRow, section_key: str) -> str:
    pretty_title = clean_title(row.raw_title)
    tag_chips = "".join(
        f'<span class="tag-chip"><a href="/tag/{_esc(t)}">{_esc(t)}</a></span>'
        for t in row.tags[:5]
    )
    type_label = (
        "Final report" if section_key == "final-report"
        else "Interim" if section_key == "interim"
        else "Note"
    )
    type_badge = (
        f'<span class="type-badge {section_key}">{type_label}</span>'
    )
    status_badge = (
        f'<span class="status-badge {_esc(row.status)}">{_esc(row.status)}</span>'
    )
    summary_html: str
    if row.summary:
        summary_html = f'<div class="summary">{_esc(row.summary)}</div>'
    else:
        summary_html = '<div class="summary missing">(no summary)</div>'
    meta = (
        '<div class="row-meta">'
        f'{type_badge}{status_badge}{tag_chips}'
        f'<span style="margin-left:auto">{row.word_count} words</span>'
        '</div>'
    )
    return (
        '<li class="note-row">'
        f'<a class="note-title" href="/note/{_esc(row.id)}">{_esc(pretty_title)}</a>'
        f'{summary_html}{meta}'
        '</li>'
    )


def render_grouped_index(
    rows: Iterable[NoteRow],
    *,
    show_stubs: bool = False,
    total_count: int | None = None,
) -> str:
    """Render the grouped All Notes page.

    Args:
        rows: notes from the vault (without ``type='index'`` — those are
            tag pages, not content).
        show_stubs: when False, auto-generated stub notes are hidden.
        total_count: passed through to the toolbar so users see how many
            were filtered.
    """
    all_rows = list(rows)
    if not show_stubs:
        visible = [r for r in all_rows if not is_stub_note(r.summary)]
    else:
        visible = all_rows

    sections: dict[str, list[NoteRow]] = {key: [] for key, _, _ in _TYPE_SECTIONS}
    for row in visible:
        sections.setdefault(_classify(row), []).append(row)

    # Sort within each section: final-reports + interim by word_count desc
    # (longer = more substantive), notes alphabetically.
    for key, rows_in in sections.items():
        if key in ("final-report", "interim"):
            rows_in.sort(key=lambda r: (-r.word_count, r.raw_title.lower()))
        else:
            rows_in.sort(key=lambda r: r.raw_title.lower())

    hidden = (total_count or len(all_rows)) - len(visible)
    toolbar_bits: list[str] = [
        f'<span class="filter-info">{len(visible)} notes shown</span>'
    ]
    if hidden > 0:
        if show_stubs:
            toolbar_bits.append('<a class="toggle" href="/notes">Hide stub notes</a>')
        else:
            toolbar_bits.append(
                f'<a class="toggle" href="/notes?show_stubs=1">'
                f'Show {hidden} stub note(s)</a>'
            )

    parts: list[str] = [
        '<h1>All notes</h1>',
        f'<div class="notes-toolbar">{" ".join(toolbar_bits)}</div>',
    ]

    rendered_any = False
    for key, label, blurb in _TYPE_SECTIONS:
        bucket = sections.get(key, [])
        if not bucket:
            continue
        rendered_any = True
        rows_html = "".join(_render_row(r, key) for r in bucket)
        parts.append(
            f'<div class="note-section">'
            f'<h2>{_esc(label)} '
            f'<span class="count">({len(bucket)})</span>'
            f'<span class="blurb">{_esc(blurb)}</span></h2>'
            f'<ul class="note-list">{rows_html}</ul>'
            '</div>'
        )

    if not rendered_any:
        parts.append('<p style="color:var(--fg-dim)">No notes match.</p>')
    return "".join(parts)


# ---------- Per-note meta header ----------

def render_note_meta_header(
    *,
    title: str,
    note_type: str,
    status: str,
    tags: Iterable[str],
    word_count: int,
) -> str:
    """Replace the legacy one-line .meta block with a richer card."""
    type_label = (
        "Final report" if note_type == "note" and title.lower().startswith("final report")
        else "Interim" if note_type == "interim"
        else note_type.capitalize() if note_type else "Note"
    )
    type_cls = (
        "interim" if note_type == "interim" else "note"
    )
    tag_pills = "".join(
        f'<span class="tag-pill"><a href="/tag/{_esc(t)}">{_esc(t)}</a></span>'
        for t in list(tags)[:8]
    )
    return (
        '<div class="note-meta-header">'
        f'<span class="type-pill {type_cls}">{_esc(type_label)}</span>'
        f'<span class="status-pill {_esc(status)}">{_esc(status)}</span>'
        f'{tag_pills}'
        f'<span class="word-count">{word_count} words</span>'
        '</div>'
    )
