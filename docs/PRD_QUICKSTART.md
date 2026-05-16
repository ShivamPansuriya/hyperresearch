# PRD Quickstart

End-to-end walkthrough: generate a PRD from a feature request, using a prior hyperresearch report as the evidence base.

## Prerequisites

- `hyperresearch` installed: `pip install hyperresearch` (or installed from this fork).
- A Claude Code session with `/hyperresearch` already working.
- One completed hyperresearch run (so you have a `research/notes/final_report_*.md`).

## Step 1 — Install the PRD extension

```bash
# Per project (preferred for ManageArk):
cd /path/to/manageark-main
hyperresearch prd-install .

# Or globally:
hyperresearch prd-install --global
```

Verify:

```bash
hyperresearch prd-install --status
```

You should see green checks on 12 skills (`hyperresearch-prd` + 11 step skills) and 9 agents.

## Step 2 — Create / populate the `prd/` directory

The pipeline reads `prd/` for existing product context. Drop any current PRDs in there (or leave empty for greenfield):

```
prd/
├── student-profile.md
├── teacher-attendance.md
├── parent-app-onboarding.md
└── ...
```

The pipeline will scan these in step 18 to learn your canonical personas, modules, entities, vocabulary, and UX patterns.

## Step 3 — Run hyperresearch first

The PRD pipeline expects a research final report. Example:

```
/hyperresearch How are top SIS / school-management systems handling parent
attendance alerts? Compare delivery channels, opt-in flows, latency
expectations, and parent-side acknowledgement patterns. Focus on K-12 SaaS
deployments.
```

When the pipeline finishes, note the path:

```
research/notes/final_report_parent-attendance-alerts-research-9c8f1e.md
```

## Step 4 — Run the PRD pipeline

```
/hyperresearch-prd Build a parent attendance alert feature for ManageArk.

Personas in scope: parent, teacher, admin.

Capabilities:
- Parent opts in per child per category (attendance, marks, behaviour) from their app.
- When a teacher marks a child absent, the parents of that child receive an in-app inbox alert and an optional push notification.
- Parents acknowledge each alert; teachers and admins see acknowledgement state.
- Admins can globally disable parent alerts per-school during exam weeks.

Constraints:
- Must respect parental-consent law (already covered by the existing onboarding flow — reuse it).
- Localized to English + Hindi for v1.
- Must integrate with the existing notification preferences screen pattern.

Out of scope (explicit): SMS channel, multi-guardian routing rules.
```

What happens:

1. Step 17 mints `prd_tag` (e.g. `parent-attendance-alerts-a3f9b7`), classifies tier (this example is `full` because it spans 3 personas and integrates with notification preferences).
2. Step 18 scans `prd/`, learns ManageArk's canonical personas + the existing notification-preferences screen.
3. Step 19 reconciles the feature with the inventory — flags that "Parent" is already canonical and that the notification-preferences pattern should be reused.
4. Step 20 maps each capability to existing screens (Teacher's attendance screen, Parent app inbox, Admin tools).
5. Step 21 writes 4–6 user stories per persona plus negative / edge-case stories.
6. Step 22 writes the user flow (mark-absent → trigger → parent inbox → acknowledge) and the `Alert` entity with user-visible fields.
7. Step 23 spawns 3 parallel `prd-draft-orchestrator` subagents (user-value / business-outcome / integration-story angles).
8. Step 24 synthesizes the three drafts into a single PRD in two passes.
9. Step 25 runs 4 critics in parallel.
10. Step 26 patches critic findings as Edit hunks.
11. Step 27 polishes (hygiene + filler cuts).
12. Step 28 applies readability recommendations selectively.

Final artifact:

```
prd/notes/final_prd_parent-attendance-alerts-a3f9b7.md
```

## Step 5 — Review and hand off

Open the PRD. You should see:

- An `Overview` section grounding the feature in concrete user pain.
- `Personas` using ManageArk's canonical names.
- `User stories` per persona, including negative cases.
- `User flow` step-by-step from teacher → parent → acknowledgement.
- `User-visible entities & fields` — a labeled field table for the `Alert` entity, with per-persona view differences.
- `Integration with existing product` describing the reused notification-preferences screen.
- `Acceptance criteria` — bulleted, observable, user-visible (no API contracts).
- `Out of scope` listing SMS + multi-guardian routing.
- `Future scope` for items the research surfaced but you didn't commit to.
- `Success metrics` user-visible: opt-in rate within 30 days, alert acknowledgement rate, parent CSAT delta.

**No** schema, no API spec, no database table, no library names, no SLAs — the dev team owns all of those.

Hand off to engineering. They use the PRD as the source of user-visible truth; their own technical design lives in their own design docs.

## If the run produced something off

The pipeline writes an audit trail. Investigate in this order:

1. `prd/scaffold.md` — does it correctly capture the request?
2. `prd/prd-decomposition.json` — is the tier and format right? Are atomic items complete?
3. `prd/feature-decomposition.json` — is the scope envelope sensible? Any items wrongly dropped to out-of-scope?
4. `prd/product-inventory.json` — did the inventory correctly read your existing PRDs?
5. `prd/prd-critic-findings-*.json` — what did the critics flag?
6. `prd/patch-log.json` — what edits got applied?
7. `prd/polish-log.json` — what hygiene cuts ran?
8. `prd/readability-decisions.json` — which readability suggestions were applied / dismissed?

To redo just the synthesis pass with a different lead angle, edit `prd/temp/synthesis-plan.md` and re-invoke `Skill(skill: "hyperresearch-prd-24-synthesize")` from a Claude Code session — that step will re-spawn the synthesizer against the same 3 drafts.

To redo the whole run with the same feature request: delete (or move to `prd/runs/archive-*`) the prior artifacts and re-invoke `/hyperresearch-prd`.

## Tier override

If you want to force a tier (e.g., a small feature you want the full adversarial audit on), include this line in your feature request:

```
pipeline_tier: full
```

Step 17 will honor the override and record it in the scaffold.

## Greenfield product

If you have no existing PRDs, step 18 records `existing_product_state: "greenfield"` and proceeds. The PRD will create the canonical vocabulary for the feature area. Add the resulting PRD to `prd/` to seed future runs.
