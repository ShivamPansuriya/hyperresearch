---
name: hyperresearch-prd-25-critics
description: >
  Step 25 of the hyperresearch-PRD pipeline. Spawns 4 adversarial
  critics in parallel against the synthesized PRD: business-value,
  scope-creep, integration-feasibility (business lens), and
  instruction-following. Each critic produces an independent findings
  JSON that the patcher (step 26) consumes. Critics never modify the
  draft directly. Full tier only.
---

# Step 25 — Four adversarial PRD critics in parallel

**Tier gate:** Full tier ONLY.

**Goal:** every PRD has blind spots. Four critics with different value functions read the synthesized PRD against the original feature request, the inventory, and the research final report, and produce structured findings. The patcher in step 26 applies critic findings as surgical Edit hunks.

**Why this step exists:** asking the synthesizer to self-review produces only cosmetic suggestions. Independent critics with different objectives find substantive omissions, scope creeps, instruction-following misses, and integration mismatches that a single author cannot see.

## Recover state

- `prd/notes/final_prd_<prd_tag>.md` (from step 24)
- All prior step artifacts.

## Step 25.1 — Spawn all four critics in parallel

Spawn ALL four in ONE message. Each gets the same draft path; the value function and findings schema differ.

### Critic 1 — prd-business-value-critic

**Spawn template:**
```
subagent_type: prd-business-value-critic
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  REQUEST FILE: prd/request-<prd_tag>.md

  PIPELINE POSITION: You are one of 4 step-25 critics in the
  hyperresearch-PRD pipeline. The synthesized PRD is at the draft
  path. After all 4 critics return, step 26 (patcher) applies your
  findings as Edit hunks. You do NOT edit the draft yourself.

  YOUR ROLE: business-value critic. You audit whether the PRD:
  - Makes the user-pain explicit and concrete (not vague).
  - States a measurable business outcome the feature is supposed to move.
  - Lists success metrics that are user-visible and business-meaningful
    (adoption, retention, completion rate, CSAT, time-saved) — not vanity.
  - Has a defensible Future scope section (each item linked to a current
    constraint or known pain).
  - Avoids feature-bloat — every in-scope capability traces back to a
    user pain or a stated business outcome.

  YOUR INPUTS:
  - draft_path: prd/notes/final_prd_<prd_tag>.md
  - feature_decomposition_path: prd/feature-decomposition.json
  - research_final_report_path: <from scaffold>
  - findings_path: prd/prd-critic-findings-business-value.json

  Write findings as JSON. Schema:
  {
    "critic": "business-value",
    "findings": [
      {
        "severity": "high | medium | low",
        "anchor": "<exact short quote from the PRD identifying location>",
        "problem": "<one paragraph>",
        "fix_direction": "<paragraph describing the change at the level of intent — not exact wording>"
      }
    ]
  }
```

### Critic 2 — prd-scope-creep-critic

```
subagent_type: prd-scope-creep-critic
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  PIPELINE POSITION: step-25 scope-creep critic.

  YOUR ROLE: detect any capability, persona, or entity in the PRD
  that is NOT in feature-decomposition.scope_envelope.in_scope or
  prd-decomposition.atomic_items. Scope creep adds work to the dev
  team and dilutes the value moment.

  Also detect the reverse: any in-scope item that the PRD silently
  dropped.

  YOUR INPUTS:
  - draft_path: prd/notes/final_prd_<prd_tag>.md
  - feature_decomposition_path: prd/feature-decomposition.json
  - prd_decomposition_path: prd/prd-decomposition.json
  - findings_path: prd/prd-critic-findings-scope-creep.json

  Findings schema same as business-value critic. Each finding names
  the creep item or dropped item by ID where possible.
```

### Critic 3 — prd-integration-feasibility-critic (business lens)

