---
name: hyperresearch-prd-17-initialize
description: >
  Step 17 of the hyperresearch-PRD pipeline. Decomposes the canonical
  feature request into atomic items, classifies pipeline_tier and
  prd_format, and produces the coverage matrix that downstream steps
  depend on. The required_section_headings field this step produces
  is the single highest-leverage input for instruction-following
  scores. Invoked via Skill tool from the entry skill (hyperresearch-prd).
---

# Step 17 — PRD initialization & feature-request decomposition

**Tier gate:** Runs for ALL tiers. This step also classifies the tier itself.

**Goal:** before any PRD writing happens, decompose the user's feature request into its atomic items. This artifact is read by the instruction-critic in step 25 and by the draft sub-orchestrators in step 23 to make sure the pipeline doesn't drift from what was actually asked.

**Why this step exists:** the single dimension where PRDs go wrong is whether the document structurally mirrors what the requester asked for. When the user asks "I want a feature for X with capability A, B, and C" and the PRD produces per-capability sections in A→B→C order with the requested fields — that's high instruction-following. When the same request produces a PRD reorganized around the writer's preferred frameworks — that's a structural mismatch, even if every requirement is in there somewhere. The decomposition makes the structural requirement explicit, in writing, BEFORE drafting.

## Recover state

- `prd/request-<prd_tag>.md` exists (canonical feature request, written by the entry skill bootstrap).
- `prd/scaffold.md` exists with feature request, modality, research final report path, prd directory path.
- The research final report exists at the path recorded in scaffold.

## Procedure

### 17.1 — Read the canonical inputs

Read in this order:
1. `prd/request-<prd_tag>.md` — verbatim feature request.
2. `prd/scaffold.md` — your private planning context.
3. The research final report at the path recorded in scaffold. Skim it; you don't need to consume every word now, but you need its structure (section headings) and topline conclusions to inform decomposition.

### 17.2 — Decompose into atomic items

**Pattern-reuse constraints (e.g., "uses existing screen X") count as BOTH a constraint AND a capability.** Record them in `constraints` for non-functional gating, AND in `capabilities` so step 21 generates a user story confirming the reused pattern is honored. Otherwise pattern-reuse silently disappears from user-visible coverage.

An atomic item is a single requirement the user explicitly or implicitly asked for. Be exhaustive. Use these categories:

- **capabilities** — what the feature must DO (e.g., "send attendance alert to parent when student is absent"). For each capability, ALSO record `disambiguations: []` — questions the orchestrator should answer before user stories are drafted (e.g., for a disable feature: "are alerts skipped permanently or deferred to after the disable window?"). Empty list is allowed; missing field is a contract violation.
- **personas_in_scope** — who uses this feature (student, teacher, admin, parent, school worker, or a subset).
- **entities_implied** — user-visible entities the request implies (e.g., "Alert", "Notification preference", "Attendance Record"). Names only; field-level detail comes in step 22.
- **flows_implied** — high-level user flows the request implies (e.g., "parent opts-in", "alert is delivered", "parent acknowledges").
- **success_signals** — what user-visible behavior would prove the feature works.
- **explicit_out_of_scope** — anything the user explicitly excluded.
- **implicit_in_scope** — necessary supporting capability the user didn't name but the feature cannot work without (e.g., "an opt-in setting" is required for an opt-in alert system).
- **constraints** — non-functional user-visible constraints (e.g., "must work on low-bandwidth networks", "must respect parental consent law").

### 17.3 — Classify `pipeline_tier`

Read these rules and pick exactly ONE tier:

| Signal | → tier |
|--------|--------|
| Touches 1 module, 1 persona, 0–1 new entities, ≤3 capabilities | `light` |
| Touches 1 module, ≥2 personas, OR 2–3 entities, OR 4–6 capabilities | `light` or `full` (call it; tier up if uncertain) |
| Touches ≥2 modules, OR cross-persona workflows, OR ≥3 new entities | `full` |
| Net-new product area / top-level menu item | `full` always |
| Compliance / safety / regulatory feature (PII, minors, payments) | `full` always |

In ManageArk's context: a feature touching only one of {student / teacher / admin / parent / school-worker} workflows in one module is usually `light`. Anything that crosses persona boundaries (e.g., a teacher publishes something a parent receives) is usually `full`.

### 17.4 — Classify `prd_format`

Pick exactly ONE:

| Format | When to use | Output character |
|--------|-------------|------------------|
| `"one_pager"` | Tiny incremental change (a new toggle, a copy change, one new field). Pair with `light` tier. | 300–800 words. Problem → Solution → User-visible change → Acceptance criteria → Future scope. Compact. |
| `"standard_prd"` | Most features. Single feature area, clear scope, 1–3 personas. | 1500–4000 words. Overview, personas, user stories, flow, UI entities, integration, acceptance, out-of-scope, future scope, success metrics. |
| `"detailed_prd"` | Cross-cutting or net-new area. Multi-persona. Compliance-heavy. | 4000–8000 words. All of standard_prd plus dedicated persona sections, multiple flow diagrams (described in prose — no drawings), edge-case appendix, phased rollout. |

