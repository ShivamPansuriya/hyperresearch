---
name: hyperresearch-prd-23-triple-draft
description: >
  Step 23 of the hyperresearch-PRD pipeline. For full tier: spawns 3
  prd-draft-orchestrator subagents in parallel, each writing one
  angle-specific PRD draft. For light tier: writes a single PRD
  draft directly to final_prd_<prd_tag>.md and skips ahead to step
  27. Runs for all tiers.
---

# Step 23 — Triple-draft ensemble (PRD edition)

**⚠ CRITICAL ANTI-PATTERN: Writing a single draft for `full` tier is a PIPELINE VIOLATION.** Full-tier MUST spawn 3 prd-draft-orchestrator subagents. Step 24 (synthesizer) consumes all 3 and writes the final report. If you find yourself about to write `prd/notes/final_prd_<prd_tag>.md` directly without spawning 3 subagents, STOP. Re-read this skill. Spawn the sub-orchestrators. (Light tier is the ONE exception — see "Light tier" section below.)

**Tier gate:** Runs for ALL tiers. For `light`: write a single draft directly to `prd/notes/final_prd_<prd_tag>.md` and skip ahead to step 27 (polish). After writing, verify word count is within ±20% of the target band middle for the prd_format. If under the floor, run ONE expansion pass that adds user stories, acceptance criteria, or edge cases drawn from prior-step artifacts (do not invent); then exit. For `full`: run the triple-draft ensemble below — step 24 (synthesizer) will turn the 3 drafts into the final PRD.

**Goal:** produce THREE independent angle-specific PRD drafts (`draft-{a,b,c}.md`). Step 24 consumes all three and writes the final PRD.

## Recover state

- All prior step artifacts exist: `prd-decomposition.json`, `product-inventory.json`, `feature-decomposition.json`. Full tier additionally has `integration-map.json`, `personas.md`, `user-stories.md`, `flows.md`, `entities.md`.

## Step 23.0 — Read prd_format and required_section_headings

Read `prd_format` and `required_section_headings` from `prd/prd-decomposition.json`. These are binding on every draft:

| Format | Target length | Character |
|--------|-------------|-----------|
| `"one_pager"` | 300–800 words | Direct, compact, ship-it tone |
| `"standard_prd"` | 1500–4000 words | Scannable, all major sections, breadth-first |
| `"detailed_prd"` | 4000–8000 words | Dense, per-persona sections, edge-case appendix, phased rollout |

**Length discipline:** Target the MIDDLE of the range. Under-length loses on comprehensiveness; over-length dilutes good content.

Every draft must use the literal H2 headings from `required_section_headings`, in order, with EXACT spelling and EXACT capitalization. Title-casing a heading that is written in sentence case (e.g., `User stories` → `User Stories`) is a violation. Each draft orchestrator must validate its draft's headings against the list before exiting.

## Light tier ONLY: single-draft path

If `pipeline_tier == "light"`: SKIP step 23.1 — 23.4 below and follow this section instead.

**Light tier writes a single PRD directly to `prd/notes/final_prd_<prd_tag>.md`.** No subagents, no triple-draft ensemble, no synthesizer.

1. **Read inputs directly:**
   - `prd/request-<prd_tag>.md` (verbatim feature request)
   - The research final report at the path in scaffold
   - `prd/feature-decomposition.json`
   - `prd/product-inventory.json`
   - `prd/prd-decomposition.json` (for required_section_headings + prd_format)

2. **Honor the structural contract.**
   - Use the literal H2 headings from `required_section_headings`, in order.
   - Hit the length target from the table above (light typically pairs with `one_pager` or `standard_prd`).
   - Apply the modality calibration from `prd/scaffold.md`.

3. **Write the PRD.** Use the section guide below as a checklist (matched to the headings):
   - **Overview** — 1 paragraph: the problem, the user pain, the one-sentence answer this feature gives.
   - **User-visible change / Goals & non-goals** — what users will see different after this ships; what we explicitly are NOT solving.
   - **Personas** (if section is required) — pull from `feature-decomposition.personas_in_scope` and `product-inventory.canonical_personas`. One short profile each.
   - **User stories / User-visible change** — 3–8 user stories in `As a / I want / so that` form.
   - **User flow** — short numbered flow describing the user's experience.
   - **User-visible entities & fields** — name the entities and list their user-visible fields.
   - **Integration with existing product** — describe in user-visible terms which existing surfaces this feature plugs into.
   - **Acceptance criteria** — bulleted, observable, user-visible.
   - **Out of scope** — copy `scope_envelope.out_of_scope`.
   - **Future scope** — copy `scope_envelope.future_scope` with rationale.
   - **Success metrics** — user-visible, business-outcome metrics. Adoption %, repeat-use %, time-saved (self-reported), CSAT, completion rate.

4. **Citations / references.** If the PRD draws a specific claim from the research final report, reference it inline as `(see research: <section title>)`. No formal citation block needed — the research final report is one document, paths captured in scaffold.

5. **Hygiene.** No YAML frontmatter on the final PRD. No pipeline vocabulary in prose ("hyperresearch", "prd-decomposition", "scaffold", "atomic items", "coverage matrix"). No architecture vocabulary (DB / API / service / queue / cache).

6. **Exit and route.** Once `prd/notes/final_prd_<prd_tag>.md` is written, return to the entry skill and invoke `Skill(skill: "hyperresearch-prd-27-polish")`. Light tier skips steps 24–26 entirely.

## Step 23.1 — Define 3 analytical angles (full tier)

Pick 3 angles that pull the PRD in genuinely different directions. The synthesizer in step 24 will reconcile them into the final document. Recommended angle set for PRDs:

