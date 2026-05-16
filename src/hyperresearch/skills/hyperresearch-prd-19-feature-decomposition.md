---
name: hyperresearch-prd-19-feature-decomposition
description: >
  Step 19 of the hyperresearch-PRD pipeline. Refines the atomic
  decomposition from step 17 by reconciling it with the existing
  product inventory from step 18. Produces feature-decomposition.json
  with deduplicated capabilities, normalized vocabulary, and an
  explicit scope envelope (in / adjacent / out). Runs for all tiers.
---

# Step 19 — Feature decomposition reconciled with product context

**Tier gate:** Runs for ALL tiers.

**Goal:** convert the raw atomic items from step 17 into product-aware feature requirements by reconciling against the inventory from step 18. The output is the working spec the rest of the pipeline writes against.

**Why this step exists:** the step-17 decomposition was done in isolation from the rest of the product. Step 18 mapped the product. Step 19 is the merge — it deduplicates, renames things to match canonical vocabulary, and draws a sharp line around what's in scope for THIS PRD.

## Recover state

- `prd/prd-decomposition.json` (from step 17)
- `prd/product-inventory.json` (from step 18)
- `prd/request-<prd_tag>.md` (canonical feature request)

## Procedure

### 19.1 — Normalize vocabulary

**Greenfield handling.** If `product_inventory.existing_product_state == "greenfield"`, `preferred_terms` is empty. In that case, the orchestrator MUST invent canonical terms for every entity in `entities_implied` and record them in `feature-decomposition.json` under `vocabulary.invented_terms: { term: "<canonical>", aliases: ["<request-word>"], provenance: "invented-this-prd" }`. Downstream PRDs read this and lock to it.

For every atomic item from step 17, check whether the wording matches `vocabulary.preferred_terms` in the inventory. If the request says "Class" and the product calls it "Classroom," the PRD must say "Classroom." Build a vocabulary translation table for this PRD.

If the request explicitly uses a non-canonical term and the meaning is clear, prefer the canonical term but note the user's word as an alias in the first mention: "Classroom (referred to as 'class' in the request)." Do this once, then use the canonical term throughout.

### 19.2 — Reconcile personas

For each `personas_in_scope` from step 17:
- Match it to an entry in `canonical_personas` from the inventory.
- If the match is exact (e.g., request says "teacher", inventory has "Teacher"), record the canonical name.
- If the match is fuzzy (e.g., request says "school staff", inventory has "School Worker" + "Admin"), pick the inventory match that best fits the intent and note the disambiguation in `persona_reconciliation_notes`.
- If the request introduces a persona the inventory does not have, flag it. Either (a) propose extending an existing persona (preferred — record the persona expansion as `proposed_persona_variation`), or (b) propose a genuinely new persona (only if unavoidable, with rationale).

### 19.3 — Reconcile entities

For each `entities_implied` from step 17:
- Cross-reference against `canonical_entities` from the inventory.
- If the new entity duplicates an existing one (e.g., request says "Notification" and inventory already has "Alert"), use the existing entity name and record `entity_reuse`. The PRD will EXTEND the existing entity, not create a parallel one. List the new fields/states being added in step 22.
- If the new entity is genuinely new, keep the proposed name (after vocabulary normalization).

### 19.4 — Resolve duplication risks

Read `duplication_risks` from the inventory. For each:
- If verdict is `duplicate`: drop the capability from the new PRD's scope. Add it under `Out of scope` with a one-line reference: "Already covered by [existing PRD title]."
- If verdict is `distinct`: keep but record a `differentiation_note` explaining how it differs.
- If verdict is `unclear`: keep but flag in the scope envelope under `requires_pm_confirmation`. The step-25 critics will surface this for human review.

### 19.5 — Draw the scope envelope

For each capability and entity, classify into ONE bucket:

- **in_scope** — this PRD is responsible for delivering this. Acceptance criteria will be written for it.
- **adjacent_scope** — this PRD describes it but the actual delivery is owned by another team / another PRD / a future phase. The PRD references it for context only.
- **out_of_scope** — explicitly excluded. Listed in the `Out of scope` section.
- **future_scope** — not in this PRD, but worth listing as phase-2 ideas. Listed in the `Future scope` section.

