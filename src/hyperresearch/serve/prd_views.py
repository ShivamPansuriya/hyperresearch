"""HTML view helpers for PRD and feature-view pages.

Separated from ``server.py`` to keep each file focused (per the
project's <800 lines convention). All functions return HTML fragments
that ``server.py`` wraps in the standard nav/main layout via ``_send``.

Cross-link contract:
- A "feature" is identified by ``prd_tag``.
- Each feature can link to one research note (via PRD frontmatter's
  ``research_final_report_path``) and may include a feature-request body.
- The reverse link (research note -> PRDs) is computed by
  ``prd_scanner.prds_for_research``.
"""

from __future__ import annotations

import html
from collections.abc import Iterable

from hyperresearch.serve.prd_scanner import FeatureGroup, PrdRecord, read_prd_body
from hyperresearch.serve.renderer import render_markdown

# CSS additions appended to the main stylesheet by server.py.
PRD_CSS = """
.feature-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 1.2rem; margin-top: 1.5rem; }
.feature-card { background: var(--bg-alt); border: 1px solid var(--border);
                border-radius: 8px; padding: 1.1rem 1.2rem; transition: transform .12s ease,
                box-shadow .12s ease; }
.feature-card:hover { transform: translateY(-2px);
                      box-shadow: 0 4px 12px rgba(60,40,20,0.08); }
.feature-card h3 { margin: 0 0 0.4rem 0; font-size: 1rem; color: var(--fg); }
.feature-card h3 a { color: inherit; border-bottom: none; }
.feature-card h3 a:hover { color: var(--accent); }
.feature-card .snippet { color: var(--fg-dim); font-size: 0.85rem;
                         line-height: 1.45; margin: 0.4rem 0 0.6rem 0; }
.feature-card .badges { display: flex; flex-wrap: wrap; gap: 5px;
                        margin-top: 0.5rem; font-size: 0.7rem; }
.feature-card .badge { background: var(--bg); border: 1px solid var(--border);
                       padding: 2px 7px; border-radius: 10px; color: var(--accent); }
.feature-card .badge.tier-light { color: #6b8a3e; border-color: #b8c8a0; }
.feature-card .badge.tier-full  { color: #8b4226; border-color: #c4956a; }
.feature-card .links { font-size: 0.82rem; margin-top: 0.7rem; display: flex;
                       gap: 0.8rem; align-items: center; }
.feature-card .links a { font-weight: 500; }
.feature-card .links .sep { color: var(--fg-dim); }
.feature-card .empty-research { color: var(--fg-dim); font-style: italic; }

.feature-detail { display: grid; grid-template-columns: 1fr;
                  gap: 1.5rem; }
.feature-detail .request-block { background: var(--bg-alt); border-left: 4px solid var(--accent);
                                 border-radius: 0 6px 6px 0; padding: 1rem 1.2rem;
                                 white-space: pre-wrap; font-size: 0.9rem;
                                 color: var(--fg); }
.feature-detail .request-block h3 { margin: 0 0 0.5rem 0; font-size: 0.78rem;
                                    text-transform: uppercase; letter-spacing: 0.06em;
                                    color: var(--accent); }
.feature-detail .cross-links { display: flex; gap: 1.2rem; flex-wrap: wrap;
                               padding: 0.8rem 1rem; background: var(--bg-alt);
                               border: 1px dashed var(--border); border-radius: 6px;
                               font-size: 0.85rem; }
.feature-detail .cross-links a { font-weight: 500; }
.feature-detail .cross-links .pill { background: var(--bg); border: 1px solid var(--border);
                                     border-radius: 14px; padding: 4px 12px; }

.related-prds { background: var(--bg-alt); border: 1px solid var(--border);
                border-radius: 6px; padding: 1rem; margin-top: 2rem; }
.related-prds h3 { font-size: 0.85rem; margin-bottom: 0.5rem; color: var(--accent); }
.related-prds li { font-size: 0.85rem; margin: 0.25rem 0; }
.related-prds .meta { color: var(--fg-dim); font-size: 0.78rem; }

.empty-state { text-align: center; padding: 3rem 1rem; color: var(--fg-dim); }
.empty-state code { background: var(--code-bg); padding: 3px 8px; border-radius: 3px;
                    color: var(--accent); font-size: 0.85rem; }
.empty-state h2 { color: var(--fg); border: none; margin-bottom: 0.6rem; }

.toc-sticky { float: right; width: 220px; margin-left: 1.5rem; margin-bottom: 1rem;
              padding: 0.8rem 0.9rem; background: var(--bg-alt);
              border: 1px solid var(--border); border-radius: 6px;
              font-size: 0.82rem; position: sticky; top: 1rem; max-height: 80vh;
              overflow-y: auto; }
.toc-sticky h4 { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
                 color: var(--accent); margin-bottom: 0.4rem; }
.toc-sticky ul { list-style: none; margin: 0; padding: 0; }
.toc-sticky li { margin: 0.15rem 0; }
.toc-sticky li.h3 { padding-left: 0.7rem; }
.toc-sticky a { border: none; color: var(--link); }
.toc-sticky a:hover { color: var(--accent); }
@media (max-width: 1100px) { .toc-sticky { display: none; } }
"""


