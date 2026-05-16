# PRD Pipeline Eval — Iteration 1

**Feature simulated:** Parent attendance alert (ManageArk K-12 SIS)
**Tier:** full
**PRD format:** standard_prd
**Eval date:** 2026-05-16

---

# Simulated step trace

**Step 17 — Initialize.** Persists the feature request verbatim to `prd/request-parent-attendance-alert.md`. Decomposes into atomic items: 8 capabilities (C1 opt-in per child per category; C2 absence-mark trigger; C3 in-app inbox alert; C4 optional push; C5 parent acknowledgement; C6 teacher/admin sees ack state; C7 admin global disable per-school; C8 reuse of existing notification-preferences screen pattern). Personas in scope: parent, teacher, admin. Entities implied: Alert, Notification preference, Acknowledgement, Exam-week disable setting. Constraints: parental-consent reuse, English+Hindi, exam-week disable. Out of scope: SMS, multi-guardian routing. Tier classified `full`. Format `standard_prd`. Required section headings: standard 11-heading default. Writes `prd/prd-decomposition.json`.

**Step 18 — Product inventory.** Scans empty PRD directory. Writes `product-inventory.json` with `existing_product_state: "greenfield"` and a `notes` warning that this PRD will create canonical vocabulary. `preferred_terms` is empty — there is no prior canon. Downstream steps will be told to be conservative about "follows existing pattern" claims.

**Step 19 — Feature decomposition.** Reconciles step 17's atomic items against the empty inventory. Builds a `scope_envelope` with in_scope (C1–C8), explicit_out (SMS, multi-guardian routing), implicit_in (opt-in storage, alert inbox surface). Vocabulary translation table is mostly identity (greenfield). Canonical terms locked as: Parent, Teacher, Admin, Student, Classroom, Alert, Notification preference, Acknowledgement. Writes `prd/feature-decomposition.json`.

**Step 20 — Integration map.** Identifies touchpoints in user-visible terms: notification-preferences screen (existing pattern, per the request), parent inbox surface, teacher attendance roster, admin school-settings screen. Maps each capability to entry/exit surfaces. Writes `prd/integration-map.md`. Greenfield caveat is noted — "existing notification-preferences screen pattern" comes from the feature request itself, not from prior PRDs.

**Step 21 — Personas & stories.** Writes one positive story per capability per persona and at least one negative/edge story per capability. Stories include: opt-in-while-disabled, absence-marked-then-rescinded, network drop during marking, multiple absences same day, parent without opt-in opens app post-absence. Stored at `prd/temp/personas-stories.md`.

**Step 22 — Flows & entities.** Writes step-by-step user flows for: opt-in flow, absence-triggered alert delivery, acknowledgement flow, admin exam-week disable flow. User-visible entity field tables for Alert, Notification preference, Acknowledgement, Exam-week disable. No schemas. Writes `prd/temp/flows.md` and `prd/temp/entities.md`.

**Step 23 — Triple draft.** Spawns three prd-draft-orchestrator subagents in parallel. For this feature (no real tensions), defaults to: Draft A breadth-optimized (covers all 8 capabilities with shallow detail); Draft B depth-optimized (deep on alert delivery + acknowledgement + opt-in granularity, lighter on admin disable); Draft C practitioner-optimized (organized around concrete daily-use rituals: morning attendance, parent inbox check, exam-week setup). Drafts at `prd/temp/draft-{a,b,c}.md`.

**Step 24 — Synthesize.** Reads all three drafts. Builds conflict log: A and B differ on whether opt-in defaults to on or off (resolved: off, per "Parent opts in"); A and C differ on whether ack state shows count or per-parent (resolved: per-parent for teacher detail view, count for admin). Writes synthesis plan + outline. Spawns prd-synthesizer subagent (Read+Write) which produces a two-pass integrated PRD at `prd/notes/final_prd_parent-attendance-alert.md`. Target ~2750 words.

**Step 25 — Critics.** Spawns four critics in parallel — instruction, business-value, scope-creep, integration-feasibility. Likely findings: instruction-critic flags "User Stories" if mis-capitalized; scope-creep flags any mention of SMS or guardian fan-out; business-value flags vague metrics or missing pain anchor; integration-feasibility flags any implementation-y language. Findings JSONs at `prd/prd-critic-findings-*.json`.

