---
name: hyperresearch-prd
description: >
  PRD generation via the HYPERRESEARCH-PRD architecture — a tier-adaptive
  14-step pipeline (light / full) that turns a feature request plus a
  completed hyperresearch report into an adversarially-audited Product
  Requirements Document. Steps 17–28 build the markdown PRD; steps 29–30
  add Mermaid diagrams and render a self-contained HTML page as the final
  deliverable. This entry skill is a ROUTER. It does not contain step
  procedures — it tells you which Skill to invoke for each step, in order.
  Each step's instructions live in its own skill file
  (`hyperresearch-prd-17-initialize` through
  `hyperresearch-prd-30-render-html`) and are loaded fresh into context
  when you invoke them.
---

# Hyperresearch-PRD — multi-skill chain orchestrator

PRD pipeline that **extends** the hyperresearch research pipeline. It runs AFTER hyperresearch step 16 completes (or against any prior `research/notes/final_report_<tag>.md`) and produces a final PRD document at `prd/notes/final_prd_<prd_tag>.md`.

PRDs are **business / product artifacts**. They MUST NOT contain architectural decisions, schemas, API contracts, code, or technology choices. Those belong to the engineering team. Every step in this pipeline is designed to keep the output strictly in the PMG (product/marketing/growth) lane: user stories, feature scope, user flows, user-facing entities/fields, integration touchpoints (described functionally), personas, acceptance criteria, out-of-scope, future scope, success metrics.

## How the chain works (READ THIS CAREFULLY)

Each pipeline step is its own skill file. There are **two equivalent ways** to invoke a step:

1. **Programmatically from the orchestrator (this entry skill):**
   ```
   Skill(skill: "hyperresearch-prd-N-stepname")
   ```
2. **Manually as a slash command** (any installed step is auto-registered as `/<skill-name>`):
   ```
   /hyperresearch-prd-17-initialize
   /hyperresearch-prd-23-triple-draft
   /hyperresearch-prd-28-readability-audit
   ```

Use the slash form when iterating on a specific stage (e.g., re-running synthesis after editing `prd/temp/synthesis-plan.md`). Use the `Skill` form when chaining through the pipeline as the orchestrator.

When you invoke a Skill, that skill's full procedure is loaded into your context **fresh**. You then execute that step's procedure, hit its exit criterion, and return to this entry skill to invoke the next step.

**Why this design?** Same reason as the parent hyperresearch pipeline: context compaction. Each step's procedure is loaded into context only at the moment it's needed.

**The 14 step skills** (all prefixed `hyperresearch-prd-`):

| #  | Skill name                                       | What it does                                                                                              | Tiers |
|----|--------------------------------------------------|-----------------------------------------------------------------------------------------------------------|-------|
| 17 | `hyperresearch-prd-17-initialize`                | Canonical feature request → prd_tag + scaffold + tier classification + required_section_headings          | all   |
| 18 | `hyperresearch-prd-18-product-inventory`         | Scan PRD directory → product-inventory.json (existing features, modules, entities, personas already documented) | all |
| 19 | `hyperresearch-prd-19-feature-decomposition`     | Decompose feature request into atomic items + coverage matrix + scope envelope                            | all   |
| 20 | `hyperresearch-prd-20-integration-map`           | Map feature touchpoints to existing modules/entities/flows in the inventory                               | full  |
| 21 | `hyperresearch-prd-21-personas-stories`          | Generate persona-anchored user stories (one set per persona)                                              | full  |
| 22 | `hyperresearch-prd-22-flows-entities`            | Build step-by-step user flows + user-facing entity field lists                                            | full  |
| 23 | `hyperresearch-prd-23-triple-draft`              | Triple-draft ensemble (3 angle-specific PRD drafts in parallel; light: single draft direct to final)      | all   |
| 24 | `hyperresearch-prd-24-synthesize`                | Synthesis plan + outline + spawn prd-synthesizer subagent (two-pass write) → final_prd.md                 | full  |
| 25 | `hyperresearch-prd-25-critics`                   | 4 adversarial critics in parallel → findings JSONs                                                        | full  |
| 26 | `hyperresearch-prd-26-patcher`                   | Surgical Edit hunks applied to draft (tool-locked Read+Edit)                                              | full  |
| 27 | `hyperresearch-prd-27-polish`                    | Hygiene + filler pass (tool-locked Read+Edit subagent)                                                    | all   |
| 28 | `hyperresearch-prd-28-readability-audit`         | Readability recommender writes JSON suggestions; orchestrator selectively applies                         | all   |
| 29 | `hyperresearch-prd-29-author-diagrams`           | Insert Mermaid diagrams (persona map, user flow, scope boundary, integration touchpoints) into the PRD    | all   |
| 30 | `hyperresearch-prd-30-render-html`               | Render the diagram-enriched PRD to a self-contained HTML file (baoyu skill if available, Python fallback) | all   |

