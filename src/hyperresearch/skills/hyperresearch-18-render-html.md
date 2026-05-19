---
name: hyperresearch-18-render-html
description: >
  Step 18 (FINAL) of the hyperresearch V8 pipeline. Renders the final report
  markdown — now enriched with Mermaid diagrams by step 17 — into a single
  self-contained HTML file the user can open directly. Primary path:
  invoke the baoyu-markdown-to-html skill if installed. Fallback path:
  pure-Python markdown rendering with Mermaid.js loaded from CDN. The HTML
  page is the user-facing deliverable. Runs for ALL tiers.
---

# Step 18 — Render the final report to HTML (FINAL STEP)

**Tier gate:** Runs for ALL tiers. The HTML is the final user-facing artifact; the markdown is the source of truth, the HTML is what the user actually opens.

**Goal:** turn `research/notes/final_report_<vault_tag>.md` into a single standalone HTML file (`research/notes/final_report_<vault_tag>.html`) that:
- Renders every Mermaid block (authored in step 17) as inline SVG.
- Looks clean and is readable on its own.
- Is self-contained — opening the `.html` file directly in a browser shows everything, no server, no missing assets.

---

## Recover state

Read these inputs:
- `research/scaffold.md` — `vault_tag`
- `research/notes/final_report_<vault_tag>.md` — the diagram-enriched final report (output of step 17)

---

## Step 18.1 — Detect rendering path

You have two paths. Detect which is available, prefer baoyu.

**Path A — baoyu (preferred).** Check if the `baoyu-markdown-to-html` skill is installed:

```bash
test -f .claude/skills/baoyu-markdown-to-html/SKILL.md && echo "project" \
  || test -f ~/.claude/skills/baoyu-markdown-to-html/SKILL.md && echo "user" \
  || echo "missing"
```

If `project` or `user`, baoyu is available — use Path A.

**Path B — Python fallback.** If baoyu isn't installed, use Path B. No additional dependencies — Python's stdlib + an inline Mermaid.js CDN script is enough.

---

## Step 18.2A — Baoyu render path

If Path A is selected:

1. Invoke the baoyu skill via the `Skill` tool:

   ```
   Skill(
     skill: "baoyu-markdown-to-html",
     args: "Convert research/notes/final_report_<vault_tag>.md to HTML.
            Output path: research/notes/final_report_<vault_tag>.html.
            Theme: modern.
            Render Mermaid blocks as inline SVG.
            Make the page self-contained (inline CSS, embedded fonts where possible)."
   )
   ```

2. When the baoyu skill returns, verify the output file exists at the expected path. If baoyu wrote it elsewhere (some versions default to a relative `out/` folder), move it to `research/notes/final_report_<vault_tag>.html` using `mv`.