**Step 26 — Patcher.** Orchestrator triages, then spawns prd-patcher (Read+Edit only). Applies surgical hunks ≤200/500 chars. Typical patches this iteration: rename "class" → "Classroom" in two places; remove a stray reference to "push pipeline"; tighten a vanity metric. Writes `prd/patch-log.json`. Structural issues (none expected here) escalate.

**Step 27 — Polish.** Spawns prd-polish-auditor (Read+Edit). Strips any remaining pipeline-vocab leaks (e.g., "atomic item", "scaffold"), architecture vocabulary remnants (e.g., "API", "endpoint"), filler ("in order to" → "to"), run-ons. Cannot add content. Writes `prd/polish-log.json`.

**Step 28 — Readability audit.** Spawns prd-readability-recommender (Read+Write) which writes JSON recommendations (merge paragraphs, bold key terms, convert listy prose to tables). Orchestrator selectively Edits the PRD. Final artifact: `prd/notes/final_prd_parent-attendance-alert.md` polished and shippable.

---

# Simulated final PRD

# Parent attendance alert — ManageArk

## Overview

When a child is marked absent at school, the people who care most — the parents — are often the last to find out. In many ManageArk-served schools today, a parent learns about an absence only when their child returns home, or worse, when the absence has already become a pattern. The Parent attendance alert feature closes that gap. The moment a teacher marks a child absent in the attendance roster, the parents of that child receive an alert in their ManageArk Parent app inbox and, if they have chosen to receive them, a push notification on their device. Parents acknowledge each alert with a single tap. Teachers and administrators can see, at a glance, which parents have seen which alerts.

This is a category-aware, opt-in system. Parents choose, per child, whether they want alerts for attendance, marks, or behaviour. They are not forced into a firehose. Administrators retain a sharp control: during exam weeks, when alert volume can spike and stress parents during a sensitive time, an Admin can globally disable parent alerts for an entire school. The feature reuses the consent the school already collected during parent onboarding, and it ships in English and Hindi at launch.

The feature is deliberately narrow at v1. SMS delivery and routing to multiple legal guardians per child are out of scope. The product is built on the existing Notification preferences screen pattern so parents do not have to learn a new place to manage what they see.

## Goals & non-goals

**Goals.**

- Reduce the time between a child's absence and the parent learning of it from "end of school day" or worse, to within minutes of the teacher marking it.
- Give parents a single, low-friction surface — the Parent app inbox — for time-sensitive school events, starting with attendance.
- Give parents fine-grained control: per child, per category, opt-in.
- Give teachers and administrators a clear signal of who has been reached and who has not.
- Give administrators a school-wide kill switch for high-stakes weeks.
- Localize the entire feature to English and Hindi at launch.

**Non-goals.**

- This release is not a behaviour or marks alert system. Although the opt-in screen lists those categories so the surface is forward-compatible, only the attendance category produces alerts in v1.
- This release does not deliver alerts over SMS. Push notification and in-app inbox are the only delivery channels.
- This release does not route alerts to multiple guardians per child by relationship rules. A child's "parents" in v1 means the parent accounts already linked to that child in the existing system.
- This release is not an attendance-marking tool. Attendance is marked exactly as teachers mark it today; only the downstream alerting is new.

## Personas

**Parent.** A guardian who has a ManageArk Parent app account and at least one linked child. The Parent is the primary recipient of alerts. They want to know quickly when their child is absent, but they want control over which categories of school events ping them, and per which child. They check the Parent app inbox during commute, lunch, or whenever a notification draws them in.

**Teacher.** A classroom teacher who marks attendance daily in the existing attendance roster. The Teacher's primary job in this feature is unchanged: they mark a child present or absent as they always have. What is new is that, after they mark a child absent, they can see whether the child's parents have received and acknowledged the alert. The Teacher uses this to know when to follow up with a phone call.

**Administrator.** A school-level administrator who manages the school's Parent app posture. The Administrator decides, on behalf of the school, when to suppress parent alerts globally — most commonly during exam weeks when teachers are entering large volumes of attendance and parents are already anxious. The Administrator also sees aggregate acknowledgement metrics for the school.

Out of persona scope for this feature: Student, School-worker. Students do not see attendance alerts. School-workers do not configure them.

## User stories