## Tier routing

Step 17 classifies the PRD into a `pipeline_tier` (`light` / `full`). The tier is written to `prd/prd-decomposition.json`. After step 17, **read that file** to learn the tier, then sequence steps according to:

| Tier   | Steps that run                                                              | Typical time |
|--------|-----------------------------------------------------------------------------|--------------|
| `light` | 17 → 18 → 19 → 20 → 21 → 23 (single draft) → 27 → 28 → 29 → 30              | ~30–40 min   |
| `full`  | 17 → 18 → 19 → 20 → 21 → 22 → 23 → 24 → 25 → 26 → 27 → 28 → 29 → 30         | ~1–2 hours   |

Steps 29 and 30 run for BOTH tiers — the HTML PRD page (with diagrams rendered as SVG) is the final user-facing deliverable.

**Light-tier note:** steps 20 (integration map) and 21 (personas + stories) are KEPT in the light path because every standard_prd requires `Integration with existing product` and `User stories` headings; skipping them produces required headings with thin content. Step 22 (flows + entities) remains full-tier only.

**RESPECT THE TIER GATE.** Simple incremental features (small UX tweaks, single-screen additions, a new field on an existing entity) classify as `light`. Net-new feature areas, cross-module flows, multi-persona experiences, and anything touching ≥3 existing modules tier up to `full`. The tier is a binding contract.

## Bootstrap (run BEFORE invoking step 17)

Before you invoke any step skill, do this:

**0. Explicit-confirmation gate (MANDATORY).** Before doing ANY work, ask the user to confirm they actually want to run the PRD pipeline. The PRD pipeline is independent from `/hyperresearch` (the research pipeline) — research is steps 1–16 and ends at the final report; PRD is steps 17–28 and produces a different artifact. This gate exists because PRD is a heavier, slower flow than research-only, and the user may have invoked `/hyperresearch-prd` by accident.

Print exactly this prompt to the user and STOP until they reply with explicit confirmation:

```
You're about to run the PRD pipeline (hyperresearch-PRD).

This is NOT the research pipeline. It consumes a prior research report
plus a feature request and produces a Product Requirements Document.

Estimated time:
- light tier: ~30–40 min
- full tier: ~1–2 hours

Required inputs:
1. The feature request you want a PRD for (verbatim).
2. A completed research final report (you must run /hyperresearch first
   if you haven't already).
3. Path to your existing PRD directory (default: prd/).

If you only wanted to do research and not generate a PRD, STOP here
and use /hyperresearch instead.

Reply 'yes, proceed with PRD' (or similar explicit affirmation) to
continue. Anything else, including silence, aborts the run.
```

Accept ONLY explicit affirmative replies (e.g., "yes", "yes proceed", "go ahead with PRD", "confirmed", "run it"). Do NOT proceed on ambiguous, conditional, or non-affirmative replies — abort and tell the user the run is cancelled. The user can re-invoke `/hyperresearch-prd` later.

If the user has clearly signalled intent in the original slash invocation (e.g., they typed `/hyperresearch-prd Build a parent attendance alert feature for ManageArk...` with a real feature request in the body), you MAY skip the confirmation gate and proceed directly to step 0a — the request body itself is the confirmation. Only ask if the invocation is bare (`/hyperresearch-prd` with no body) or if you cannot tell whether the user meant research or PRD.

0a. **Auto-install PRD step skills if missing.** Check that `.claude/skills/hyperresearch-prd-17-initialize/SKILL.md` exists relative to the working directory. If it does not, run `hyperresearch install --steps-only . --json` — this installs the research step skills AND the PRD step skills + 9 PRD subagents in one shot. If the binary isn't on PATH, tell the user to run `pip install hyperresearch` then re-invoke `/hyperresearch-prd`. If the file already exists, the command no-ops cheaply — safe to run unconditionally.

0b. **Inputs check.** You need three things to begin:
   - `feature_request` — the user's verbatim feature ask (GOSPEL — never paraphrase).
   - `research_final_report_path` — path to a completed hyperresearch report, e.g. `research/notes/final_report_<research_tag>.md`. If the user did not run `/hyperresearch` first, surface this as a hard prerequisite and stop. The PRD pipeline assumes the research is done.
   - `prd_directory` — path to the directory holding existing PRDs that describe the current product. Default: `prd/` at the repo root. If the directory is empty or does not exist, step 18 will record `"existing_product_state": "greenfield"` and the pipeline proceeds with an empty inventory.

