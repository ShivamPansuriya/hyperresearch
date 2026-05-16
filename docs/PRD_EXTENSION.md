# Hyperresearch-PRD Extension

A tier-adaptive 12-step pipeline that turns a **feature request + a completed hyperresearch report + an existing PRD directory** into an adversarially-audited Product Requirements Document.

The extension lives alongside the 16-step research pipeline. It reuses the same step-skill chain architecture, the same canonical-input-is-gospel invariant, the same patch-never-regenerate invariant, and the same tool-locked subagent pattern.

## What it produces

A single Markdown file:

```
prd/notes/final_prd_<prd_tag>.md
```

Format options (auto-classified by step 17 or overridable via the feature request):

- **`one_pager`** — 300–800 words. Tiny incremental change.
- **`standard_prd`** — 1500–4000 words. Most features.
- **`detailed_prd`** — 4000–8000 words. Cross-cutting, multi-persona, compliance-heavy.

PRDs contain **business / product** content only: feature overview, goals & non-goals, personas, user stories, user flows, user-visible entities & fields, integration with existing product, acceptance criteria, out of scope, future scope, success metrics. **No** architecture, schemas, APIs, languages, frameworks, infrastructure, code.

## When to use it

After a completed `/hyperresearch` run that informs a product decision. The research final report becomes the evidence base; the PRD is the spec PMG hands to engineering.

Typical use:

```
1. /hyperresearch "How are top SIS systems handling parent-attendance alerts?"
2. /hyperresearch-prd "Build a parent attendance alert feature for ManageArk: parents opt in
   per child, get push + inbox when a child is marked absent, with acknowledge flow."
```

The PRD pipeline reads:
1. The verbatim feature request (gospel).
2. The latest `research/notes/final_report_*.md` (research findings).
3. The repository's `prd/` directory (existing product PRDs for context).

## Pipeline at a glance

| #  | Step                                               | Tiers |
|----|----------------------------------------------------|-------|
| 17 | Initialize (mint prd_tag, classify tier + format)  | all   |
| 18 | Product inventory (scan PRD dir)                   | all   |
| 19 | Feature decomposition (reconciled with inventory)  | all   |
| 20 | Integration map (user-visible touchpoints)         | full  |
| 21 | Personas & user stories                            | full  |
| 22 | Flows & user-visible entity fields                 | full  |
| 23 | Triple-draft ensemble (light: single)              | all   |
| 24 | Synthesizer (two-pass write)                       | full  |
| 25 | 4 adversarial critics in parallel                  | full  |
| 26 | Patcher (tool-locked Read+Edit)                    | full  |
| 27 | Polish auditor (tool-locked Read+Edit)             | all   |
| 28 | Readability audit + selective apply                | all   |

### Tier routing

- **light:** `17 → 18 → 19 → 23 (single draft) → 27 → 28` — small features, 20–30 min.
- **full:** all 12 steps — cross-cutting, multi-persona, regulatory features, 1–2 hours.

Step 17 classifies the tier automatically. Override in the feature request if needed (`pipeline_tier: full`).

## The 9 PRD subagents

| Agent name                              | Tool lock        | Spawned in step |
|-----------------------------------------|------------------|-----------------|
| `prd-draft-orchestrator` (×3 parallel)  | Read/Write/Bash  | 23              |
| `prd-synthesizer`                       | Read+Write only  | 24              |
| `prd-business-value-critic`             | Read+Write only  | 25              |
| `prd-scope-creep-critic`                | Read+Write only  | 25              |
| `prd-integration-feasibility-critic`    | Read+Write only  | 25              |
| `prd-instruction-critic`                | Read+Write only  | 25              |
| `prd-patcher`                           | **Read+Edit ONLY** | 26              |
| `prd-polish-auditor`                    | **Read+Edit ONLY** | 27              |
| `prd-readability-recommender`           | Read+Write only  | 28              |

The Read+Edit lock on the patcher and polish-auditor is the same invariant the research pipeline enforces on its patcher and polish auditor: surgical edits only, no rewrites.

## Artifact map

```
prd/
├── request-<prd_tag>.md                 # canonical feature request, gospel
├── scaffold.md                          # orchestrator's private planning doc
├── prd-decomposition.json               # tier + format + required headings
├── product-inventory.json               # snapshot of existing product
├── feature-decomposition.json           # in/adjacent/out/future scope
├── integration-map.json                 # user-visible touchpoints (full only)
├── personas.md                          # persona profiles (full only)
├── user-stories.md                      # per-persona stories (full only)
├── flows.md                             # step-by-step user flows (full only)
├── entities.md                          # user-visible field tables (full only)
├── temp/                                # scratch + intermediate
│   ├── coverage-matrix.md
│   ├── scope-envelope.md
│   ├── angle-assignment.md
│   ├── draft-{a,b,c}.md                # full only
│   ├── draft-{a,b,c}-source-list.md    # full only
│   ├── synthesis-plan.md               # full only
│   ├── synthesis-outline.md            # full only
│   ├── synthesis-conflicts.md          # full only
│   ├── synthesis-pass1.md              # full only
│   ├── critic-triage.md                # full only
│   ├── orchestrator-notes.md
│   └── inventory-summary.md
├── prd-critic-findings-{business-value,scope-creep,
│     integration-feasibility,instruction}.json   # full only
├── patch-log.json                      # full only
├── polish-log.json
├── readability-recommendations.json
├── readability-decisions.json
└── notes/
    └── final_prd_<prd_tag>.md          # THE FINAL PRD
```