**S1 — Parent — opt-in.** As a Parent, when I open the Notification preferences screen, I see each of my linked children listed, and under each child I can independently turn on or off Attendance, Marks, and Behaviour alerts. My choices save the moment I tap. I can return at any time to change them.

**S2 — Parent — receives alert.** As a Parent who has Attendance alerts on for my child, when my child is marked absent, I see a new alert in my Parent app inbox, and — if I have push enabled — I get a notification on my device. The alert tells me which child, which Classroom, and when the absence was recorded.

**S3 — Parent — acknowledges.** As a Parent, when I open an attendance alert, I can tap "I have seen this." The alert moves to an acknowledged state. I do not have to type anything.

**S4 — Parent — no alert when opted out.** As a Parent who has turned off Attendance alerts for a child, when my child is marked absent, I do not get an inbox alert and I do not get a push. The school records the absence as normal; my preference is honored.

**S5 — Parent — missed alerts banner.** As a Parent who had Attendance alerts off and then turns them on, the next time I open the app I see a banner: "You missed N attendance events for [child] while alerts were off." I can choose to view them or dismiss the banner.

**S6 — Teacher — sees acknowledgement.** As a Teacher, after I mark a child absent, I can open that child's row and see, per parent, whether each linked parent has received the alert and whether they have acknowledged it. The display uses three states: not yet delivered, delivered but not acknowledged, acknowledged.

**S7 — Teacher — exam-week awareness.** As a Teacher, when the Administrator has disabled parent alerts school-wide, I see a clear banner on the attendance roster: "Parent alerts are paused school-wide until [date]." I can still mark attendance as normal; I simply know the parents are not being pinged.

**S8 — Administrator — disable for exam week.** As an Administrator, I can open the school's settings and toggle off Parent attendance alerts for a date range. While the toggle is off, no parent alerts are generated, regardless of individual parent opt-in. When the date range ends, the toggle re-enables automatically.

**S9 — Administrator — aggregate view.** As an Administrator, I see a school-level dashboard tile showing, for the current day, how many attendance alerts were sent, how many were delivered, and how many were acknowledged. I cannot, from this tile, see individual parent identities.

**S10 — Edge — network drop during marking.** As a Teacher marking attendance on a slow or dropped network, I see a "saved offline — will sync" indicator. When my device reconnects, the absences sync, and alerts go out as if marked at the original time, not at sync time.

**S11 — Edge — multiple absences same day.** As a Parent whose child is marked absent in two consecutive Classroom periods on the same day, I receive one alert per absence event but the alerts are visually grouped under "Today's absences for [child]" in my inbox so I do not feel firehose-spammed.

**S12 — Edge — Hindi locale.** As a Parent whose device language is Hindi, every screen and every alert body — including the missed-alerts banner — is rendered in Hindi.

## User flow

**A. Parent opts in.** Parent opens the Parent app and taps Settings, then Notification preferences. They see one card per linked child. Under each child they see three toggles: Attendance, Marks, Behaviour. They turn Attendance on for the child they care about. The toggle state saves immediately. They navigate away.

**B. Teacher marks a child absent.** Teacher opens the daily attendance roster for their Classroom. They mark a child absent and confirm the row. Behind their action, an Alert is created for that child. The roster row immediately shows a "Parent: not yet delivered" indicator next to the child's name.

**C. Parent receives the alert.** The Parent's inbox gains a new Alert. If push is enabled, the Parent's device buzzes with a notification. The Alert shows the child's name, the Classroom, the date and time the absence was marked, and a single action: "I have seen this."

**D. Parent acknowledges.** The Parent taps "I have seen this." The Alert moves to the Acknowledged section of their inbox. The Teacher's roster row updates the indicator from "delivered, not acknowledged" to "acknowledged."

**E. Administrator disables for exam week.** The Administrator opens School settings, scrolls to Parent alerts, and toggles off Parent attendance alerts. They pick a date range. The toggle saves. Teachers across the school see a banner on their roster the next time they open it. No alerts go out during the range. When the range ends, alerts resume without any further action.

**F. Edge — recovery from offline marking.** A Teacher on a slow network marks several absences. The roster shows "saved offline." On reconnection, the rows sync. For each synced absence, the Alert is created with the original marking time. Parents see one alert per absence, time-stamped accurately.