Write the envelope to `prd/temp/scope-envelope.md`:

```markdown
## Scope envelope

### In scope (this PRD delivers)
- C1: <capability text>
- C3: <capability text>
- E1: <entity name>

### Adjacent scope (referenced for context)
- E2: <entity name> — owned by [other PRD / other team]

### Out of scope (explicitly excluded)
- C5: <capability text> — reason: <user explicitly excluded | duplicates existing>

### Future scope (phase 2+)
- C7: <capability text>
```

### 19.6 — Persona ↔ capability matrix

Build a small matrix mapping which personas use which in-scope capabilities. This will seed step 21 (per-persona user stories).

```markdown
| Capability | Student | Teacher | Admin | Parent | School worker |
|---|---|---|---|---|---|
| C1 | — | author | view | receive | — |
| C2 | — | view | manage | — | — |
```

Verbs: `author`, `view`, `receive`, `acknowledge`, `manage`, `configure`, `approve`, `report-on`, or `—` (not involved).

### 19.7 — Write `prd/feature-decomposition.json`

Schema:

```json
{
  "prd_tag": "...",
  "based_on": {
    "request_path": "prd/request-<prd_tag>.md",
    "research_final_report_path": "...",
    "product_inventory_path": "prd/product-inventory.json"
  },
  "vocabulary_translation": {"request_term": "canonical_term"},
  "personas_in_scope": [
    {"id": "P1", "canonical_name": "...", "role_in_feature": "<one line>", "reconciliation_note": "..."}
  ],
  "entities_in_scope": [
    {"id": "E1", "canonical_name": "...", "reuse_or_new": "reuse | new", "extends_existing": "<entity name if reuse>", "rationale": "..."}
  ],
  "capabilities_in_scope": [
    {"id": "C1", "text": "<canonicalized capability>", "owning_persona_verb": {"teacher": "author", "parent": "receive"}, "differentiation_note": "..."}
  ],
  "scope_envelope": {
    "in_scope": ["C1", "C2", "E1"],
    "adjacent_scope": [{"id": "E2", "owned_by": "..."}],
    "out_of_scope": [{"id": "C5", "reason": "..."}],
    "future_scope": [{"id": "C7", "rationale": "..."}]
  },
  "persona_capability_matrix": "... (markdown table as string, OR structured as object)",
  "requires_pm_confirmation": [{"item_id": "...", "question": "..."}],
  "proposed_persona_variations": [{"name": "...", "parent_persona": "...", "rationale": "..."}]
}
```

### 19.8 — Update coverage matrix

Re-read `prd/temp/coverage-matrix.md` from step 17. For every row, confirm that the canonicalized item from step 19 still covers the request phrase. If vocabulary normalization or duplication-drop dropped a phrase off the map, fix it (either by adding the canonical item or by recording in `out_of_scope` with the original phrase as the reason).

### 19.9 — Identify relevant Claude Code skills

Some features benefit from specialized PMG-domain skills available in the Claude Code environment. Inspect the feature decomposition for domain signals and select PMG-RELEVANT skills only. Engineering-implementation skills (language patterns, frameworks, DB, deployment, etc.) are NOT included — those are the dev team's tools, not PMG's.

**Skill-relevance heuristics:**

| Feature signal | Suggest skill | Used in pipeline by |
|---|---|---|
| Capability mentions a screen / dashboard / visual UI / new field on UI | `impeccable` | draft-orchestrator (when writing entities / flows sections), polish-auditor (cosmetic readability) |
| Capability touches design system / visual identity / new component | `frontend-design` | draft-orchestrator (entities section guidance) |
| Capability is iOS / iPadOS specific UI | `liquid-glass-design` | draft-orchestrator (UI section) |
| Capability touches notification copy, messaging, in-app announcements | `content-engine` | draft-orchestrator (acceptance criteria + user-visible strings) |
| Capability is heavy on prose / narrative / longer-form content | `article-writing` | synthesizer (voice calibration) |
| PRD has an exec-summary or stakeholder-pitch section | `investor-materials` | synthesizer (Overview section voice) |
| Capability requires competitive / market context (rarely needed if research already covered it) | `market-research` | draft-orchestrator (background framing) |
| Capability uses Claude API / on-device AI / LLM features | `claude-api` | draft-orchestrator (capability framing — strictly user-visible behavior, not API details) |
| Capability involves video creation / playback | `videodb`, `fal-ai-media` | draft-orchestrator |
| Capability matches a domain skill present in the environment (e.g., `customs-trade-compliance`, `inventory-demand-planning`, `energy-procurement`, `carrier-relationship-management`, `returns-reverse-logistics`, `quality-nonconformance`) | the matching domain skill | draft-orchestrator (domain context) |