- **Angle A — User value:** lead with the user pain and the value moment. Personas and user stories are the spine; flows and entities are in service of the stories. Strongest when the feature is a UX improvement or a new persona-facing capability.
- **Angle B — Business outcome:** lead with the metric the feature exists to move (engagement, adoption, retention, school admin satisfaction, regulatory compliance). Success metrics, out-of-scope, and phased rollout get heavier emphasis.
- **Angle C — Integration story:** lead with how the feature plugs into the existing product surface. Integration map, entity reuse, vocabulary fit, and cross-persona handoffs get heavier emphasis. Strongest for cross-cutting or persona-expansion features.

If the feature is heavily compliance / safety / regulatory, swap angle C for **Angle C' — Risk & guardrails:** lead with the constraints and guardrails (consent, age-appropriate content, parental visibility, audit trail user-visibility), and frame everything else as serving those constraints.

Pick the three angles best suited to the feature's modality. Record your choice and rationale in `prd/temp/angle-assignment.md`.

## Step 23.2 — Curate per-angle source material

For each angle, write a short "must include" list pulled from prior-step artifacts:

```markdown
## Draft A — User value
Must-include source material:
- From prd/user-stories.md: stories S1.1, S1.2, S2.1 (highest-impact stories).
- From prd/personas.md: full profiles for personas P1, P2.
- From prd/flows.md: flow F1 verbatim; F2 as a 3-bullet summary.
- From research final report: <section title>, <paragraph reference>.

## Draft B — Business outcome
Must-include source material:
- From prd/feature-decomposition.json scope_envelope: full in_scope + out_of_scope + future_scope.
- From research final report: <section about adoption / market / outcomes>.
- From product-inventory.json: success patterns of analogous features (if listed).

## Draft C — Integration story
Must-include source material:
- From prd/integration-map.json: capability_touchpoints + cross_persona_handoffs in full.
- From prd/entities.md: full entity field tables.
- From product-inventory.json: canonical_modules + vocabulary preferred_terms.
```

Write to `prd/temp/draft-{a,b,c}-source-list.md`.

## Step 23.3 — Spawn 3 prd-draft-orchestrators in parallel

**Spawn 3 `prd-draft-orchestrator` subagents in ONE message.** True parallel execution. Each gets a different `draft_id`, `analytical_angle`, and (CRUCIALLY) a different `must_read_paths` array.

**Spawn template:**
```
subagent_type: prd-draft-orchestrator
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  RESEARCH FINAL REPORT PATH: <path from scaffold>
  REQUEST FILE: prd/request-<prd_tag>.md

  PIPELINE POSITION: You are one of 3 parallel step 23 sub-orchestrators
  in the hyperresearch-PRD pipeline. After you and the other two return,
  the main orchestrator runs step 24 (synthesizer subagent) which reads
  all 3 drafts and writes the final PRD. Your draft is an INPUT to that
  synthesis, not the final output.

  YOUR INPUTS:
  - request_file_path: prd/request-<prd_tag>.md
  - prd_tag: <prd_tag>
  - draft_id: "a" (or "b" or "c")
  - output_path: prd/temp/draft-a.md (or draft-b.md or draft-c.md)
  - analytical_angle: "<the 2-3 sentence angle assignment>"
  - must_read_paths: [<list of file paths from draft-<x>-source-list.md>]
  - research_final_report_path: <path>
  - feature_decomposition_path: prd/feature-decomposition.json
  - product_inventory_path: prd/product-inventory.json
  - integration_map_path: prd/integration-map.json
  - personas_path: prd/personas.md
  - user_stories_path: prd/user-stories.md
  - flows_path: prd/flows.md
  - entities_path: prd/entities.md
  - relevant_skills_path: prd/relevant-skills.json
  - required_section_headings: [<exact list>]
  - prd_format: "<one_pager|standard_prd|detailed_prd>"
  - modality: "<new-feature|enhancement|cross-cutting|persona-expansion|net-new-area>"

  Read every file on must_read_paths before writing. Do NOT survey
  the PRD directory beyond what's listed. Do NOT introduce new
  capabilities, personas, or entities not in feature-decomposition.
  Write your draft from your assigned angle, in the literal section
  headings provided. No architecture, no schemas, no APIs.
```

**CRITICAL: never emit bare text while the 3 sub-orchestrators are running.** They will take 3–10 minutes each. Use this time to think — append notes to `prd/temp/orchestrator-notes.md` about the synthesis you'll plan in step 24: what's the strongest thesis emerging across angles? Which atomic items will be contentious? Which user-visible behaviors must the final draft commit to? One file check per minute max. Write thoughts, don't just poll.

## Step 23.4 — Validate that all 3 drafts came back

After all 3 subagents return:

1. Confirm `prd/temp/draft-a.md`, `prd/temp/draft-b.md`, `prd/temp/draft-c.md` exist.
2. Confirm each draft has every `required_section_headings` as an H2 heading, in order. If a draft is missing a heading, re-spawn that one subagent with explicit instruction to add the missing section. Re-spawn ONCE; if it still misses, log the failure and let step 24's synthesizer plug the gap from the other two drafts.
3. Confirm each draft is within ±25% of the target length range. If a draft is wildly off, log it; step 24 will reconcile.

## Exit criterion (full tier)

- `prd/temp/draft-a.md`, `prd/temp/draft-b.md`, `prd/temp/draft-c.md` all exist.
- Each has the required section headings.
- `prd/temp/angle-assignment.md` records which angle each draft id used.

## Next step

Return to the entry skill.

- **light tier:** invoke step 27 (`hyperresearch-prd-27-polish`).
- **full tier:** invoke step 24 (`hyperresearch-prd-24-synthesize`).