## User-visible entities & fields

**Alert.** The single notification a Parent sees when their child is marked absent. Fields visible to the Parent: child name, Classroom name, date and time the absence was marked, acknowledgement state, "I have seen this" action. Fields visible to the Teacher: same plus per-parent delivery state and per-parent acknowledgement state. Fields visible to the Administrator: aggregate counts only, no individual content.

**Notification preference.** A per-Parent, per-child, per-category setting. Visible to the Parent only. Fields: child name, category (Attendance, Marks, Behaviour), on/off, last changed. Marks and Behaviour are visible but inactive in v1; the on/off control persists the choice for forward compatibility.

**Acknowledgement.** A state attached to an Alert. Fields visible to the Teacher: which parent acknowledged, time of acknowledgement. Visible to the Parent: their own acknowledgement only. Visible to the Administrator: aggregate counts only.

**Exam-week disable.** A school-level setting. Fields visible to the Administrator: on/off, start date, end date, reason note. Visible to the Teacher: as a banner derived from this setting. Not visible to the Parent.

## Integration with existing product

The Parent attendance alert feature reuses three existing surfaces and modifies one.

**Notification preferences screen (reused, extended).** Parents already manage device-level alert preferences here. The feature adds a per-child, per-category section. The screen's existing pattern — one row per setting, immediate save on toggle — is preserved.

**Parent app inbox (reused).** Alerts land in the existing inbox surface that Parents already check for school messages. No new top-level navigation is introduced. Attendance alerts are tagged with an Attendance label so Parents can filter.

**Attendance roster (modified).** The existing Teacher attendance roster gains a per-row delivery and acknowledgement indicator after a child is marked absent. Marking itself is unchanged.

**School settings (reused, extended).** The existing School settings screen gains a Parent alerts section with the exam-week disable control.

**Onboarding consent (reused, unchanged).** The parental-consent screen that runs during Parent app onboarding already collects consent to receive school communications. This feature relies on that consent and does not introduce a new consent gate.

## Acceptance criteria

- A Parent can, from the Notification preferences screen, independently toggle Attendance alerts on or off for each of their linked children. Toggling saves immediately and persists across app restarts.
- When a Teacher marks a child absent and the child's Parent has Attendance alerts on, the Parent sees an Alert in their inbox. If the Parent has push enabled at the device level, the Parent's device receives a push notification.
- When the same Teacher marks the same child absent and the Parent has Attendance alerts off for that child, the Parent sees no Alert and receives no push.
- When a Parent taps "I have seen this" on an Alert, the Alert moves to the Acknowledged state in the Parent's inbox, and the Teacher's roster row reflects "acknowledged" for that Parent.
- A Teacher viewing the attendance roster sees, per absent child, a per-parent indicator with one of three states: not yet delivered, delivered but not acknowledged, acknowledged.
- An Administrator can set a date range during which all Parent attendance alerts are suppressed school-wide. During that range, no Alerts are created regardless of per-Parent opt-in state. After the range, alerts resume.
- When the exam-week disable is active, Teachers see a banner on the attendance roster naming the date range.
- Every Alert body, every Notification preferences label, every banner, and every acceptance dialog is available in English and in Hindi, switched by the Parent's device language.
- A Parent whose device drops network between absence-marking and alert delivery sees the Alert the next time the device reconnects, with the original absence-marking time stamped on the Alert.
- A Parent who turns Attendance alerts on after they were off sees a "you missed N events" banner on next app open, with a tap-through to the missed events.
- A child marked absent in two consecutive Classroom periods on the same day produces two Alerts grouped under "Today's absences for [child]" in the Parent's inbox.

## Out of scope

- **SMS delivery channel.** Alerts are delivered only via the in-app inbox and optional push notification.
- **Multi-guardian routing rules.** The set of recipients per child is the set of Parent accounts already linked to that child. No relationship-based routing (mother-first, father-first, primary-only) is supported in v1.
- **Marks and Behaviour alert categories.** The opt-in toggles for Marks and Behaviour are visible to preserve the long-term shape of the screen, but no alerts of those categories are generated in v1.
- **Parental consent collection.** Consent is gathered by the existing onboarding flow and is reused as-is. This feature does not introduce, redesign, or replace the consent step.
- **Student-facing surfacing of attendance alerts.** Students do not see, in their own app, that their absence triggered a Parent alert.