### 17.5 — Define `required_section_headings`

**Persist the tier classification rationale.** Add a `tier_rationale` field to `prd-decomposition.json` with one sentence on why this feature is `light` vs `full` (number of personas, presence of cross-cutting constraints, presence of edge cases). This is auditable.


Write the literal H2 headings the final PRD MUST use, in order. This is the highest-leverage instruction-following anchor. Defaults:

- `one_pager`: `["Overview", "User-visible change", "Acceptance criteria", "Out of scope", "Future scope"]`
- `standard_prd`: `["Overview", "Goals & non-goals", "Personas", "User stories", "User flow", "User-visible entities & fields", "Integration with existing product", "Acceptance criteria", "Out of scope", "Future scope", "Success metrics"]`
- `detailed_prd`: `["Overview", "Goals & non-goals", "Personas", "Per-persona user stories", "User flows", "User-visible entities & fields", "Integration with existing product", "Edge cases & error states", "Acceptance criteria", "Phased rollout", "Out of scope", "Future scope", "Success metrics"]`

If the feature request explicitly asks for a particular structure ("I want a section on X", "include a comparison table of Y"), insert that heading in the order it appears in the request. **The request's structural ask always wins over the defaults.**

### 17.6 — Write `prd/prd-decomposition.json`

Schema:

```json
{
  "prd_tag": "<from scaffold>",
  "created": "<ISO-8601>",
  "modality": "<from scaffold>",
  "pipeline_tier": "light | full",
  "prd_format": "one_pager | standard_prd | detailed_prd",
  "required_section_headings": ["...", "..."],
  "atomic_items": {
    "capabilities": [{"id": "C1", "text": "<verbatim or close paraphrase>", "source": "explicit | implicit"}],
    "personas_in_scope": [{"id": "P1", "persona": "student | teacher | admin | parent | school-worker | <other>", "role_summary": "<one line>"}],
    "entities_implied": [{"id": "E1", "name": "<entity name>", "rationale": "<why this is implied>"}],
    "flows_implied": [{"id": "F1", "name": "<flow name>", "trigger": "<what kicks it off>", "outcome": "<user-visible result>"}],
    "success_signals": [{"id": "S1", "text": "<observable user-visible behavior>"}],
    "explicit_out_of_scope": ["..."],
    "implicit_in_scope": [{"id": "I1", "text": "<...>", "rationale": "<...>"}],
    "constraints": [{"id": "K1", "text": "<...>", "kind": "compliance | accessibility | performance-as-felt | locale | <other>"}]
  },
  "research_final_report_path": "<from scaffold>",
  "prd_directory": "<from scaffold>",
  "tier_rationale": "<2-3 sentences>",
  "format_rationale": "<2-3 sentences>"
}
```

### 17.7 — Coverage matrix self-audit

Re-read the verbatim feature request. Walk through it phrase by phrase and extract every **significant noun phrase, persona reference, capability verb, entity name, and constraint phrase**. For each:

- Does it map to at least one atomic item in the decomposition?
- Is the decomposition's interpretation **as broad as the phrase's natural scope**? (e.g., "all users" must not be narrowed to "students only")
- If the phrase has multiple plausible referents, does the decomposition cover BOTH readings?

Write the matrix to `prd/temp/coverage-matrix.md`:

```markdown
## Coverage Matrix — feature-request phrase → atomic item mapping

| Request phrase (verbatim) | Mapped atomic item(s) | Scope check | Gap? |
|---|---|---|---|
| "send alert to parent" | C1 (capability), P1 (parent persona), F1 (alert delivery flow) | OK | No |
| "for all critical events" | C2 — but "critical" not defined | NARROWED — request says "critical" broadly, decomposition needs a definition lane | **YES** |
```

**If any row has `Gap? = YES`:** go back and fix the decomposition. Add the missing items or broaden the narrowed scope. Then re-run the matrix until every row passes. Do NOT proceed with known gaps — they cascade into missing user stories, missing flows, and missing PRD sections.

### 17.8 — Update the scaffold

Append a "Tier rationale" subsection to `prd/scaffold.md` that QUOTES the `tier_rationale` field from `prd/prd-decomposition.json`. The JSON is canonical; the scaffold mirrors it for human readability. Never edit the scaffold copy independently — if you need to revise the rationale, edit the JSON and re-mirror.

## Exit criterion

- `prd/prd-decomposition.json` exists, parses as valid JSON, all required keys present.
- `prd/temp/coverage-matrix.md` exists, every row reads `Gap? = No`.
- `prd/scaffold.md` has the tier rationale appended.

## Next step

Return to the entry skill (`hyperresearch-prd`). Read `prd/prd-decomposition.json` to confirm the tier, then invoke step 18:

```
Skill(skill: "hyperresearch-prd-18-product-inventory")
```

Step 18 runs for ALL tiers.