def _esc(value: str | None) -> str:
    return html.escape(value) if value else ""


def _tier_badge(tier: str | None) -> str:
    if not tier:
        return ""
    cls = "tier-light" if tier.lower() == "light" else "tier-full"
    return f'<span class="badge {cls}">{_esc(tier)}</span>'


def _modality_badge(modality: str | None) -> str:
    if not modality:
        return ""
    return f'<span class="badge">{_esc(modality)}</span>'


def render_empty_features() -> str:
    return (
        '<h1>Features</h1>'
        '<div class="empty-state">'
        '<h2>No PRDs yet</h2>'
        '<p>This vault has no PRDs. Run <code>/hyperresearch</code> first, '
        'then <code>/hyperresearch-prd</code> to generate a feature PRD '
        'that links back to its research.</p>'
        '</div>'
    )


def render_features_index(groups: Iterable[FeatureGroup]) -> str:
    groups = list(groups)
    if not groups:
        return render_empty_features()

    cards: list[str] = []
    for group in groups:
        snippet_html = (
            f'<p class="snippet">{_esc(group.feature_request_snippet)}</p>'
            if group.feature_request_snippet
            else ""
        )
        research_link = (
            f'<a href="/note/{_esc(group.research_note_id)}">Research →</a>'
            if group.research_note_id
            else '<span class="empty-research">No linked research</span>'
        )
        prd_link = f'<a href="/prd/{_esc(group.tag)}">PRD →</a>'
        badges = _tier_badge(group.prd.tier) + _modality_badge(group.prd.modality)
        cards.append(
            '<div class="feature-card">'
            f'<h3><a href="/feature/{_esc(group.tag)}">{_esc(group.title)}</a></h3>'
            f'{snippet_html}'
            f'<div class="badges">{badges}</div>'
            f'<div class="links">{research_link}'
            f'<span class="sep">·</span>{prd_link}</div>'
            '</div>'
        )

    return (
        '<h1>Features</h1>'
        f'<p style="color:var(--fg-dim);font-size:0.9rem">{len(groups)} feature(s). '
        'Each card links research and PRD for one feature instance.</p>'
        f'<div class="feature-grid">{"".join(cards)}</div>'
    )


def render_prds_index(records: list[PrdRecord]) -> str:
    if not records:
        return render_empty_features()

    items: list[str] = []
    for record in records:
        meta_bits: list[str] = []
        if record.tier:
            meta_bits.append(f"tier: {_esc(record.tier)}")
        if record.modality:
            meta_bits.append(f"format: {_esc(record.modality)}")
        meta_bits.append(f"{record.word_count} words")
        meta = " · ".join(meta_bits)
        items.append(
            f'<li><a href="/prd/{_esc(record.prd_tag)}">{_esc(record.title)}</a>'
            f' <span style="color:var(--fg-dim);font-size:0.82rem">— {meta}</span></li>'
        )
    return (
        '<h1>All PRDs</h1>'
        f'<p>{len(records)} PRD(s), newest first.</p>'
        f'<ul>{"".join(items)}</ul>'
    )


def _build_toc(markdown_body: str) -> str:
    """Build a sticky table of contents from H2/H3 headings in raw markdown."""
    items: list[str] = []
    in_code = False
    for line in markdown_body.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        stripped = line.lstrip()
        level = 0
        if stripped.startswith("## ") and not stripped.startswith("### "):
            level = 2
            text = stripped[3:].strip()
        elif stripped.startswith("### "):
            level = 3
            text = stripped[4:].strip()
        else:
            continue
        slug = "h-" + "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
        cls = "h2" if level == 2 else "h3"
        items.append(f'<li class="{cls}"><a href="#{slug}">{_esc(text)}</a></li>')
    if not items:
        return ""
    return (
        '<aside class="toc-sticky">'
        '<h4>On this page</h4>'
        f'<ul>{"".join(items)}</ul>'
        '</aside>'
    )