## Future scope

- **SMS as a fallback channel.** The team deferred SMS to v1 to avoid the operational and cost overhead of carrier integration; once delivery rates on push are measured, the team will revisit SMS for low-connectivity households.
- **Multi-guardian routing rules.** Several pilot schools have asked for primary-guardian-only routing or sequential delivery. The team deferred this because the v1 cohort can be served by fan-out to all linked Parent accounts; revisit once a clearer requirement emerges from the field.
- **Marks and Behaviour alert categories.** The opt-in screen already exposes these categories so that adding them is a follow-on activation, not a redesign.
- **Additional locales.** Languages beyond English and Hindi were deferred to v1 to keep translation review tight; the next locales will be selected from the field by adoption signal.
- **Per-period quiet hours for Parents.** Parents in the discovery interviews asked for "do not disturb me before 9am" controls; deferred because the v1 hypothesis is that the missed-events banner is enough.

## Success metrics

- **Time-to-knowledge.** Median time between Teacher marking a child absent and the child's first Parent acknowledging the Alert, measured per school. Target at end of pilot: under 20 minutes.
- **Opt-in adoption.** Percentage of eligible Parents who turn Attendance alerts on for at least one child within 14 days of release. Target: 60%.
- **Acknowledgement rate.** Percentage of delivered Alerts that are acknowledged by at least one linked Parent within 24 hours. Target: 70%.
- **Exam-week disable usage.** Percentage of pilot schools that use the exam-week disable at least once during the first exam window. A leading indicator that Administrators trust the control.
- **Hindi-locale satisfaction.** CSAT delta between English-locale Parents and Hindi-locale Parents on the post-alert micro-survey. Target: within 5 points.
- **Operational quiet.** Number of "missed alert" support tickets per 1000 Parents per month. Target: under 2.

---

# Findings

1. **HIGH — Instruction-following — heading capitalization risk.** The required headings include `"User stories"` (lowercase "s"). The simulated PRD uses `## User stories` — matches. But Draft B (depth-optimized) and many natural-writing instincts use Title Case. Risk: a draft that wins synthesis with "## User Stories" survives the instruction-critic only at medium severity (misspelled), and the patcher's ≤200-char cap will fix the heading text but won't reorder. Pipeline-bug: step 23.0 mentions "literal H2 headings... in order" but does not gate at the per-draft level — the draft orchestrator could quietly Title-Case.

2. **HIGH — Coverage gap — C8 not surfaced as a user story.** Capability C8 (reuse of the existing Notification preferences screen pattern) is treated as a constraint by step 17, not a user-visible behavior, so step 21 will not generate a user story for it. It does land in `Integration with existing product`. The scope-creep critic checks for in_scope items silently dropped — but C8 is structurally a constraint, not a capability. The critic taxonomy does not have a slot for "constraint without integration-section coverage." Contract-bug in `feature-decomposition.json` schema.

3. **MEDIUM — Coverage — exam-week disable acceptance criterion ambiguity.** The simulated PRD says "After the range, alerts resume" but does not specify behavior for absences marked during the disabled window — are alerts generated retroactively or skipped permanently? Step 17's atomic-item extraction lists "globally disable per-school during exam weeks" without forcing the orchestrator to disambiguate skipped-vs-deferred. Pipeline-bug in step 17.2.

4. **MEDIUM — Architecture-leak risk — "push notification."** The phrase "push notification" appears in the PRD and is necessary product language (the feature request itself uses it). The instruction-critic's blacklist includes `queue`, `cache`, `pub/sub` but not "push" — which is the right call, but the polish auditor's procedure is not explicit that "push notification" is allowed user-visible vocabulary. Risk: an over-zealous polish pass strips a needed product term. Agent-bug in `prd-polish-auditor` strict rules.

5. **MEDIUM — Vocabulary — greenfield Classroom term.** Step 18 returns `existing_product_state: "greenfield"` with empty `preferred_terms`. Step 19 says "if Classroom is canonical, use Classroom." But with greenfield, there IS no canonical. The PRD invents "Classroom" — which is fine, but the instruction-critic cannot validate it because there's nothing to validate against. Contract-bug: `feature-decomposition.json` should record `vocabulary_provenance: "invented-this-prd"` for greenfield terms so future PRDs can lock to them.