1. **Archive any prior PRD run's artifacts.** If `prd/scaffold.md`, `prd/prd-decomposition.json`, or `prd/temp/*` exist from a prior run, move them to `prd/runs/archive-<prev-prd-tag>-<UTC-timestamp>/`. Final PRDs (`prd/notes/final_prd_<prd_tag>.md`) and canonical request files (`prd/request-<prd_tag>.md`) are namespaced and stay in place.

2. **Mint a unique prd_tag.** Produce a short topical slug from the feature request — 3–5 lowercase hyphen-separated words, e.g. `parent-attendance-alerts`. Append a random 6-hex-char suffix verified unique against `prd/request-*.md` and `prd/notes/final_prd_*.md` in this repo. Result: `parent-attendance-alerts-9c8f1e`. This is the canonical `prd_tag`.

3. **Persist the feature request file.** Write the verbatim feature request to `prd/request-<prd_tag>.md`:
   ```markdown
   ---
   prd_tag: <slug-with-suffix>
   created: <ISO-8601 timestamp>
   source: user-prompt
   research_final_report_path: <path>
   prd_directory: <path>
   ---

   <verbatim feature request text, character-for-character>
   ```
   Every step skill and every subagent reads this file by path. It is the canonical feature-request reference for the entire pipeline.

4. **Classify PRD modality** — record in the scaffold. This is a label that calibrates step 23's drafting style:
   - **new-feature**: net-new capability inside an existing product surface
   - **enhancement**: extends an existing feature (new field, new state, new action)
   - **cross-cutting**: touches ≥3 modules, requires integration map across many surfaces
   - **persona-expansion**: opens an existing feature to a new persona (e.g., parents get a teacher-only screen)
   - **net-new-area**: introduces a new top-level product area (new module / new menu item)

5. **Write the scaffold.** Write `prd/scaffold.md` (your private planning document — it MUST NOT appear anywhere in the final PRD). Include:
   - Feature Request (VERBATIM — gospel)
   - Research final report path
   - PRD directory path
   - prd_tag, created timestamp
   - Modality classification rationale
   - Tier rationale (filled in after step 17)
   - Wrapper requirements (if any: save path override, naming convention override)

6. **Seed the TodoWrite list.** Create todos for all 14 step skill invocations using their integer step numbers:
   - `Step 17 — Skill: hyperresearch-prd-17-initialize`
   - `Step 18 — Skill: hyperresearch-prd-18-product-inventory`
   - ...
   - `Step 28 — Skill: hyperresearch-prd-28-readability-audit`
   - `Step 29 — Skill: hyperresearch-prd-29-author-diagrams`
   - `Step 30 — Skill: hyperresearch-prd-30-render-html`

   The todo list survives context compaction; it's your durable memory of where you are in the chain.

7. **Invoke step 17:** `Skill(skill: "hyperresearch-prd-17-initialize")`.

After step 17 returns, read `prd/prd-decomposition.json` to learn the tier, then continue invoking step skills per the tier routing table above. After each step's exit criterion is met, mark its todo complete and move to the next.

## Four canonical rules (ALWAYS in force)

1. **NO ARCHITECTURE LEAKAGE.** PRDs are business documents. Every step must filter out:
   - Database schemas, table names, column types, foreign keys
   - API endpoints, HTTP verbs, request/response shapes
   - Programming languages, frameworks, libraries
   - Algorithms, data structures, indexing strategies
   - Deployment topology, scaling decisions, infra choices
   - Caching, queueing, threading, transactions
   When a research source provides architectural detail, **translate** it into user-visible behavior. "Eventually-consistent denormalized view" becomes "users may see a 2-minute lag after publish." "Pub/sub broadcast" becomes "all subscribed teachers get the alert simultaneously." Anything you cannot translate into user-visible language is OUT OF SCOPE for the PRD — flag it as `engineering_decision_deferred` in critic findings, do not include it.

2. **PATCH, NEVER REGENERATE.** After step 23 produces the synthesized PRD (or step 23 single-draft for light tier), the only modifications are surgical Edit hunks from step 26 (patcher) and step 27 (polish-auditor). Both subagents are tool-locked to `[Read, Edit]`. Critic findings that require rewriting a whole section escalate to you as structural issues — not silent rewrites.