```
subagent_type: prd-integration-feasibility-critic
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  PIPELINE POSITION: step-25 integration-feasibility critic.

  YOUR ROLE: read the PRD against product-inventory.json and
  integration-map.json. Flag:
  - References to a screen / surface / module that does not appear
    in the inventory.
  - Persona names or vocabulary that contradict the inventory's
    canonical terms.
  - Cross-persona handoffs that contradict the product's existing
    notification or permission pattern.
  - User-visible expectations that contradict the product's existing
    behavior (e.g., "real-time" when the product's pattern is
    digest-based).

  CRITICAL: you are a BUSINESS critic, not a technical reviewer. You
  flag integration mismatches at the user-visible behavior level
  only. Do NOT make architecture claims ("this needs a new
  microservice"). Engineering owns implementation.

  YOUR INPUTS:
  - draft_path: prd/notes/final_prd_<prd_tag>.md
  - product_inventory_path: prd/product-inventory.json
  - integration_map_path: prd/integration-map.json
  - findings_path: prd/prd-critic-findings-integration-feasibility.json

  Findings schema same as above.
```

### Critic 4 — prd-instruction-critic

```
subagent_type: prd-instruction-critic
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  PIPELINE POSITION: step-25 instruction-following critic.

  YOUR ROLE: read the PRD against prd-decomposition.json. Flag any
  case where:
  - A `required_section_headings` heading is missing, misspelled,
    or out of order.
  - A `capabilities` atomic item is missing from the PRD.
  - A `personas_in_scope` item is missing from the Personas section.
  - An `entities_implied` item is missing from the entities section.
  - A `constraints` item is not respected somewhere in the PRD.
  - The `prd_format` length contract is violated (too short / too long
    by more than 20%).
  - The `out_of_scope` section is missing items that decomposition
    flagged as explicit_out_of_scope.

  Also flag architecture-leak language and pipeline-vocabulary leaks
  ("scaffold", "atomic items", "coverage matrix", "prd-decomposition",
  "hyperresearch", "synthesis plan").

  YOUR INPUTS:
  - draft_path: prd/notes/final_prd_<prd_tag>.md
  - prd_decomposition_path: prd/prd-decomposition.json
  - feature_decomposition_path: prd/feature-decomposition.json
  - findings_path: prd/prd-critic-findings-instruction.json

  Findings schema same as above. Severity: high for missing headings or
  missing required items; medium for length violations or vocabulary
  leaks; low for stylistic suggestions.
```

## Step 25.2 — Wait + read findings

While the 4 critics run, append observations to `prd/temp/orchestrator-notes.md`. Do NOT emit bare text. One vault check per minute max.

After all 4 return, confirm:
- `prd/prd-critic-findings-business-value.json`
- `prd/prd-critic-findings-scope-creep.json`
- `prd/prd-critic-findings-integration-feasibility.json`
- `prd/prd-critic-findings-instruction.json`

All exist. Each parses as valid JSON. Each has a `findings` array (may be empty if the critic found nothing — but log if a critic returned empty across the board, that's often a hidden failure).

## Step 25.3 — Triage and prioritize

Read all 4 findings JSONs. Tag each finding:
- **patch-doable** — fits a small Edit hunk. Step 26 (patcher) handles.
- **gap-fetch** — finding requires new information not in the current artifacts. If the gap is from research, the user must re-run /hyperresearch with a refined query — surface as a "research gap" warning. If the gap is from the inventory (missing PRD context), surface as an "inventory gap" warning. The PRD will ship with the gap acknowledged.
- **structural** — finding requires rewriting a section or restructuring headings. Step 26 escalates these to the orchestrator (you) for hand-written Edits.
- **dismiss** — critic is wrong or off-scope. Note the dismissal rationale.

Write the triage to `prd/temp/critic-triage.md`.

## Exit criterion

- All 4 critic findings JSONs exist.
- `prd/temp/critic-triage.md` exists with a tag on every finding.

## Next step

Return to the entry skill. Invoke step 26:

```
Skill(skill: "hyperresearch-prd-26-patcher")
```