6. **MEDIUM — Length discipline near floor.** Standard_prd target is 2750, range 1500–4000, ±20% band is 2200–3300. The simulated PRD is ~2700 — comfortably in band. But Draft A (breadth-optimized) for a feature this size will naturally come in at ~1700–1900 (under-band), and synthesizer's pass-2 cleanup tends to cut not add. Pipeline-bug: step 24 pass 2 description says "tighten" but does not guard the lower-bound.

7. **MEDIUM — Argumentative density — S6 ack state without entity link.** Story S6 (Teacher sees acknowledgement) references three states but the Acknowledgement entity field table doesn't enumerate the three states explicitly — it says "which parent acknowledged" and "time." The story-to-entity link is implicit, not enforced. Pipeline-bug: step 22.2 entity tables and step 21 stories should be cross-checked.

8. **LOW — Edge case — "rescinded absence."** Step 21.4 lists likely edge cases but not "Teacher un-marks an absence after the alert was sent." The simulated PRD does not address this. Pipeline-bug: step 21.4 examples are illustrative, not a checklist; a feature-specific edge-case enumerator is missing.

9. **LOW — Future-scope rationale present but uneven.** Three future-scope items have crisp rationale ("once delivery rates on push are measured"), two are softer ("once a clearer requirement emerges"). The business-value critic flags items without rationale; "soft rationale" passes. Agent-bug in `prd-business-value-critic`.

10. **LOW — Success metric — "Operational quiet" is borderline vanity.** "Support tickets per 1000 Parents" is observable and user-anchored, so it passes. But the threshold (under 2) has no source. Step 17 does not require metric thresholds to be sourced.

11. **LOW — Pipeline-vocab — none leaked.** Clean. The polish auditor's strict-rules list catches scaffold, atomic items, prd-decomposition. The simulated PRD has none.

12. **LOW — Personas in scope — student/school-worker correctly excluded.** The PRD explicitly names them as out of persona scope, which is good practice but is not required by any step. Pipeline-strength, not a bug.

13. **MEDIUM — Routing — light vs full classification not auditable.** Step 17 classifies tier but the classification rationale is not persisted. If a reviewer asks "why was this full?" the answer is in the orchestrator's head, not in `prd-decomposition.json`. Contract-bug.

14. **HIGH — Routing — light tier skips integration-map (step 20).** Per the entry router: light tier is `17 → 18 → 19 → 23 → 27 → 28`, which skips 20 (integration map), 21 (personas-stories), and 22 (flows-entities). This means a "light" PRD has no Integration with existing product section sourced from a real touchpoint inventory — yet `standard_prd` REQUIRES that heading. A light-tier standard_prd will produce a heading with thin content. Routing-bug.

15. **MEDIUM — Patcher escalation invisibility.** When the patcher escalates a structural finding, the entry router does not specify what the orchestrator does with the escalation. Step 26 says "escalations exist" but the next-step is step 27 (polish), which cannot add content. Structural findings die. Pipeline-bug.

---

# Recommended patches

