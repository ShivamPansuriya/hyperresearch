---
name: hyperresearch-prd-22-flows-entities
description: >
  Step 22 of the hyperresearch-PRD pipeline. Builds step-by-step user
  flows and user-facing entity field lists. Full tier only. Produces
  flows.md and entities.md. Strictly user-visible — no schemas, no
  APIs, no architecture.
---

# Step 22 — Flows & user-visible entities

**Tier gate:** Full tier ONLY.

**Goal:** the user stories from step 21 describe motivation; this step describes *what the user sees, step by step, on screen* and *what fields they encounter when looking at an entity*. This is the most concrete part of the PRD and the one the dev team will reference most often when implementing UI.

**Why this step exists:** flows and entity fields are where architecture-leak most often sneaks in. By isolating this work in a dedicated step with a strict no-architecture rule, the rest of the pipeline stays clean.

## Recover state

- `prd/feature-decomposition.json` (step 19)
- `prd/integration-map.json` (step 20)
- `prd/user-stories.md` (step 21)
- `prd/product-inventory.json` (step 18) — for vocabulary and existing field reuse

## Procedure

**Cross-check invariant.** Before exiting, verify that every distinct state or value mentioned in any user story from step 21 appears as either an enumerated field value, a state transition, or a per-persona view difference in the entity tables. If a story says "three states: not yet delivered, delivered but not acknowledged, acknowledged" then the corresponding entity table must enumerate exactly those three states. Mismatches are a high-severity finding for the instruction critic.

### 22.1 — User flows

For each in-scope flow (from `flows_implied` in step 17, expanded through step 19/20):

Write a numbered, step-by-step user-visible flow:

```markdown
### Flow F1 — <flow name>

**Trigger.** <The user-visible event that starts the flow.>
**Primary actor.** <Persona who drives the flow.>
**Other actors involved (if any).** <With their role.>

**Steps**
1. **<Persona> on <surface>:** <user-visible action>. Result: <user-visible outcome>.
2. **<Persona> on <surface>:** <user-visible action>. Result: <user-visible outcome>.
3. **System on <surface>:** <user-visible system response, described as what the user sees>.
4. ...

**Branch — <branch name>.** When <user-visible condition>, the flow diverges:
- Step 3a. <user-visible action / outcome>
- Step 3b. <user-visible action / outcome>

**End states.**
- Happy path: <what the user ends up looking at>.
- Cancelled / abandoned: <where the user lands>.
- Error: <what the user sees + how they recover>.

**Linked stories:** S1.1, S1-neg.
**Linked entities:** E1, E2.
```

Constraints:
- Each step must name (a) WHO is acting, (b) WHERE on screen, (c) WHAT they see / do.
- No system step may describe non-user-visible internals. "System validates the request" is too vague — write "System shows a success toast and the new item appears in the list."
- Branches must be USER-VISIBLE conditions ("If the student is already marked present" — not "If the cache hit returns null").
- Each flow must end in a clearly described end-state set.

Write all flows to `prd/flows.md`. Start with a short "Reading guide" paragraph noting that flows are user-visible only and that the dev team owns the technical realization.

### 22.2 — User-visible entity fields

For each in-scope entity, list the fields the USER will see. NOT a schema. Schema is the dev team's job. This list answers: "If a user opens this entity's detail view, what labels and values do they see?"

Format:

```markdown
### Entity E1 — <canonical entity name>

**Purpose for users.** <One sentence. What the user gains by interacting with this entity.>

**Where the user encounters this entity.** <From integration-map: list of surfaces.>

**User-visible fields**

| Field label (as shown) | Type from user POV | Editable by whom | Notes |
|---|---|---|---|
| Title | Short text | Author persona | Required |
| Status | One of {Draft, Published, Archived} | Author persona | Visible state badge |
| Linked Student | Reference to a Student | System-generated | Click opens Student profile |
| Linked Class | Reference to a Class | System-generated | — |
| Created at | Date and time | System | Shown in user's local timezone |
| Acknowledged at | Date and time, or blank | Receiver persona | Shown only after receiver acknowledges |

**Per-persona view differences**
- **Teacher:** sees full field list + author controls.
- **Parent:** sees Title, Status, Linked Student, Created at, Acknowledged at; sees the "Acknowledge" button when Status is Published and Acknowledged at is blank.
- **Admin:** sees aggregate counts, not individual entity detail unless drilling in.

**State transitions (user-visible)**
- Draft → Published: triggered by author's "Publish" action.
- Published → Acknowledged: triggered by receiver tapping "Acknowledge".
- Any → Archived: by admin from the admin tools screen, or after 90 days automatic — user sees a "Move to archive" confirmation.

**Linked entities (user-visible relationships)**
- Each <Entity> is associated with one <Other entity> — the user clicks to navigate.

**Linked stories:** S1.1.
```

Constraints:
- "Type from user POV" describes what the user perceives (Short text, Long text, Date, Yes/No, Choice, List of items, Reference to <entity>) — NEVER `VARCHAR(255)`, `INT`, `JSONB`, etc.
- "Editable by whom" names personas, not roles in an ACL sense — never write "users with write permission."
- Mention required/optional, default value (from user POV), and validation rules (as a user would experience them: "must be a school day", "name cannot be blank").
- State transitions are described as user actions or as user-visible outcomes of system events — never as "service publishes message to queue."

Write all entities to `prd/entities.md`. Start with a short "Reading guide" paragraph: "These are the entities and fields users see. The development team will define data models, types, and persistence; this document captures only what users perceive and interact with."

### 22.3 — Cross-link check

For every story in `prd/user-stories.md` whose body mentions an entity or flow, confirm it links to the corresponding F# or E# id. Add missing links.

### 22.4 — Architecture-leak sanity gate

Re-read `prd/flows.md` and `prd/entities.md`. Search for and rewrite:
- Any DB term (table, row, column, index, foreign key, JSONB, NULL, INT)
- Any API term (endpoint, GET, POST, route, handler)
- Any infra term (queue, cache, service, microservice, worker, deploy)
- Any code term (function, class, module-in-the-codebase-sense, library name)
- Any timing term that reads like an SLA without user context ("99.9% uptime", "p99 latency 200ms")

Replace each leak with a user-visible equivalent or remove. Architecture decisions are out of scope.

## Exit criterion

- `prd/flows.md` exists; every in-scope flow has a numbered step list, branch list, and end-state list.
- `prd/entities.md` exists; every in-scope entity has a labeled field table and per-persona view differences.
- Sanity gate passes — no architecture vocabulary remains.

## Next step

Return to the entry skill. Invoke step 23:

```
Skill(skill: "hyperresearch-prd-23-triple-draft")
```