3. **Diagram check.** Read the first 500 lines of the produced HTML and confirm at least one `<svg` tag is present (this verifies Mermaid actually rendered into SVG and didn't leave the diagrams as raw code blocks). If no `<svg>` tag is present, baoyu's Mermaid renderer failed — append the inline Mermaid.js CDN script from Path B's template so the diagrams still render at view time.

If baoyu fails to run (missing `bun`, network error fetching its deps, parse error on the markdown), fall through to Path B.

---

## Step 18.2B — Python fallback render path

If Path B is selected (or Path A failed):

1. Render the markdown to HTML body using Python's `markdown` library if installed; otherwise use the `mistune` fallback below. Either way, **leave the `mermaid` fenced code blocks as `<pre><code class="language-mermaid">…</code></pre>`** — the client-side Mermaid script will find them by class and replace them with SVG.

2. Use the following Python script (write it to `research/temp/render_html.py`, then run it with `python3`):

```python
"""Render final report markdown to a self-contained HTML page with Mermaid + TOC."""
import re
import sys
from pathlib import Path

try:
    import markdown as md_lib
    def render_md(text: str) -> str:
        return md_lib.markdown(
            text,
            extensions=["fenced_code", "tables", "toc", "footnotes", "attr_list"],
            extension_configs={"toc": {"permalink": True}},
        )
except ImportError:
    # mistune is more commonly preinstalled; fall back to it
    try:
        import mistune
        def render_md(text: str) -> str:
            return mistune.html(text)
    except ImportError:
        # Last resort: hand-rolled minimal renderer (headings, paragraphs, fenced code, links)
        def render_md(text: str) -> str:
            html = []
            in_code = False
            code_lang = ""
            code_buf = []
            for line in text.splitlines():
                if line.startswith("```"):
                    if in_code:
                        html.append(f'<pre><code class="language-{code_lang}">' + "\n".join(code_buf) + "</code></pre>")
                        code_buf, in_code, code_lang = [], False, ""
                    else:
                        in_code = True
                        code_lang = line[3:].strip()
                    continue
                if in_code:
                    code_buf.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
                    continue
                m = re.match(r"^(#{1,6})\s+(.+)$", line)
                if m:
                    level = len(m.group(1))
                    text_ = m.group(2)
                    html.append(f"<h{level}>{text_}</h{level}>")
                    continue
                if line.strip() == "":
                    html.append("")
                else:
                    html.append(f"<p>{line}</p>")
            return "\n".join(html)


def build_toc(md_text: str) -> str:
    """Extract H2/H3 headings and build a sidebar TOC."""
    items = []
    for line in md_text.splitlines():
        m = re.match(r"^(#{2,3})\s+(.+)$", line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        slug = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-")
        items.append((level, title, slug))
    if not items:
        return ""
    out = ['<nav class="toc"><h2>On this page</h2><ul>']
    for level, title, slug in items:
        cls = "toc-h2" if level == 2 else "toc-h3"
        out.append(f'<li class="{cls}"><a href="#{slug}">{title}</a></li>')
    out.append("</ul></nav>")
    return "\n".join(out)


def add_heading_ids(html: str) -> str:
    """Add id attributes to <h2>/<h3> based on the text so TOC anchors resolve."""
    def slug(s: str) -> str:
        s = re.sub(r"<[^>]+>", "", s).strip().lower()
        return re.sub(r"[^a-z0-9-]+", "-", s).strip("-")
    return re.sub(
        r"<(h[23])>(.+?)</\1>",
        lambda m: f'<{m.group(1)} id="{slug(m.group(2))}">{m.group(2)}</{m.group(1)}>',
        html,
    )


def main(md_path: str, out_path: str) -> None:
    md_text = Path(md_path).read_text(encoding="utf-8")
    title = next(
        (line[2:].strip() for line in md_text.splitlines() if line.startswith("# ")),
        Path(md_path).stem,
    )
    body_html = add_heading_ids(render_md(md_text))
    toc_html = build_toc(md_text)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{title}</title>
<style>
:root {{ --bg:#fbfaf6; --fg:#1c1c1c; --muted:#6b6b6b; --border:#e6e3da; --link:#a0501a; --code-bg:#f1eee5; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--fg); background:var(--bg); }}
.layout {{ display:grid; grid-template-columns:260px minmax(0,1fr); max-width:1400px; margin:0 auto; }}
.toc {{ position:sticky; top:0; align-self:start; max-height:100vh; overflow-y:auto; padding:2rem 1rem 2rem 2rem; border-right:1px solid var(--border); font-size:14px; }}
.toc h2 {{ margin:0 0 1rem 0; font-size:13px; letter-spacing:0.05em; text-transform:uppercase; color:var(--muted); }}
.toc ul {{ list-style:none; padding:0; margin:0; }}
.toc li.toc-h2 {{ margin:0.25rem 0; }}
.toc li.toc-h3 {{ margin:0.15rem 0 0.15rem 1rem; font-size:13px; }}
.toc a {{ color:var(--fg); text-decoration:none; }}
.toc a:hover {{ color:var(--link); }}
main {{ padding:2.5rem 3rem; max-width:900px; min-width:0; }}
h1 {{ font-size:2.2rem; margin:0 0 1rem 0; }}
h2 {{ font-size:1.6rem; margin:2.5rem 0 1rem 0; padding-bottom:0.3rem; border-bottom:1px solid var(--border); }}
h3 {{ font-size:1.2rem; margin:1.8rem 0 0.6rem 0; }}
p {{ margin:0 0 1rem 0; }}
a {{ color:var(--link); }}
code {{ background:var(--code-bg); padding:0.1em 0.35em; border-radius:3px; font-size:0.92em; }}
pre {{ background:var(--code-bg); padding:1rem; border-radius:6px; overflow-x:auto; }}
pre code {{ background:none; padding:0; }}
.mermaid {{ background:#fff; padding:1.2rem; border-radius:8px; border:1px solid var(--border); margin:1.5rem 0; text-align:center; }}
table {{ border-collapse:collapse; width:100%; margin:1.5rem 0; font-size:0.95em; }}
th, td {{ border:1px solid var(--border); padding:0.55rem 0.85rem; text-align:left; }}
th {{ background:var(--code-bg); }}
blockquote {{ margin:1rem 0; padding:0.6rem 1rem; border-left:4px solid var(--link); background:#fff7ec; color:#553016; }}
@media (max-width:980px) {{
  .layout {{ grid-template-columns:1fr; }}
  .toc {{ position:static; max-height:none; border-right:none; border-bottom:1px solid var(--border); }}
}}
</style>
</head>
<body>
<div class="layout">
{toc_html}
<main>
{body_html}
</main>
</div>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
mermaid.initialize({{ startOnLoad: false, theme: "default", securityLevel: "loose" }});
document.querySelectorAll("pre > code.language-mermaid, code.language-mermaid").forEach((el) => {{
  const pre = el.closest("pre") || el;
  const wrap = document.createElement("div");
  wrap.className = "mermaid";
  wrap.textContent = el.textContent;
  pre.replaceWith(wrap);
}});
mermaid.run({{ querySelector: ".mermaid" }});
</script>
</body>
</html>
"""
    Path(out_path).write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

3. Run it:

```bash
python3 research/temp/render_html.py \
  research/notes/final_report_<vault_tag>.md \
  research/notes/final_report_<vault_tag>.html
```

4. Verify the file exists and contains the Mermaid script: `grep -c 'mermaid' research/notes/final_report_<vault_tag>.html` should return a positive integer.

---

## Step 18.3 — Log

Write `research/html-render-log.json`:

```json
{
  "vault_tag": "<vault_tag>",
  "tier": "<light|full>",
  "render_path": "baoyu | python-fallback",
  "input_md": "research/notes/final_report_<vault_tag>.md",
  "output_html": "research/notes/final_report_<vault_tag>.html",
  "mermaid_blocks_in_md": <int — count of ```mermaid blocks in the input>,
  "svg_blocks_in_html": <int — count of `<svg` tags in the output, or 0 if relying on client-side render>,
  "size_kb": <int — output file size in kilobytes>
}
```

---

## Exit criterion

- `research/notes/final_report_<vault_tag>.html` exists.
- The HTML opens directly in a browser without errors (you can't verify this end-to-end, but a sanity check: the file starts with `<!doctype html>` and ends with `</html>`).
- Mermaid diagrams from the markdown either render as inline `<svg>` (baoyu path) or as `<div class="mermaid">…</div>` blocks that the embedded CDN script will render at view time (Python fallback).
- `research/html-render-log.json` exists.

---

## Pipeline complete

Tell the user:
- Final report markdown: `research/notes/final_report_<vault_tag>.md`
- **Final report HTML (open this): `research/notes/final_report_<vault_tag>.html`**
- Total Mermaid diagrams authored: from `research/diagram-log.json`
- Render path: baoyu or python-fallback

Mark all todos complete. The pipeline is done.