**Skill-exclusion list (NEVER include in `relevant-skills.json`):**

- Any `python-*`, `go-*`, `rust-*`, `cpp-*`, `kotlin-*`, `swift-*`, `java-*`, `perl-*`, `dart-*`, `flutter-*` skill (engineering).
- Any `springboot-*`, `django-*`, `laravel-*`, `compose-*`, `swiftui-*`, `frontend-patterns`, `backend-patterns`, `android-*` skill (framework / implementation).
- Any `postgres-*`, `clickhouse-*`, `database-migrations`, `jpa-patterns`, `kotlin-exposed-*` skill (DB layer).
- Any `docker-*`, `deployment-*`, `e2e-*`, `*-testing`, `*-tdd`, `*-verification`, `cost-aware-llm-pipeline`, `agent-harness-construction` skill (DevOps / testing / agent ops).
- Any `api-design`, `mcp-server-patterns`, `mcp-*`, `claude-devfleet`, `dmux-*`, `gsd-*` skill (orchestration / engineering tooling).
- Any `hyperresearch-*` or `hyperresearch-prd-*` skill (pipeline internals).
- Any `figma-*`, `frontend-slides`, code-related design-tool skills unless the PRD's feature explicitly delivers via that tool.

**How to look up available skills:** the Claude Code session lists installed skills in the system-reminder block at the top of the conversation. Walk that list, apply the heuristics above, and emit only entries that exist in the environment AND clear the exclusion list AND match a feature signal.

**Write `prd/relevant-skills.json`:**

```json
{
  "prd_tag": "...",
  "relevant_skills": [
    {
      "skill": "impeccable",
      "rationale": "Feature introduces 3 new screens and a redesigned dashboard card — impeccable's UI critique helps draft-orchestrator describe user-visible UX in scannable terms.",
      "consumed_by": ["prd-draft-orchestrator", "prd-polish-auditor"],
      "sections_it_strengthens": ["User-visible entities & fields", "User flow", "Integration with existing product"]
    },
    {
      "skill": "content-engine",
      "rationale": "Feature delivers notification copy + in-app announcements; content-engine guides platform-native voice for those user-visible strings.",
      "consumed_by": ["prd-draft-orchestrator"],
      "sections_it_strengthens": ["Acceptance criteria", "User stories"]
    }
  ],
  "explicitly_excluded": [
    {"skill": "springboot-patterns", "reason": "engineering / framework — out of PRD lane"},
    {"skill": "api-design", "reason": "engineering — dev team decides"}
  ]
}
```

**Strict caps:**
- Maximum 5 `relevant_skills` entries. More dilutes the draft-orchestrators' attention.
- If zero skills match (which is fine and common), write an empty array. The pipeline proceeds normally.
- Each entry must clear BOTH a feature signal AND the exclusion list. When in doubt, exclude.

**No skill is mandatory.** This step strengthens the draft when relevant skills exist. It is not a gate.

## Exit criterion

- `prd/feature-decomposition.json` exists, valid JSON, all required keys present.
- `prd/temp/scope-envelope.md` exists.
- `prd/relevant-skills.json` exists (may have empty `relevant_skills` array — that's valid).
- The persona-capability matrix has ≥1 verb-cell per in-scope capability.
- Coverage matrix from step 17 still passes (every original request phrase maps somewhere).

## Next step

Return to the entry skill. Read `pipeline_tier` from `prd/prd-decomposition.json`:

- **light tier:** skip 20, 21, 22, 24, 25, 26. Invoke step 23 next (single-draft path):
  ```
  Skill(skill: "hyperresearch-prd-23-triple-draft")
  ```
- **full tier:** invoke step 20:
  ```
  Skill(skill: "hyperresearch-prd-20-integration-map")
  ```