```json
[
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-23-triple-draft.md",
    "old_string": "Every draft must use the literal H2 headings from `required_section_headings`, in order.",
    "new_string": "Every draft must use the literal H2 headings from `required_section_headings`, in order, with EXACT spelling and EXACT capitalization. Title-casing a heading that is written in sentence case (e.g., `User stories` → `User Stories`) is a violation. Each draft orchestrator must validate its draft's headings against the list before exiting.",
    "rationale": "Closes the heading-capitalization gap (Finding 1). Forces per-draft validation rather than relying on the instruction critic three steps downstream."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-17-initialize.md",
    "old_string": "### 17.2 — Decompose into atomic items",
    "new_string": "### 17.2 — Decompose into atomic items\n\n**Pattern-reuse constraints (e.g., \"uses existing screen X\") count as BOTH a constraint AND a capability.** Record them in `constraints` for non-functional gating, AND in `capabilities` so step 21 generates a user story confirming the reused pattern is honored. Otherwise pattern-reuse silently disappears from user-visible coverage.",
    "rationale": "Addresses Finding 2. Forces C8-class items (constraints that imply user-visible behavior) into the capability coverage matrix."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-17-initialize.md",
    "old_string": "- **capabilities** — what the feature must DO (e.g., \"send attendance alert to parent when student is absent\").",
    "new_string": "- **capabilities** — what the feature must DO (e.g., \"send attendance alert to parent when student is absent\"). For each capability, ALSO record `disambiguations: []` — questions the orchestrator should answer before user stories are drafted (e.g., for a disable feature: \"are alerts skipped permanently or deferred to after the disable window?\"). Empty list is allowed; missing field is a contract violation.",
    "rationale": "Addresses Finding 3. Forces step 17 to surface ambiguities (skipped-vs-deferred, on-vs-off-default) before step 21 turns them into stories."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/agents/prd/prd-polish-auditor.md",
    "old_string": "## Strict rules\n\n- You CANNOT Write new files. The polish log is pre-stubbed; you Edit it.\n- You CANNOT introduce content. You can rewrite a phrase but you can't add new claims, new acceptance criteria, new personas, new entities.\n- You CANNOT change the section headings.\n- You CANNOT change the H1 / title.",
    "new_string": "## Strict rules\n\n- You CANNOT Write new files. The polish log is pre-stubbed; you Edit it.\n- You CANNOT introduce content. You can rewrite a phrase but you can't add new claims, new acceptance criteria, new personas, new entities.\n- You CANNOT change the section headings.\n- You CANNOT change the H1 / title.\n- **Allowed user-visible product vocabulary** (do NOT strip these even though they look architectural): `push notification`, `inbox`, `banner`, `toggle`, `dashboard`, `roster`, `screen`. These are the words users see in the product UI. Strip only the architecture words explicitly listed in step 27 (API, endpoint, database, schema, queue, cache, etc.).",
    "rationale": "Addresses Finding 4. Prevents over-zealous stripping of user-visible product terms that share surface form with architecture vocabulary."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-19-feature-decomposition.md",
    "old_string": "### 19.1 — Normalize vocabulary",
    "new_string": "### 19.1 — Normalize vocabulary\n\n**Greenfield handling.** If `product_inventory.existing_product_state == \"greenfield\"`, `preferred_terms` is empty. In that case, the orchestrator MUST invent canonical terms for every entity in `entities_implied` and record them in `feature-decomposition.json` under `vocabulary.invented_terms: { term: \"<canonical>\", aliases: [\"<request-word>\"], provenance: \"invented-this-prd\" }`. Downstream PRDs read this and lock to it.",
    "rationale": "Addresses Finding 5. Makes greenfield vocabulary explicit and durable instead of implicit and brittle."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-24-synthesize.md",
    "old_string": "## Exit criterion\n\n- `prd/notes/final_prd_<prd_tag>.md` exists.\n- All required section headings present in order.\n- Word count within ±20% of target.\n- Validation gate passes (or remaining violations are minor and logged for step 26).",
    "new_string": "## Exit criterion\n\n- `prd/notes/final_prd_<prd_tag>.md` exists.\n- All required section headings present in order, with exact spelling and capitalization.\n- Word count within ±20% of target band middle. If the synthesized PRD is below the floor, the synthesizer's pass 2 must EXPAND under-developed sections (typically User stories, Acceptance criteria, Edge cases) using material already present in the 3 drafts; pass 2 is not exclusively a cutting pass.\n- Validation gate passes (or remaining violations are minor and logged for step 26).",
    "rationale": "Addresses Finding 6. Synthesizer's pass 2 was framed as a cut-only pass; explicit lower-bound guidance prevents under-length PRDs."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-22-flows-entities.md",
    "old_string": "## Procedure",
    "new_string": "## Procedure\n\n**Cross-check invariant.** Before exiting, verify that every distinct state or value mentioned in any user story from step 21 appears as either an enumerated field value, a state transition, or a per-persona view difference in the entity tables. If story S6 says \"three states: not yet delivered, delivered but not acknowledged, acknowledged\" then the Acknowledgement entity table must enumerate exactly those three states. Mismatches are a high-severity finding for the instruction critic.",
    "rationale": "Addresses Finding 7. Forces story-to-entity consistency at write time rather than catching it at critic time."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-21-personas-stories.md",
    "old_string": "# step-21-personas-stories",
    "new_string": "# step-21-personas-stories\n\n**Edge-case enumerator (mandatory).** For every capability, generate edge stories from this checklist before stopping. Skip an item only if it is genuinely inapplicable, and record why in `prd/temp/edge-case-coverage.md`:\n\n1. Opt-in-off then triggering event.\n2. Network drop during user action.\n3. Same triggering event occurs N times in quick succession.\n4. The triggering event is undone / rescinded after the alert went out.\n5. The actor's locale is the non-default language.\n6. The actor is on a device-class with no push capability.\n7. The feature is globally disabled (admin kill switch) at the moment of the event.",
    "rationale": "Addresses Finding 8. Replaces step 21.4's illustrative examples with a real checklist, including the rescinded-event case the simulation missed."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/agents/prd/prd-business-value-critic.md",
    "old_string": "4. **Future scope without rationale.** Each future-scope item must link to a current constraint or known pain (\"we deferred multi-language because the research showed it's a phase-2 priority\"). Items without rationale are speculative bloat.",
    "new_string": "4. **Future scope without rationale.** Each future-scope item must link to a current constraint or known pain (\"we deferred multi-language because the research showed it's a phase-2 priority\"). Items without rationale are speculative bloat. SOFT rationale (\"once a clearer requirement emerges\", \"when we have more data\") counts as MISSING rationale and is a medium finding — push for a concrete constraint, cost, or measurable trigger.",
    "rationale": "Addresses Finding 9. Tightens the rationale bar so future-scope items can't pass with hand-waving language."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-17-initialize.md",
    "old_string": "### 17.5 — Define `required_section_headings`",
    "new_string": "### 17.5 — Define `required_section_headings`\n\n**Persist the tier classification rationale.** Add a `tier_rationale` field to `prd-decomposition.json` with one sentence on why this feature is `light` vs `full` (number of personas, presence of cross-cutting constraints, presence of edge cases). This is auditable.\n",
    "rationale": "Addresses Finding 13. Makes tier classification auditable rather than implicit."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd.md",
    "old_string": "- **light:** `17 → 18 → 19 → 23 (single draft) → 27 → 28` — small features, 20–30 min.",
    "new_string": "- **light:** `17 → 18 → 19 → 20 → 21 → 23 (single draft) → 27 → 28` — small features, 20–30 min. Steps 20 and 21 are KEPT in the light path because every standard_prd requires an `Integration with existing product` heading and a `User stories` heading; skipping them produces a heading with thin content. Step 22 (flows + entities) remains full-tier only.",
    "rationale": "Addresses Finding 14. Light tier currently skips the only step that sources Integration content and the only step that sources stories; this leaves required headings empty for a standard_prd."
  },
  {
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-26-patcher.md",
    "old_string": "## Procedure",
    "new_string": "## Procedure\n\n**Escalation handling.** Patcher escalations are NOT closed by step 27 (polish cannot add content). After step 26 returns, the entry router must inspect `patch-log.json.escalations`. If the array is non-empty, the orchestrator re-runs step 24 (synthesizer) with the escalation list appended to its inputs and a directive to add the missing content, THEN proceeds to step 25 again — bounded to one re-loop. If the re-loop still leaves escalations open, the PRD ships with a `## Known gaps` appendix listing them.",
    "rationale": "Addresses Finding 15. Closes the dead-letter path for structural critic findings."
  }
]
```

---

# Summary

**Findings:** 15 total — 3 high, 7 medium, 5 low.

**Recommended patches:** 12 (covering all 15 findings; Findings 10–12 do not need patches — 10 is acceptable-as-is, 11 is a pass, 12 is a strength).

**Categories:** 4 pipeline-bugs, 2 agent-bugs, 4 contract-bugs, 2 routing-bugs, 3 mixed.

**Assessment:** **Pipeline needs 3 high-severity patches before it is ship-ready.** The two highest-leverage fixes are (a) routing-bug 14 — the light tier currently skips the only steps that source two required headings, so a light-tier standard_prd ships with thin sections by design; and (b) pipeline-bug 2 — pattern-reuse constraints (like "reuse the existing notification-preferences screen pattern") never become user stories, so a critical class of in-scope behavior is silently dropped from coverage. The medium-severity patches around heading capitalization, greenfield vocabulary, story-to-entity cross-checks, and synthesizer lower-bound guarding will materially raise instruction-following scores in iteration 2.
