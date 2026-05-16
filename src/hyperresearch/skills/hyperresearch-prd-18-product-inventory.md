---
name: hyperresearch-prd-18-product-inventory
description: >
  Step 18 of the hyperresearch-PRD pipeline. Scans the PRD directory
  to build a structured inventory of the existing product — modules,
  personas, entities, flows, and integration points. Produces
  product-inventory.json which every downstream step reads to keep
  the new PRD coherent with the rest of the product. Runs for all
  tiers. Invoked via Skill tool from the entry skill.
---

# Step 18 — Product inventory scan

**Tier gate:** Runs for ALL tiers.

**Goal:** before writing anything new, understand the existing product. New features must plug into an existing surface coherently — same vocabulary, same persona model, same flow patterns. This step builds a structured inventory of the product as it exists today, by reading the PRD directory.

**Why this step exists:** without product context, the PRD will reinvent personas the product already has, propose entities that duplicate existing ones, or describe flows that contradict established UX patterns. Step 20 (integration map) and step 25 (instruction-following critic) both depend on this inventory being accurate.

## Recover state

- `prd/prd-decomposition.json` exists.
- `prd/scaffold.md` records `prd_directory` (default `prd/`).

## Procedure

### 18.1 — Locate and enumerate the PRD directory

1. Read `prd_directory` from `prd/scaffold.md`.
2. List all PRD files. Look for these patterns in order:
   - `<prd_directory>/notes/final_prd_*.md` (prior runs of THIS pipeline)
   - `<prd_directory>/*.md` (legacy or hand-written PRDs)
   - `<prd_directory>/**/*.md` (nested PRDs)
3. Exclude:
   - `<prd_directory>/temp/*` and `<prd_directory>/runs/*` (scratch + archive)
   - `<prd_directory>/scaffold.md` (current run's planning doc)
   - `<prd_directory>/request-*.md` (canonical request files)
   - `<prd_directory>/*-decomposition.json` etc. (orchestration artifacts)

If the directory does not exist OR contains zero qualifying PRD files: skip to step 18.5 with `existing_product_state = "greenfield"`.

### 18.2 — Read each PRD file

For each qualifying PRD file, read the full content. Extract:

- **module / feature area** the PRD belongs to (from filename, title, or Overview section)
- **personas referenced** — names and one-line role summary as written
- **user-visible entities** — names + the field lists the PRD documents (if listed)
- **user flows described** — flow name + trigger + outcome
- **integration points to other modules** — cross-references to other PRDs or modules
- **terminology / vocabulary** — distinctive product nouns and verbs (e.g., "Classroom" vs "Class", "Assignment" vs "Task", "Marks" vs "Grades")
- **out-of-scope items** explicitly listed (so we don't re-introduce them)
- **future-scope items** noted (so we know what's already on the roadmap)

If a PRD is very long, prioritize: Overview, Personas, Entities, Flows, Integration sections. Skim the rest.

### 18.3 — Detect persona model

Aggregate the personas referenced across all PRDs. Build the canonical persona set the product uses today. For ManageArk this will typically be a subset of: `student | teacher | admin | parent | school-worker`. Record any role variations:
- "Class Teacher" vs "Subject Teacher"
- "Primary Admin" vs "Sub-Admin"
- "Parent of Student" vs "Guardian"

The new PRD must use these exact terms in its `Personas` section. Inventing new persona names is a high-severity instruction violation that the persona-vocabulary check in step 25 will flag.

### 18.4 — Detect product-wide patterns

Identify recurring UX patterns the product already uses:
- **Notification pattern** — how does the product currently surface alerts? (banner, toast, inbox, push, email digest)
- **Permission pattern** — how is access controlled? (role-based screens, per-feature toggles, school-admin overrides)
- **Approval pattern** — how do multi-step approvals work? (queue + approve/reject, single-step auto, school-admin override)
- **Content visibility** — are there age-gates, parental-consent gates, or visibility scopes (class / grade / school) the product enforces?
- **Localization / language** — does the product support multiple languages? Which ones?

These patterns are the "house style" the new feature must follow.

### 18.5 — Write `prd/product-inventory.json`

Schema:

```json
{
  "existing_product_state": "documented | sparse | greenfield",
  "prds_scanned": [
    {
      "path": "<relative path>",
      "title": "<from H1 or filename>",
      "module": "<inferred module>",
      "personas_referenced": ["..."],
      "entities_referenced": [{"name": "<entity>", "fields_documented": ["..."]}],
      "flows_referenced": [{"name": "<flow>", "trigger": "<...>", "outcome": "<...>"}],
      "out_of_scope_items": ["..."],
      "future_scope_items": ["..."]
    }
  ],
  "canonical_personas": [
    {"name": "<exact term>", "role_summary": "<one line>", "variations": ["..."]}
  ],
  "canonical_modules": [
    {"name": "<module name>", "purpose": "<one line>", "key_entities": ["..."]}
  ],
  "canonical_entities": [
    {"name": "<exact entity name>", "fields_documented": ["..."], "owned_by_module": "<module>"}
  ],
  "vocabulary": {
    "preferred_terms": {"Class": "Classroom", "Task": "Assignment", "Grades": "Marks"},
    "avoid_terms": ["..."]
  },
  "ux_patterns": {
    "notification": "<description>",
    "permission": "<description>",
    "approval": "<description>",
    "content_visibility": "<description>",
    "localization": "<description>"
  },
  "integration_surface_areas": [
    {"surface": "<e.g., 'Student Dashboard'>", "owner_module": "<...>", "currently_shows": ["..."]}
  ],
  "duplication_risks": [
    {"new_concept_from_request": "<from prd-decomposition>", "potentially_duplicates": "<existing entity/feature>", "verdict": "duplicate | distinct | unclear"}
  ]
}
```

The `duplication_risks` section is critical. Cross-reference the `atomic_items` from step 17 against `canonical_entities`, `canonical_modules`, and prior `future_scope_items`. If the user is asking for something that already exists or was already planned, flag it. Step 19 will resolve these.

### 18.6 — Sparse-inventory and greenfield handling

- **Greenfield** (zero PRDs): write the inventory JSON with empty arrays for everything except `existing_product_state: "greenfield"` and a `notes` field that warns "no existing PRD context — the new PRD will create the canonical persona/entity/flow vocabulary for this product area."
- **Sparse** (1–3 PRDs found): proceed but flag in the JSON `existing_product_state: "sparse"` so downstream steps know to be conservative about claims like "follows existing pattern X."

### 18.7 — Sanity print

Print a short summary (≤25 lines) to your scratch notes at `prd/temp/inventory-summary.md`:
- N PRDs scanned
- M canonical personas detected
- K canonical modules detected
- Top 3 duplication risks

## Exit criterion

- `prd/product-inventory.json` exists and parses as valid JSON.
- `prd/temp/inventory-summary.md` exists.
- If `existing_product_state == "documented"`, the JSON has ≥1 entry in `canonical_personas`, `canonical_modules`, and `canonical_entities`.

## Next step

Return to the entry skill. Invoke step 19:

```
Skill(skill: "hyperresearch-prd-19-feature-decomposition")
```

Step 19 runs for ALL tiers.