3. **CANONICAL FEATURE REQUEST IS GOSPEL.** The verbatim user prompt is persisted to `prd/request-<prd_tag>.md` once and re-read by every subsequent step and every spawned subagent. Wrapper requirements (save path overrides, etc.) are a separate contract captured in the scaffold.

4. **RESPECT THE TIER GATE.** See tier routing table. Don't add steps "for thoroughness." Don't drop steps "for budget." Tier is binding.

## Subagent spawn contract (applies to every Task call)

When a step skill instructs you to spawn a subagent, the prompt you pass MUST include four pieces near the top:

1. **`feature_request` — verbatim, block-quoted** from `prd/request-<prd_tag>.md`. Do not paraphrase, do not summarize.

2. **`research_final_report_path`** — the source-of-truth path for the research that underpins this PRD. Subagents must read it before drafting.

3. **Pipeline position statement.** One sentence naming what step the subagent runs in, what came before, what comes after.

4. **The subagent's specific inputs** (prd_tag, output_path, draft_id, persona, etc.). Each step skill's spawn template documents the required fields.

Skipping any of these in a Task prompt is a process violation.

## Recovery: if you wake up uncertain where you are

Context compaction may eat parts of this conversation. If you're unsure what step you're on:

1. **Check the TodoWrite list.** It carries integer step numbers and survives compaction.
2. **Check disk artifacts.** Each step writes a canonical artifact:
   - Step 17: `prd/scaffold.md`, `prd/prd-decomposition.json`, `prd/temp/coverage-matrix.md`
   - Step 18: `prd/product-inventory.json`
   - Step 19: `prd/feature-decomposition.json`, `prd/temp/scope-envelope.md`
   - Step 20: `prd/integration-map.json`
   - Step 21: `prd/personas.md`, `prd/user-stories.md`
   - Step 22: `prd/flows.md`, `prd/entities.md`
   - Step 23: `prd/temp/draft-{a,b,c}.md` (full) OR `prd/notes/final_prd_<prd_tag>.md` (light)
   - Step 24: `prd/temp/synthesis-plan.md`, `prd/temp/synthesis-outline.md`, `prd/temp/synthesis-pass1.md`, `prd/notes/final_prd_<prd_tag>.md`
   - Step 25: `prd/prd-critic-findings-{business-value,scope-creep,integration-feasibility,instruction}.json`
   - Step 26: `prd/patch-log.json`
   - Step 27: `prd/polish-log.json`
   - Step 28: `prd/readability-recommendations.json`, `prd/readability-decisions.json`
   - Step 29: `prd/diagram-log.json` (and the final PRD file now contains Mermaid blocks)
   - Step 30: `prd/notes/final_prd_<prd_tag>.html`, `prd/html-render-log.json`
3. **Find the highest-numbered step whose artifact exists.** Resume from the next step.
4. **Re-invoke this entry skill** if you've lost track entirely: `Skill(skill: "hyperresearch-prd")`. It loads fresh.

## Final integrity gate (after step 30)

Before declaring the run complete, verify every expected artifact exists. The required set depends on the tier:

- **light tier:** `prd/notes/final_prd_<prd_tag>.md`, `prd/notes/final_prd_<prd_tag>.html`, `prd/polish-log.json`, `prd/readability-recommendations.json`, `prd/readability-decisions.json`, `prd/diagram-log.json`, `prd/html-render-log.json`.
- **full tier:** all light-tier artifacts PLUS the 4 critic findings, patch-log.json, comparisons/integration-map/personas/user-stories/flows/entities.

If any artifact is missing, the responsible step failed silently. Re-spawn the responsible agent ONCE; if it fails again, write a minimal stub and log the failure before proceeding.

## Invariants you cannot break

1. **No architecture in the PRD.** This is the prime invariant. Re-read the four rules.
2. **The feature request file is canonical.** Never edit `prd/request-<prd_tag>.md` after step 17 writes it.
3. **Patcher and polish-auditor are Read+Edit only.** Tool-lock is enforced at the Claude Code allowlist level; bypassing it is a critical violation.
4. **One PRD per prd_tag.** The 6-hex suffix guarantees no overwrite across runs.
5. **Existing PRD directory is read-only during the run.** Step 18 only READS the inventory. Never mutate existing PRD files from this pipeline.

## Final deliverable

When step 30 finishes, the artifact the user opens is:
- **HTML PRD: `prd/notes/final_prd_<prd_tag>.html`** (self-contained, diagrams render as SVG via Mermaid)
- Markdown source of truth: `prd/notes/final_prd_<prd_tag>.md`

## Now begin

Execute the bootstrap (steps 0–6 above), then invoke `Skill(skill: "hyperresearch-prd-17-initialize")`.