## Invariants

1. **No architecture in the PRD.** Every step filters out DB / schema / API / endpoint / queue / cache / service / framework / language references. Where a research source provided architectural detail, the PRD translates to user-visible behavior or omits.
2. **Patch, never regenerate.** After step 23 (light) / step 24 (full) writes the final PRD, only surgical Edit hunks modify it. Tool-locked at the Claude Code allowlist level.
3. **Canonical feature request is gospel.** Persisted to `prd/request-<prd_tag>.md` once and re-read by every step and every subagent.
4. **Existing PRD directory is read-only.** Step 18 only READS the inventory. The pipeline never mutates existing PRDs.
5. **Tier gate respected.** Light = light. Full = full. No silent upgrades or downgrades.

## Install

The extension ships with the `hyperresearch` package. After installing or upgrading:

```bash
# Per-project install
hyperresearch prd-install .

# Or user-level install (slash command available everywhere)
hyperresearch prd-install --global

# Check what's installed
hyperresearch prd-install --status
```

This copies the 12 step skills to `<target>/.claude/skills/hyperresearch-prd-*/SKILL.md` and the 9 subagents to `<target>/.claude/agents/<name>.md`.

## Run it

Once installed:

```
/hyperresearch-prd <your feature request, in prose>
```

The Claude Code skill resolves to `hyperresearch-prd` (the router), which bootstraps inputs and chains through steps 17–28. If a hyperresearch final report is missing the pipeline halts and tells you to run `/hyperresearch` first.

### Per-step invocation

Every step is also independently invokable, exactly like the research pipeline's `/hyperresearch-1-decompose` … `/hyperresearch-16-readability-audit`:

```
/hyperresearch-prd-17-initialize
/hyperresearch-prd-18-product-inventory
/hyperresearch-prd-19-feature-decomposition
/hyperresearch-prd-20-integration-map
/hyperresearch-prd-21-personas-stories
/hyperresearch-prd-22-flows-entities
/hyperresearch-prd-23-triple-draft
/hyperresearch-prd-24-synthesize
/hyperresearch-prd-25-critics
/hyperresearch-prd-26-patcher
/hyperresearch-prd-27-polish
/hyperresearch-prd-28-readability-audit
```

Use these to iterate on a specific stage without re-running the whole pipeline (e.g., re-synthesizing after editing `prd/temp/synthesis-plan.md`, or re-scanning the PRD directory after adding a new PRD to `prd/`).

Each step's recovery contract (the artifacts it needs from prior steps) is documented in its `Recover state` section. See `docs/PRD_PER_STEP_INVOCATION.md` for the full input-requirement table and rerun scenarios.

## When the pipeline finishes

You get:

- A user-facing PRD at `prd/notes/final_prd_<prd_tag>.md` ready to hand to engineering.
- An audit trail: every artifact above, plus the patch log and polish log if full-tier.
- A closing summary printed by step 28: tier, format, word count, applied/deferred/dismissed recommendations, any escalations.

## Comparison to the research pipeline

| Dimension                       | hyperresearch (steps 1–16)         | hyperresearch-PRD (steps 17–28)     |
|---------------------------------|------------------------------------|-------------------------------------|
| Output                          | `research/notes/final_report_*.md` | `prd/notes/final_prd_*.md`          |
| Canonical input                 | `research/query-*.md`              | `prd/request-*.md`                  |
| Width sweep                     | Multi-source web + academic        | Reads existing PRD directory        |
| Adversarial critics             | 4 (dialectic, depth, width, instr) | 4 (BV, scope-creep, IF, instr)      |
| Patch never regenerate          | Yes                                | Yes                                 |
| Tool-locked subagents           | patcher, polish-auditor            | patcher, polish-auditor             |
| Two-pass synthesizer            | Yes                                | Yes                                 |
| Light tier                      | 1 → 2 → 10 → 15 → 16               | 17 → 18 → 19 → 23 → 27 → 28         |
| Full tier                       | 1 → … → 16 (all 16)                | 17 → … → 28 (all 12)                |

The two pipelines compose: research grounds the PRD's claims in evidence; the PRD distills evidence into a buildable spec.
