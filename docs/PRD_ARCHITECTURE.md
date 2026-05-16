# PRD Extension Architecture

How the 12-step PRD pipeline is wired and why each piece exists. Reader: someone modifying or extending the pipeline.

## Origin

Hyperresearch (steps 1–16) produces an adversarially-audited research report. PRD generation is structurally similar: a canonical input is decomposed, a corpus is gathered (the existing PRD directory + the research final report instead of web sources), drafts are written from multiple angles, a synthesizer integrates them, critics audit, a patcher fixes, polish and readability finalize.

The extension reuses the same machinery (skill-chain orchestration, tool-locked subagents, patch-never-regenerate, canonical-input-is-gospel) but with PRD-specific value functions in the critics, PRD-specific section contracts in step 17, and PRD-specific drafting angles in step 23.

## Skill chain layout

```
hyperresearch-prd                       ← entry router (skill)
├── hyperresearch-prd-17-initialize     ← decompose feature request, classify tier
├── hyperresearch-prd-18-product-inventory  ← scan PRD directory
├── hyperresearch-prd-19-feature-decomposition  ← reconcile with inventory
├── hyperresearch-prd-20-integration-map        ← full-tier only
├── hyperresearch-prd-21-personas-stories       ← full-tier only
├── hyperresearch-prd-22-flows-entities         ← full-tier only
├── hyperresearch-prd-23-triple-draft           ← light: single; full: 3 parallel
├── hyperresearch-prd-24-synthesize             ← full-tier only
├── hyperresearch-prd-25-critics                ← full-tier only (4 parallel)
├── hyperresearch-prd-26-patcher                ← full-tier only (Read+Edit only)
├── hyperresearch-prd-27-polish                 ← Read+Edit only
└── hyperresearch-prd-28-readability-audit      ← Read+Write only, orchestrator applies
```

Each step file:
- has YAML frontmatter with `name` and `description` (Claude Code skill metadata)
- starts with `# Step N — <title>`
- has a `Recover state` section so the orchestrator can resume after compaction
- ends with an `Exit criterion` and `Next step` block

The router (`hyperresearch-prd`) does not contain step procedures; it tells the orchestrator which Skill to invoke at each tier-routing branch.

## Subagent roster

Defined in `src/hyperresearch/agents/prd/*.md`. Each file is the prompt + tool-lock declaration the Claude Code subagent receives.

| Agent                                | Tool lock        | Role                                                                 |
|--------------------------------------|------------------|----------------------------------------------------------------------|
| `prd-draft-orchestrator`             | Read/Write/Bash  | Writes one angle-specific draft. Spawned 3× in parallel.             |
| `prd-synthesizer`                    | Read+Write only  | Two-pass write: rough integration → voice/density cleanup.           |
| `prd-business-value-critic`          | Read+Write only  | Flags vague pain, vanity metrics, feature-bloat.                     |
| `prd-scope-creep-critic`             | Read+Write only  | Flags out-of-scope additions + in-scope drops.                       |
| `prd-integration-feasibility-critic` | Read+Write only  | Flags vocabulary mismatches, surface name errors, UX pattern breaks. |
| `prd-instruction-critic`             | Read+Write only  | Flags missing/misordered headings, length violations, vocab leaks.   |
| `prd-patcher`                        | **Read+Edit only** | Applies critic findings as surgical Edit hunks.                     |
| `prd-polish-auditor`                 | **Read+Edit only** | Final hygiene + filler pass.                                        |
| `prd-readability-recommender`        | Read+Write only  | Writes JSON suggestions; orchestrator applies via Edit.              |

The two Read+Edit tool-locks are the heart of "patch, never regenerate." They are enforced at the Claude Code allowlist level — those agents cannot Write a new file. The orchestrator pre-stubs `prd/patch-log.json` and `prd/polish-log.json` so the tool-locked agents can Edit into them.

## Artifact contract

The pipeline communicates between steps exclusively through files. No in-memory hand-off. Every step:
- reads its inputs from files written by prior steps
- writes its outputs to canonical paths
- exits

This makes the pipeline resumable: at any point, an orchestrator (or the user) can re-invoke a step skill and it will pick up state from disk.

Canonical paths are listed in the entry skill's "Recovery" section and in the per-step "Recover state" sections.

## Inputs the pipeline reads

1. **Feature request** — verbatim, passed in the `/hyperresearch-prd <text>` invocation. Persisted to `prd/request-<prd_tag>.md` by the entry skill bootstrap, then re-read by every step.
2. **Research final report** — path inferred from `research/notes/final_report_*.md` or specified in the feature request. Read by step 17 (light reading), step 21 (for persona color), step 23 (each angle-draft reads it), and the synthesizer.
3. **Existing PRD directory** — `prd/` (or wherever the scaffold says). Scanned by step 18.

