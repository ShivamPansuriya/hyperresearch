---
name: hyperresearch-prd-24-synthesize
description: >
  Step 24 of the hyperresearch-PRD pipeline. Reads the 3 angle-specific
  PRD drafts from step 23, spot-checks factual conflicts, writes a
  synthesis plan + outline, then spawns ONE prd-synthesizer subagent
  (Read+Write tool-locked) that writes the final PRD in TWO passes —
  pass 1 rough integrated draft, pass 2 voice/redundancy/length
  cleanup. Skipped for light tier (which writes a single draft
  directly in step 23). Full tier only.
---

# Step 24 — PRD synthesizer (two-pass integration)

**Tier gate:** Full tier ONLY. Light tier already wrote the final draft in step 23 and skipped here.

**Goal:** the 3 angle-drafts each have unique strengths and overlapping weaknesses. The synthesizer reads all three and produces ONE final PRD in ONE voice — not section-grafted from the inputs, but rewritten as a coherent whole.

**Why this step exists:** if you just stitched together the best paragraphs from drafts A/B/C, you'd get a Frankenstein PRD with voice shifts, repeated arguments, and structural inconsistency. Two passes — rough integration, then aggressive cleanup — gives the final document one consistent voice and tight argumentative density.

## Recover state

- `prd/temp/draft-a.md`, `draft-b.md`, `draft-c.md` (from step 23)
- All upstream artifacts available.

## Step 24.1 — Read all 3 drafts + spot-check conflicts

Read all 3 drafts in full. Build a conflict log at `prd/temp/synthesis-conflicts.md`:

```markdown
## Cross-draft conflicts

### Conflict 1
- Draft A claims: <X>
- Draft B claims: <Y>
- Draft C claims: <Z>
- Resolution: <which draft is right, or merge approach>
- Justification: <pull from prior artifacts or research final report>
```

Typical PRD conflicts:
- Different acceptance criteria phrasings for the same capability — pick the most user-visible.
- Different persona vocabulary — go with the canonical from product-inventory.
- Different entity field lists — superset, but only if every added field is justified by feature-decomposition.
- Different success metrics — pick the most user/business-outcome oriented; drop vanity metrics.
- Different out-of-scope or future-scope items — superset, dedupe.

If a conflict can't be resolved from artifacts, decide via the canonical feature request: which interpretation best honors the request's verbatim wording?

## Step 24.2 — Write the synthesis plan

Write `prd/temp/synthesis-plan.md`:

```markdown
## Synthesis plan

**Lead angle:** <A | B | C> — because <why this angle's framing best serves the request>.

**Borrow from other drafts:**
- From draft <X>: the section on <Y> — because <reason>.
- From draft <Z>: the framing of <thing> — because <reason>.

**Drop:**
- <Section / claim from draft Y> — because <reason: redundant / off-scope / wrong>.

**Conflict resolutions:** see synthesis-conflicts.md.

**Voice target.** <e.g., "Business-stakeholder friendly. Active voice. Short sentences. Avoid hedge words.">

**Length target.** <middle of the range for prd_format>.

**Required section order (binding):** <list from prd-decomposition.required_section_headings>.

**Argumentative density commitment.** For each in-scope capability, the PRD must include: (1) one explicit user story, (2) one user-visible acceptance signal, (3) one explicit linkage to a persona, (4) at least one entity or flow reference. Density check happens in pass 2.
```

## Step 24.3 — Write the synthesis outline

Write `prd/temp/synthesis-outline.md` with the literal section headings and 2–4 bullets each on what content goes in. This is the synthesizer's structural anchor.

## Step 24.4 — Spawn the prd-synthesizer subagent

Single spawn. Tool-locked to `[Read, Write]`.

