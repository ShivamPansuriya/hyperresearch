<p align="center">
  <img src="assets/banner.png" alt="HYPERRESEARCH" width="700">
</p>

<h3 align="center">The Most Powerful Deep Research Harness</h3>

<p align="center">
  <a href="https://pypi.org/project/hyperresearch/"><img src="https://img.shields.io/pypi/v/hyperresearch" alt="PyPI version"></a>
  <a href="https://pypi.org/project/hyperresearch/"><img src="https://img.shields.io/pypi/pyversions/hyperresearch" alt="Python 3.11+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/jordan-gibbs/hyperresearch" alt="License: MIT"></a>
  <a href="https://github.com/jordan-gibbs/hyperresearch"><img src="https://img.shields.io/github/stars/jordan-gibbs/hyperresearch?style=social" alt="GitHub stars"></a>
</p>

---

> **Fork notice.** This is a fork of [`jordan-gibbs/hyperresearch`](https://github.com/jordan-gibbs/hyperresearch) that adds **hyperresearch-PRD** — a 12-step Product Requirements Document pipeline (steps 17–28) that consumes a research final report plus a feature request and emits an adversarially-audited PRD. Same architecture as the research pipeline: tier-adaptive, skill-chain, Read+Edit-locked patcher/polish, canonical-input-is-gospel. See [`docs/PRD_EXTENSION.md`](docs/PRD_EXTENSION.md) and the [Install](#install) section below.

**Hyperresearch turns Claude Code into a deep research agent. and currently leads the DeepResearch-Bench RACE leaderboard (benchmarked internally).** A tier-adaptive 16-step pipeline produces adversarially-audited reports with full source provenance. Every fetched source lands in a persistent, searchable vault that compounds across sessions.

<p align="center">
  <img src="assets/benchmark.png" alt="DeepResearch-Bench top-5 — hyperresearch leads the chart ahead of Grep Deep Research, Cellcog Max, nvidia-aiq, Gemini Deep Research, and OpenAI Deep Research" width="780">
</p>

<p align="center"><sub>Forward-looking projection from a stratified pilot against the DeepResearch-Bench leaderboard snapshot (https://huggingface.co/spaces/muset-ai/DeepResearch-Bench-Leaderboard). Third party validation is pending.</sub></p>

## Install

### One-click install (this fork — includes both `/hyperresearch` AND `/hyperresearch-prd`)

```bash
pip install git+https://github.com/ShivamPansuriya/hyperresearch.git@prd-extension && hyperresearch install --global
```

That single line installs the package from this fork's `prd-extension` branch and registers all skills + subagents globally. After it finishes, `/hyperresearch` and `/hyperresearch-prd` are available in every Claude Code session.

Per-project install (cleaner system-reminder footprint):

```bash
cd your-project
pip install git+https://github.com/ShivamPansuriya/hyperresearch.git@prd-extension && hyperresearch install
```

Then `/hyperresearch <anything>` and `/hyperresearch-prd <feature request>` in Claude Code.

### Upstream-only install (research pipeline without the PRD extension)

```bash
cd your-project
pip install hyperresearch && hyperresearch install
```

> Python 3.11–3.13. (3.14 not yet supported — use `pyenv install 3.13`, `uv venv -p 3.13`, or `py -3.13 -m venv .venv`.)
>
> Power users: `hyperresearch install --global` makes both slash commands reachable from every Claude Code session anywhere, at the cost of ~15 lines in every session's system reminder. Per-project install keeps unrelated CC sessions clean.

---

## The 18-step research pipeline

The entry skill is a thin router. It bootstraps the canonical research query, then invokes one step skill per pipeline phase via Claude Code's `Skill` tool. Each step's procedure is loaded fresh into context only when needed defeating context-rot problems that makes long pipelines silently drop steps. Steps 1–16 produce the markdown report; steps 17–18 add Mermaid diagrams and render a self-contained HTML page as the final deliverable.

| # | Step | What it does | Tiers |
|---|---|---|---|
| 1 | Decompose | Canonical query → atomic items + coverage matrix + tier classification | both |
| 2 | Width sweep | Multi-perspective search plan + parallel fetcher waves (Haiku) | both |
| 3 | Contradiction graph | Pair contradictions across the corpus into ranked clusters | full |
| 4 | Loci analysis | Two parallel loci-analysts → scored loci with source budgets | full |
| 5 | Depth investigation | K parallel depth-investigators → interim notes with committed positions | full |
| 6 | Cross-locus reconcile | Reconcile committed positions → comparisons.md | full |
| 7 | Source tensions | Extract expert disagreements → source-tensions.json | full |
| 8 | Corpus critic | "What source would overturn this?" + targeted gap-fill fetch | full |
| 9 | Evidence digest | Top claims + verbatim quotes → evidence-digest.md | full |
| 10 | Triple draft | Per-angle source curation + 3 parallel draft sub-orchestrators (light: single draft) | both |
| 11 | Synthesize | Plan + outline + spawn synthesizer subagent → final_report.md | full |
| 12 | Critics | 4 adversarial critics in parallel → findings JSONs | full |
| 13 | Gap-fetch | Targeted fetch wave for critic-identified vault gaps | full |
| 14 | Patcher | Surgical Edit hunks applied to draft (tool-locked Read+Edit) | full |
| 15 | Polish | Hygiene + filler pass (tool-locked Read+Edit subagent) | both |
| 16 | Readability audit | Recommender writes JSON suggestions; orchestrator selectively applies | both |
| 17 | Author diagrams | Insert Mermaid blocks (hypothesis tree, source-tension graph, architecture, comparison, decision tree) into the final report | both |
| 18 | Render HTML | Convert diagram-enriched markdown → self-contained HTML with rendered SVG diagrams (baoyu skill or Python fallback) | both |

### Depth Modes 

In your prompt, you can request one of two tiers and the rest of the pipeline scales accordingly. Full mode is default.

| Tier | Steps that run | Typical time |
|---|---|---|
| `light` | bounded factual queries, surveys, comparisons — 1 → 2 → 10 → 15 → 16 → 17 → 18 | ~30–40 min |
| `full` | deep argumentative analysis with adversarial review — all 18 steps | ~1.5–2.5 hours |

The HTML render step (18) is the same for both tiers. The markdown source lives at `research/notes/final_report_<vault_tag>.md`; the user-facing HTML is `research/notes/final_report_<vault_tag>.html`.

### The two load-bearing principles

1. **Patch, never regenerate.** After step 11 produces the synthesized report (or step 10 for light tier), the only modifications are surgical Edit hunks. The patcher and polish auditor are tool-locked to `[Read, Edit]` at the Claude Code allowlist level so they physically cannot Write a new draft. Per-hunk caps make "just rewrite it" mechanically impossible. Critic findings that don't fit a small hunk escalate as structural issues.

2. **Canonical research query is gospel.** The verbatim user prompt is persisted to `research/query-<vault_tag>.md` once and re-read by every subsequent step and every spawned subagent. Wrapper requirements (save paths, citation format, terminal sections) are a separate contract.

### Subagent roster

| Agent | Model | Role |
|---|---|---|
| `hyperresearch-fetcher` | Sonnet | URL fetching via crawl4ai; runs 8–12 in parallel per wave |
| `hyperresearch-source-analyst` | Sonnet (1M ctx) | End-to-end digest of any single long source >5000 words |
| `hyperresearch-loci-analyst` | Sonnet | Reads the width corpus, returns 1–8 depth loci with rationale |
| `hyperresearch-depth-investigator` | Sonnet | Investigates one locus, writes one interim note with a committed position |
| `hyperresearch-corpus-critic` | Sonnet | "What source would overturn the current direction?" pre-draft gap analysis |
| `hyperresearch-draft-orchestrator` | Opus | One per draft angle; reads its curated source list and writes one draft |
| `hyperresearch-synthesizer` | Opus | Reads all 3 drafts, writes the final report (two-pass write, Read+Write locked) |
| `hyperresearch-dialectic-critic` | Opus | Counter-evidence the draft missed |
| `hyperresearch-depth-critic` | Opus | Shallow spots interim notes could fill |
| `hyperresearch-width-critic` | Opus | Topical corners the corpus supports but the draft ignores |
| `hyperresearch-instruction-critic` | Opus | Structural mismatches against the prompt's atomic items |
| `hyperresearch-patcher` | Opus | Tool-locked `[Read, Edit]`. Applies critic findings as surgical Edit hunks |
| `hyperresearch-polish-auditor` | Opus | Tool-locked `[Read, Edit]`. Cuts filler, strips hygiene leaks |
| `hyperresearch-readability-recommender` | Opus | Writes JSON suggestions for paragraph rhythm and list/table conversion |

---

## The PRD extension (steps 17–30) — fork-only

The fork adds a second pipeline that consumes a completed research report plus a feature request and produces a Product Requirements Document. Same step-skill chain, same canonical-input-is-gospel invariant, same patch-never-regenerate invariant, same tool-locked subagent pattern. Final step renders an HTML PRD with Mermaid diagrams.

| #  | Step                            | Tiers |
|----|---------------------------------|-------|
| 17 | Initialize (tier + format + required headings) | all |
| 18 | Product inventory (scan existing PRD directory) | all |
| 19 | Feature decomposition + skill discovery | all |
| 20 | Integration map (user-visible touchpoints) | full + light |
| 21 | Personas & user stories | full + light |
| 22 | Flows & user-visible entity fields | full |
| 23 | Triple-draft ensemble (light: single draft) | all |
| 24 | Synthesizer (two-pass write) | full |
| 25 | 4 adversarial critics in parallel | full |
| 26 | Patcher (Read+Edit only) | full |
| 27 | Polish auditor (Read+Edit only) | all |
| 28 | Readability audit + selective apply | all |
| 29 | Author diagrams (persona map, user flow, scope boundary, integration touchpoints) into the PRD | all |
| 30 | Render the diagram-enriched PRD to a self-contained HTML file (FINAL) | all |

**What goes in:** a verbatim feature request + a prior `/hyperresearch` final report + an optional existing PRD directory (default `prd/`).
**What comes out:**
- `prd/notes/final_prd_<prd_tag>.md` — a business-only PRD (no schemas, no APIs, no architecture) ready for engineering handoff.
- `prd/notes/final_prd_<prd_tag>.html` — the same PRD rendered as a self-contained HTML page with persona maps, user flows, scope-boundary diagrams, and integration-touchpoint maps rendered as SVG. **This is the page the team actually opens.**

### Tier routing

| Tier   | Steps                                                                               | Typical time |
|--------|-------------------------------------------------------------------------------------|--------------|
| `light` | 17 → 18 → 19 → 20 → 21 → 23 (single draft) → 27 → 28 → 29 → 30                     | ~30–40 min   |
| `full`  | 17 → 18 → 19 → 20 → 21 → 22 → 23 → 24 → 25 → 26 → 27 → 28 → 29 → 30                | ~1–2 hours   |

### Per-step invocation

Every step is independently invokable, exactly like the research pipeline's 1–16:

```
/hyperresearch-prd                              ← whole pipeline
/hyperresearch-prd-17-initialize                ← just step 17
/hyperresearch-prd-23-triple-draft              ← just step 23
…
/hyperresearch-prd-28-readability-audit         ← just step 28
```

### Skill discovery (NEW)

Step 19 detects PMG-relevant Claude Code skills (`impeccable`, `frontend-design`, `content-engine`, `article-writing`, `investor-materials`, etc.) installed in your environment and writes them to `prd/relevant-skills.json`. The draft-orchestrator and synthesizer subagents read this list and invoke each listed skill via `Skill(skill: "...")` before drafting the sections it strengthens. Engineering / framework / DB skills are explicitly excluded — the PRD stays in the business lane.

### HTML output (research and PRD)

Both pipelines end with a Mermaid-enriched HTML page as the user-facing deliverable:

- Research: `research/notes/final_report_<vault_tag>.html`
- PRD: `prd/notes/final_prd_<prd_tag>.html`

The HTML render step prefers the [`baoyu-markdown-to-html`](https://www.skills.sh/jimliu/baoyu-skills/baoyu-markdown-to-html) skill if installed (`npx skills add https://github.com/jimliu/baoyu-skills --skill baoyu-markdown-to-html`). If baoyu is not installed, a pure-Python fallback renders a sticky-TOC themed page and loads Mermaid.js from a CDN at view time. Either path produces a single self-contained file you can open directly in a browser.

### Documentation

- [`docs/PRD_EXTENSION.md`](docs/PRD_EXTENSION.md) — overview, tier routing, invariants, comparison to research pipeline
- [`docs/PRD_QUICKSTART.md`](docs/PRD_QUICKSTART.md) — end-to-end walkthrough using a concrete example
- [`docs/PRD_ARCHITECTURE.md`](docs/PRD_ARCHITECTURE.md) — internals, extension points, design rationale
- [`docs/PRD_PER_STEP_INVOCATION.md`](docs/PRD_PER_STEP_INVOCATION.md) — recovery contract per step, manual rerun scenarios
- [`evals/`](evals/) — 3 iterations of adversarial eval that drove findings from 15 → 8 → 3 (zero HIGH after iteration 3)

---

## The vault: persistent, searchable, compounding

Hyperresearch is not a one-shot report generator like most other Deep research harnesses. Every fetched source lands in a SQLite-indexed vault that every future research session can reuse.

```bash
hyperresearch search "ion-trap gate fidelity" -j           # Full-text search
hyperresearch search "quantum" --include-body -j           # Full-body search
hyperresearch note show <id1> <id2> <id3> -j               # Batch-read notes
hyperresearch graph hubs -j                                # Most-connected notes
hyperresearch graph backlinks <id> -j                      # Reverse links
hyperresearch lint -j                                      # Health check (broken links, missing tags)
```

**Markdown is truth, SQLite is cache.** Notes live as plain markdown with YAML frontmatter in `research/notes/`. The SQLite index is fully rebuildable. Delete it and `hyperresearch sync` reconstructs it from the markdown. The vault is inspectable in any editor, version-controllable in git, and readable without the tool installed.

**PDFs fetch directly.** `hyperresearch fetch` auto-detects PDF URLs (arXiv, NBER, SSRN, direct `.pdf` links) and extracts full text via pymupdf. Raw PDFs land in `research/raw/<note-id>.pdf` and the note's `raw_file:` frontmatter links back.

**Provenance breadcrumbs.** Every fetched source carries a `--suggested-by` link back to whatever surfaced it. The chain forms a rooted tree from seed fetches; the `provenance` lint rule catches disconnected components.

---

## What's structurally enforced

- **Verbatim prompt as gospel** — `scaffold-prompt` lint blocks if the scaffold doesn't open with the user's exact prompt
- **Locus coverage** — every step 4 locus must have a step 5 interim note; missing interims flag as errors
- **Patch-only modification** — steps 14, 15, 16 are tool-locked to `[Read, Edit]`. They cannot regenerate the draft
- **Critical findings never silently skip** — `patch-surgery` lint surfaces any critical finding the patcher couldn't apply
- **Schema integrity** — `tier`, `content_type`, and `type` are SQLite CHECK-constrained vocabularies; corrupted frontmatter cannot poison the index
- **Hygiene leaks caught on the way out** — scaffold sections, YAML frontmatter, and prompt echoes are stripped by step 15 before ship

---

## Authenticated crawling

Fetch from LinkedIn, Twitter, paywalled sites or anything you can log into:

```bash
hyperresearch setup       # Browser opens. Log into your sites. Done.
```

LinkedIn, Twitter, Facebook, Instagram, and TikTok automatically use a visible browser to avoid session kills.

---

## Academic APIs before web search

For any topic with a research literature, hit academic APIs BEFORE web search. They return citation-ranked canonical papers; web search returns derivative commentary.

- **Semantic Scholar** — `https://api.semanticscholar.org/graph/v1/paper/search`
- **arXiv** — `https://export.arxiv.org/api/query`
- **OpenAlex** — `https://api.openalex.org/works`
- **PubMed** — `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`

After the academic sweep, run web searches for context, news, non-academic angles, and at least one adversarial search ("criticism of X", "limitations of X").

### Exa MCP (optional, enriches web search)

The fetcher and corpus-critic agents support the [Exa MCP server](https://exa.ai) — a neural search engine that returns higher-signal results than keyword search. When configured, agents prefer Exa over the built-in `WebSearch` and pick the right Exa mode by query type:

- `mcp__exa__web_search_exa` — default discovery (describe the ideal page in natural language).
- `mcp__exa__web_search_advanced_exa` — filtered search: date ranges, domain include/exclude, categories (`research paper`, `news`, `pdf`, `company`, `people`, `financial report`, `github`, `personal site`).
- `mcp__exa__deep_search_exa` — multi-angle synthesized answer with citations (used sparingly, ~5-50s).
- `mcp__exa__get_code_context_exa` — code / API / library examples from GitHub, Stack Overflow, docs.
- `mcp__exa__crawling_exa` — extract full markdown from a known URL when `hyperresearch fetch` is blocked.

The corpus-critic uses Exa to verify each candidate gap before flagging it (so the gap-fetch wave in step 13 doesn't hunt for sources that already exist or genuinely don't exist).

Setup: add to `~/.claude.json`:

```json
"exa-web-search": {
  "command": "npx",
  "args": ["-y", "exa-mcp-server"],
  "env": { "EXA_API_KEY": "YOUR_EXA_API_KEY_HERE" }
}
```

If Exa isn't configured, agents silently fall back to `WebSearch` + the academic APIs — the pipeline still works, just with lower discovery signal.

---

## What it doesn't do

- It doesn't replace your judgment on which sources matter. The agent picks, you steer.
- It can't fetch what's behind a paywall you haven't logged into.
- It runs on Anthropic models Opus + Sonnet + Haiku via the subagent roster. Costs scale with tier and corpus size. If anyone wants to port this to Codex, put up a PR! 
- The lint gate catches **structural** failures (missing scaffold, broken provenance, unresolved CRITICALs). It cannot guarantee factual accuracy, that's still your call.

---

## Requirements

- Python 3.11+
- [Claude Code](https://claude.com/claude-code)

---

## License

[MIT](LICENSE)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=jordan-gibbs/hyperresearch&type=Date)](https://star-history.com/#jordan-gibbs/hyperresearch&Date)