The pipeline does NOT fetch from the web. All evidence comes from the prior research run.

## Tier routing logic

Step 17 produces `prd/prd-decomposition.json` containing `pipeline_tier`. The entry skill reads this file after step 17 and routes:

- `light`: `17 → 18 → 19 → 23 (single-draft branch) → 27 → 28`
- `full`: `17 → 18 → 19 → 20 → 21 → 22 → 23 (triple-draft branch) → 24 → 25 → 26 → 27 → 28`

Step 23 has internal branching based on `pipeline_tier` — same skill file, different code path inside it.

Step 27 (polish) and step 28 (readability) run for BOTH tiers. The integrity gate inside step 27 has tier-aware artifact-presence checks.

## Architecture-leak guard

A PRD is a business document. The four most common leaks are:

1. Database schema vocabulary (`schema`, `table`, `column`, `foreign key`, `JSONB`, `VARCHAR`)
2. API vocabulary (`API`, `endpoint`, `route`, `handler`, `GET`, `POST`)
3. Infra vocabulary (`queue`, `cache`, `microservice`, `service layer`, `pub/sub`)
4. Performance vocabulary as SLAs (`p99`, `QPS`, `99.9% uptime`)

The pipeline guards against these at four points:
- Step 20 (integration map) has an explicit "sanity gate" grep.
- Step 22 (flows & entities) has an explicit grep.
- The `prd-synthesizer` is instructed to scrub during pass 2.
- The `prd-instruction-critic` (step 25) flags surviving leaks.
- The `prd-polish-auditor` (step 27) does a final scrub.

Any leak that reaches the final PRD is a bug in one of those five guards.

## Pipeline-vocabulary leak guard

Words like `scaffold`, `coverage matrix`, `atomic items`, `prd-decomposition`, `synthesis plan`, `triple draft`, `critic findings`, `patch log`, `polish log`, `draft a/b/c` belong to the pipeline's internal vocabulary. They MUST NOT appear in the final PRD. Same five-point guard applies.

## Extension points

If you want to add a new critic in step 25:
1. Write the subagent file in `src/hyperresearch/agents/prd/prd-<name>-critic.md`.
2. Add its name to `PRD_SUBAGENTS` in `src/hyperresearch/core/prd_install.py`.
3. Add a spawn block in `src/hyperresearch/skills/hyperresearch-prd-25-critics.md`.
4. Update `src/hyperresearch/skills/hyperresearch-prd-26-patcher.md`'s `critic_findings_paths` list and the integrity gate in step 27.
5. Re-run `hyperresearch prd-install .` to copy the new files into Claude Code.

If you want to add a new prd_format (e.g., `mini_prd` for ≤200 word internal memos):
1. Add the format to step 17's classification table and `required_section_headings` defaults.
2. Add a length band to step 23's "Step 23.0 — Read prd_format" table.
3. Add it to the synthesizer's `target_word_count` calibration.

If you want to add a new tier (e.g., `xl` for compliance PRDs that need 5 critics and 2 patcher passes):
1. Update the entry skill's tier-routing table.
2. Update step 17's tier-classification rules.
3. Define the additional steps and wire them into the chain.

## Why no "vault" for PRDs

The research pipeline uses a SQLite-backed vault to store ~hundreds of source notes that compound across sessions. The PRD pipeline doesn't need that — its evidence corpus is bounded (one research report + N existing PRDs). Files on disk are enough. If you want PRD-level history across many runs, look at `prd/runs/archive-*/` directories — the entry skill bootstrap automatically archives prior runs by `prd_tag`.

## Why no fetcher

The research pipeline fetches web sources via the `hyperresearch-fetcher` subagent. PRDs don't need that — they synthesize from the research report. If a critic in step 25 says "the PRD needs evidence the research didn't cover," the resolution is to re-run `/hyperresearch` with a refined query, not to grow the PRD pipeline.

## Why the synthesizer is two-pass

A single-pass synthesizer reading three drafts tends to stitch sections together with abrupt voice shifts. Pass 1 produces a rough integrated draft. Pass 2 reads its own output back and rewrites for one consistent voice, redundancy removal, and argumentative density. Same pattern the research synthesizer uses.

## Why the readability recommender doesn't Edit

Same reason as the research pipeline: separating recommendation from application gives the orchestrator a chance to decline reformatting suggestions that would re-introduce architecture vocabulary or shrink the PRD below its format minimum. The recommender's job is to see opportunities; the orchestrator's job is to apply judgment.