**Spawn template:**
```
subagent_type: prd-synthesizer
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  REQUEST FILE: prd/request-<prd_tag>.md

  PIPELINE POSITION: You are step 24 (synthesizer) of the hyperresearch-PRD
  pipeline. Step 23 wrote 3 angle-specific drafts (draft-a/b/c.md). After
  you write the final PRD, step 25 will spawn 4 adversarial critics
  against it. You are tool-locked to [Read, Write]. You write the
  final PRD in two passes — pass 1 rough integration, pass 2 cleanup.

  YOUR INPUTS:
  - request_file_path: prd/request-<prd_tag>.md
  - draft_paths: ["prd/temp/draft-a.md", "prd/temp/draft-b.md", "prd/temp/draft-c.md"]
  - synthesis_plan_path: prd/temp/synthesis-plan.md
  - synthesis_outline_path: prd/temp/synthesis-outline.md
  - conflicts_path: prd/temp/synthesis-conflicts.md
  - decomposition_path: prd/prd-decomposition.json
  - feature_decomposition_path: prd/feature-decomposition.json
  - product_inventory_path: prd/product-inventory.json
  - integration_map_path: prd/integration-map.json
  - personas_path: prd/personas.md
  - user_stories_path: prd/user-stories.md
  - flows_path: prd/flows.md
  - entities_path: prd/entities.md
  - relevant_skills_path: prd/relevant-skills.json
  - research_final_report_path: <from scaffold>
  - output_path: prd/notes/final_prd_<prd_tag>.md
  - pass1_path: prd/temp/synthesis-pass1.md
  - required_section_headings: [<exact list>]
  - prd_format: "<one_pager|standard_prd|detailed_prd>"
  - target_word_count: <middle of range>

  PASS 1: write a rough integrated draft to pass1_path. Use the
  synthesis plan to choose lead angle and borrowed sections. Honor
  required_section_headings exactly.

  PASS 2: read pass1_path back. Cut voice shifts. Cut redundancy.
  Tighten argument density (every capability gets story + acceptance
  + persona + entity/flow). Trim or expand to hit target_word_count.
  Write the final result to output_path.

  STRICT RULES:
  - No architecture vocabulary (DB / schema / API / endpoint / queue /
    cache / service / latency-as-SLA / framework / library / language).
  - No pipeline vocabulary in prose ("hyperresearch", "prd-decomposition",
    "scaffold", "atomic items", "coverage matrix").
  - No new capabilities, personas, or entities beyond what
    feature-decomposition.in_scope authorizes.
  - Use canonical vocabulary from product-inventory.preferred_terms.
  - The required section headings appear in the exact order and
    spelling specified.
  - The PRD has NO YAML frontmatter at the top.
```

**CRITICAL: never emit bare text while the synthesizer is running.** Append integration notes to `prd/temp/orchestrator-notes.md` while waiting. One file check per minute max.

## Step 24.5 — Validate the synthesized PRD

After the synthesizer returns:

1. Confirm `prd/notes/final_prd_<prd_tag>.md` exists.
2. Verify all `required_section_headings` appear as H2, in order, exact spelling.
3. Verify word count is within ±20% of the target.
4. Run the architecture-leak grep on the file: search for "API", "endpoint", "database", "schema", "table", "queue", "cache", "service layer", "microservice", "JSONB", "VARCHAR", "INT", "foreign key", "p99", "p95", "QPS". Each hit is a violation. If ≥3 hits, re-spawn the synthesizer with explicit instruction to strip leaks. If 1–2 hits, mark them for step 26 (patcher) to clean.
5. Verify no YAML frontmatter at the top.
6. Verify no pipeline vocabulary in prose (`prd-decomposition`, `scaffold`, `coverage matrix`, `atomic items`).

## Exit criterion

- `prd/notes/final_prd_<prd_tag>.md` exists.
- All required section headings present in order, with exact spelling and capitalization.
- Word count within ±20% of target band middle. If the synthesized PRD is below the floor, the synthesizer's pass 2 must EXPAND under-developed sections (typically User stories, Acceptance criteria, Edge cases) using material already present in the 3 drafts; pass 2 is not exclusively a cutting pass.
- Validation gate passes (or remaining violations are minor and logged for step 26).

## Next step

Return to the entry skill. Invoke step 25:

```
Skill(skill: "hyperresearch-prd-25-critics")
```
