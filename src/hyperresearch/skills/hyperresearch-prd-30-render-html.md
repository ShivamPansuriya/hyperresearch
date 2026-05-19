---
name: hyperresearch-prd-30-render-html
description: >
  Step 30 (FINAL) of the hyperresearch-PRD pipeline. Renders the diagram-
  enriched PRD markdown into a single self-contained HTML file the
  engineering team can open directly. Primary path: invoke the
  baoyu-markdown-to-html skill if installed. Fallback path: pure-Python
  markdown rendering with Mermaid.js from CDN. The HTML page is the
  user-facing deliverable for the PRD. Runs for ALL tiers.
---

# Step 30 — Render the final PRD to HTML (FINAL STEP)

**Tier gate:** Runs for ALL tiers. The HTML is the final artifact handed to engineering / product reviewers; the markdown is the source of truth, the HTML is what they actually read.

**Goal:** turn `prd/notes/final_prd_<prd_tag>.md` into `prd/notes/final_prd_<prd_tag>.html` — a single standalone file that:
- Renders every Mermaid block (authored in step 29) as inline SVG.
- Has a sticky sidebar TOC for easy navigation.
- Is self-contained — no external assets except the Mermaid CDN script (which loads at view time).

---

## Recover state

Read these inputs:
- `prd/scaffold.md` — `prd_tag`
- `prd/notes/final_prd_<prd_tag>.md` — the diagram-enriched final PRD (output of step 29)

---

## Step 30.1 — Detect rendering path

You have two paths. Prefer baoyu.

**Path A — baoyu (preferred).** Check if the `baoyu-markdown-to-html` skill is installed:

```bash
test -f .claude/skills/baoyu-markdown-to-html/SKILL.md && echo "project" \
  || test -f ~/.claude/skills/baoyu-markdown-to-html/SKILL.md && echo "user" \
  || echo "missing"
```

If `project` or `user`, baoyu is available — use Path A. Otherwise, Path B.

---

## Step 30.2A — Baoyu render path

If Path A:

1. Invoke baoyu via the `Skill` tool:

   ```
   Skill(
     skill: "baoyu-markdown-to-html",
     args: "Convert prd/notes/final_prd_<prd_tag>.md to HTML.
            Output path: prd/notes/final_prd_<prd_tag>.html.
            Theme: modern.
            Render Mermaid blocks as inline SVG.
            Make the page self-contained."
   )
   ```

2. Verify the output file exists at the expected path; `mv` it if baoyu wrote elsewhere.

3. **Diagram check.** Read the first 500 lines of the produced HTML and confirm at least one `<svg` tag is present. If absent, append the inline Mermaid.js CDN script from Path B so the diagrams render at view time.

If baoyu fails to run (missing `bun`, network error, parse error), fall through to Path B.

---

## Step 30.2B — Python fallback render path

If Path B (or Path A failed):

1. Reuse the rendering script written by the research pipeline's step-18 fallback. If it exists at `research/temp/render_html.py`, call it directly. Otherwise write it now using the exact template from `hyperresearch-18-render-html` SKILL.md Step 18.2B (the same Python program — see that skill for the full source).

2. Run it against the PRD inputs:

   ```bash
   mkdir -p prd/temp
   # If research/temp/render_html.py exists, reuse it. Otherwise write it
   # using the template from hyperresearch-18-render-html (same file body).
   python3 research/temp/render_html.py \
     prd/notes/final_prd_<prd_tag>.md \
     prd/notes/final_prd_<prd_tag>.html
   ```

   (The render script is generic — it doesn't care whether the input is a research report or a PRD; it just renders any markdown file with embedded Mermaid blocks.)

3. Verify the file exists and contains the Mermaid script via `grep -c 'mermaid' prd/notes/final_prd_<prd_tag>.html`.

---

## Step 30.3 — Log

Write `prd/html-render-log.json`:

```json
{
  "prd_tag": "<prd_tag>",
  "tier": "<light|full>",
  "render_path": "baoyu | python-fallback",
  "input_md": "prd/notes/final_prd_<prd_tag>.md",
  "output_html": "prd/notes/final_prd_<prd_tag>.html",
  "mermaid_blocks_in_md": <int>,
  "svg_blocks_in_html": <int>,
  "size_kb": <int>
}
```

---

## Exit criterion

- `prd/notes/final_prd_<prd_tag>.html` exists.
- The file starts with `<!doctype html>` and ends with `</html>`.
- All Mermaid blocks from the markdown are either inline-SVG (baoyu) or wrapped in `<div class="mermaid">…</div>` blocks that the embedded CDN script renders at view time (Python fallback).
- `prd/html-render-log.json` exists.

---

## Pipeline complete

Print a short closing summary (≤15 lines) listing:
- `prd_tag`
- `pipeline_tier`
- `prd_format`
- Final word count
- **Final PRD markdown:** `prd/notes/final_prd_<prd_tag>.md`
- **Final PRD HTML (open this):** `prd/notes/final_prd_<prd_tag>.html`
- Total diagrams authored: from `prd/diagram-log.json`
- Render path: baoyu or python-fallback
- Any escalations or warnings the pipeline flagged for human attention

Then stop. The PRD is ready for the development team. The HTML is the page they'll actually read.