def _inject_heading_anchors(rendered_html: str, markdown_body: str) -> str:
    """Add id attributes to <h2>/<h3> so the TOC anchors work."""
    slugs: list[tuple[str, str]] = []
    in_code = False
    for line in markdown_body.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        stripped = line.lstrip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            text = stripped[3:].strip()
            tag = "h2"
        elif stripped.startswith("### "):
            text = stripped[4:].strip()
            tag = "h3"
        else:
            continue
        slug = "h-" + "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
        slugs.append((tag, slug))

    out = rendered_html
    for tag, slug in slugs:
        needle = f"<{tag}>"
        idx = out.find(needle)
        if idx == -1:
            continue
        out = out[:idx] + f'<{tag} id="{slug}">' + out[idx + len(needle):]
    return out


def render_prd_detail(record: PrdRecord) -> tuple[str, str]:
    """Return (title, body_html) for the PRD detail page."""
    body_md = read_prd_body(record)
    body_html = render_markdown(body_md)
    body_html = _inject_heading_anchors(body_html, body_md)
    toc = _build_toc(body_md)

    research_link_html = (
        f'<a href="/note/{_esc(record.research_note_id)}" class="pill">'
        f'← Research: {_esc(record.research_tag or record.research_note_id)}</a>'
        if record.research_note_id
        else ""
    )
    feature_link = f'<a href="/feature/{_esc(record.prd_tag)}" class="pill">Feature view ↗</a>'
    badges = _tier_badge(record.tier) + _modality_badge(record.modality)
    header = (
        f'<div class="meta">{badges}'
        f'<span>{record.word_count} words</span></div>'
        f'<div class="feature-detail"><div class="cross-links">{research_link_html}{feature_link}</div></div>'
    )
    full = f"{toc}{header}{body_html}"
    return record.title, full


def render_feature_detail(record: PrdRecord) -> tuple[str, str]:
    """Side-by-side request + research + PRD inline rendering."""
    body_md = read_prd_body(record)
    body_html = render_markdown(body_md)
    body_html = _inject_heading_anchors(body_html, body_md)
    toc = _build_toc(body_md)

    request_html = (
        f'<div class="request-block"><h3>Feature request</h3>{_esc(record.feature_request)}</div>'
        if record.feature_request
        else ""
    )

    cross_links: list[str] = []
    if record.research_note_id:
        cross_links.append(
            f'<a href="/note/{_esc(record.research_note_id)}" class="pill">'
            f'Read research →</a>'
        )
    cross_links.append(
        f'<a href="/prd/{_esc(record.prd_tag)}" class="pill">Open PRD page →</a>'
    )

    badges = _tier_badge(record.tier) + _modality_badge(record.modality)
    body = (
        f'<h1>{_esc(record.title)}</h1>'
        f'<div class="meta">{badges}<span>{record.word_count} words</span></div>'
        '<div class="feature-detail">'
        f'<div class="cross-links">{"".join(cross_links)}</div>'
        f'{request_html}'
        '</div>'
        f'{toc}'
        '<h2 id="prd-content">PRD</h2>'
        f'{body_html}'
    )
    return record.title, body


def render_related_prds_panel(records: list[PrdRecord]) -> str:
    """Sidebar fragment listing PRDs that reference the current research note."""
    if not records:
        return ""
    items: list[str] = []
    for record in records:
        meta_bits: list[str] = []
        if record.tier:
            meta_bits.append(_esc(record.tier))
        if record.modality:
            meta_bits.append(_esc(record.modality))
        meta = " · ".join(meta_bits)
        meta_html = f'<div class="meta">{meta}</div>' if meta else ""
        items.append(
            f'<li><a href="/feature/{_esc(record.prd_tag)}">{_esc(record.title)}</a>'
            f'{meta_html}</li>'
        )
    return (
        '<div class="related-prds">'
        f'<h3>Linked PRDs ({len(records)})</h3>'
        f'<ul>{"".join(items)}</ul>'
        '</div>'
    )
