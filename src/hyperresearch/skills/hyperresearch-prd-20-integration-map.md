---
name: hyperresearch-prd-20-integration-map
description: >
  Step 20 of the hyperresearch-PRD pipeline. Maps each in-scope
  capability and entity to the existing modules, surfaces, and flows
  it touches — described functionally (from a user-visible behavior
  standpoint), never architecturally. Full tier only. Produces
  integration-map.json which step 22 (flows) and step 25 (critics)
  read.
---

# Step 20 — Integration map

**Tier gate:** Full tier ONLY. Light tier skips this step.

**Goal:** for every in-scope capability and entity, document where it shows up in the existing product, what existing flows it changes, and which existing screens / dashboards / notification surfaces are affected — all in user-visible terms. No APIs. No schemas. No services.

**Why this step exists:** features that don't ground their integration story in the existing product produce PRDs the dev team has to mentally rewrite. By forcing a user-visible mapping ("when an admin opens the Reports module, a new tile titled X appears"), the PRD stays grounded and the dev team gets unambiguous integration acceptance criteria.

## Recover state

- `prd/feature-decomposition.json` (step 19)
- `prd/product-inventory.json` (step 18)
- `prd_directory` from scaffold

## Procedure

### 20.1 — Identify touchpoints per capability

For each capability in `scope_envelope.in_scope`:

1. **Where does this capability ENTER the user's view?** Which existing screen, menu, or notification surface introduces it? Examples (user-visible only):
   - "A new card on the Student Dashboard"
   - "An additional row in the Teacher's Assignments table"
   - "A new tab on the Parent app's home screen"
   - "A push notification surfaced through the existing Alerts pipeline (from the Parent module)"
2. **Where does it EXIT the user's view?** Where does the user complete the interaction? (a confirmation screen, a back-to-list, a notification mark-as-read)
3. **What existing flow does it modify, if any?** If the feature changes an existing flow's steps or branches, name the existing flow and describe the user-visible change.
4. **Does the capability require permission changes?** Describe in user-visible terms ("admins will see an additional checkbox in the role configuration screen"). Do NOT describe role tables or ACL implementation.

Record these as `touchpoints` per capability.

### 20.2 — Identify touchpoints per entity

For each entity in `entities_in_scope`:

1. **Where is this entity displayed?** Which screens, lists, or detail views show it?
2. **Where is it created / edited / archived from the user's perspective?** A button, a form, an inline edit?
3. **Which existing entities does it relate to in user-visible terms?** ("Each Alert is linked to a Student and is visible to that Student's parents and class teacher.") This is a USER-VISIBLE relationship, not a foreign key.
4. **Does the user see different views of the same entity by persona?** ("A teacher sees author + edit controls; a parent sees content + acknowledge button.")

### 20.3 — Map notifications and async events

For each capability with an async / notification element:

1. **What user-visible event triggers the notification?** ("Attendance marked absent" → triggers "Parent attendance alert.")
2. **Which existing notification surfaces deliver it?** (in-app inbox, push, SMS, email digest, banner) — only those the inventory says the product already has. New channels are out-of-scope for this PRD unless the request explicitly asks.
3. **How does the user opt in / opt out?** Describe the user-visible control. Reuse the product's existing notification-preferences pattern from the inventory if one exists.

### 20.4 — Map cross-persona handoffs

For every capability with `≥2` personas in `persona_capability_matrix`:

- Describe the handoff in user-visible terms. ("Teacher authors a homework assignment; once published, every enrolled Student's My Assignments list adds the item; each Parent of an enrolled Student receives an inbox notification.")
- Note any time-sensitive expectations from the user perspective. ("Parent sees the assignment within 1 minute of teacher publishing it.") Phrase as user expectation, not SLA.

### 20.5 — Write `prd/integration-map.json`

Schema:

```json
{
  "prd_tag": "...",
  "capability_touchpoints": [
    {
      "capability_id": "C1",
      "entry_surfaces": ["Student Dashboard > Today card", "Teacher app > Quick actions"],
      "exit_surfaces": ["Confirmation toast", "Updated assignments list"],
      "modifies_existing_flows": [
        {"flow_name": "Teacher publishes assignment", "module": "Classroom", "user_visible_change": "Adds an 'Attach research summary' step before publish."}
      ],
      "permission_changes": [{"surface": "Role configuration screen", "change": "Adds an 'allow attaching research summaries' toggle for the Teacher role"}]
    }
  ],
  "entity_touchpoints": [
    {
      "entity_id": "E1",
      "displayed_on": ["Parent inbox list", "Parent app > Alerts > detail"],
      "created_from": "System-generated when attendance marked absent",
      "edited_from": "Not user-editable; only acknowledged",
      "user_visible_relations": [
        {"to_entity": "Student", "described_as": "An Alert is linked to a single Student"},
        {"to_entity": "Parent", "described_as": "Visible to every Parent of the linked Student"}
      ],
      "per_persona_views": {
        "teacher": "Read-only view of historical alerts for their class",
        "parent": "List + detail + acknowledge button",
        "admin": "Aggregate report; can disable per-school"
      }
    }
  ],
  "notification_map": [
    {
      "trigger_event_user_visible": "Attendance marked absent",
      "alert_name": "Parent attendance alert",
      "channels": ["Parent app inbox", "Push notification"],
      "user_opt_in_control": "Parent app > Settings > Notification preferences > Attendance",
      "follows_product_pattern": "Yes — reuses the existing Notification Preferences screen"
    }
  ],
  "cross_persona_handoffs": [
    {
      "handoff_name": "Absence → parent alert",
      "actor_chain": ["Teacher marks attendance", "System detects absence", "Parent receives alert"],
      "user_visible_latency_expectation": "Parent receives alert within 2 minutes of attendance submission"
    }
  ],
  "integration_risks": [
    {
      "risk": "Existing dashboard already has 6 cards; adding a 7th may push key cards below the fold on mobile",
      "from_inventory_pattern": "Student Dashboard density",
      "mitigation_user_visible": "Place new card inside existing 'Today' section rather than as a top-level card"
    }
  ]
}
```

### 20.6 — Sanity gate: no architecture leaks

Re-read everything you just wrote. Strike out / rewrite any phrase that:
- Names a database table, column, service, or API endpoint.
- Refers to "the backend", "the API", "the service layer", "the database", "events bus", "queue", "cache", etc.
- Describes consistency, latency, throughput as engineering specs rather than user-felt expectations.
- Names a programming language, framework, library, or infra component.

If you have a leak, the fix is almost always: translate to user-visible. "Eventually consistent" → "may take up to 2 minutes to appear." "Pub/sub" → "all subscribed users see the update simultaneously."

## Exit criterion

- `prd/integration-map.json` exists, valid JSON.
- Every in-scope capability has at least one `entry_surface`.
- Every in-scope entity has at least one `displayed_on` surface.
- Architecture-leak sanity gate passes (no banned terms).

## Next step

Return to the entry skill. Invoke step 21:

```
Skill(skill: "hyperresearch-prd-21-personas-stories")
```
