# PRD Pipeline Eval — Iteration 2

**Feature simulated:** Parent attendance alert (ManageArk K-12 SIS)
**Tier:** full
**PRD format:** standard_prd
**Eval date:** 2026-05-16
**Prior iteration:** `prd-pipeline-eval-iteration-1.md` (15 findings: 3 high, 7 medium, 5 low; 12 patches applied)

---

# Simulated step trace (17–28)

**Step 17 — Initialization & decomposition.** Orchestrator writes `prd/request-parent-attendance-alert.md` (verbatim feature request, gospel). Classifies as `full` tier (4 personas including admin school-week-scope; multi-flow opt-in / deliver / acknowledge / globally-disable; cross-module: notifications, attendance, admin). Writes `prd_format: "standard_prd"`. Required section headings (sentence case): `Overview`, `Problem and goals`, `Personas`, `User stories`, `Integration with existing product`, `Acceptance criteria`, `Edge cases`, `Out of scope`, `Future scope`, `Success metrics`. Atomic items: C1–C8 capabilities (C8 = reuse Notification preferences screen pattern — dual-classed under both `constraints` AND `capabilities` per patch-2; with `disambiguations: ["disable = skip permanently or deferred?"]` on C7 per patch-3). P1–P3 personas. E1–E4 entities. F1–F5 flows. `tier_rationale` persisted to `prd-decomposition.json` per patch-10. Writes scaffold with Tier rationale subsection.

**Step 18 — Product inventory.** Scans `prd/` for prior PRDs. None found → `existing_product_state: "greenfield"`; `preferred_terms: []`. Records `discovery_method: "directory_scan"` and prior PRD count 0.

**Step 19 — Feature decomposition reconciled.** Since greenfield, orchestrator invents canonical terms per patch-5: `Alert` (aliases: "alert", "notification"), `Notification preference` (aliases: "opt-in"), `Acknowledgement` (aliases: "ack"), `Exam-week disable` (aliases: "global disable"), `Classroom` (aliases: "class"). All written to `feature-decomposition.json.vocabulary.invented_terms` with `provenance: "invented-this-prd"`. Coverage matrix built: C1–C8 each mapped to user-facing surfaces and personas.

**Step 20 — Integration map.** For every capability and entity, document where it surfaces in the (greenfield) product. Since no existing screens, integration is anchored to the named patterns: "Notification preferences screen pattern", "Inbox surface", "Teacher attendance roster". C8 (reuse pattern) explicitly surfaces here AND as a user story (per patch-2 dual classing).

**Step 21 — Personas & user stories.** Three personas (parent, teacher, admin). Stories drafted per capability (8 positive + 8 edge per patch-8 mandatory 7-item checklist + 1 reuse-pattern story for C8 per patch-2). The 7 edge-case items applied to each in-scope capability: opt-in-off-then-event, network-drop, multi-fire, undo-after-alert, locale-Hindi, no-push-device, admin-kill-switch. Items genuinely inapplicable (e.g., locale doesn't apply to admin-only flows) recorded in `prd/temp/edge-case-coverage.md` with reasons.

**Step 22 — Flows & entities.** F1: parent opts in; F2: teacher marks absent → alert delivered; F3: parent acknowledges; F4: admin disables for exam week. Entities Alert (states: not_delivered / delivered_unack / acknowledged), Notification preference, Acknowledgement, Exam-week disable. Cross-check invariant per patch-7: every state mentioned in stories is enumerated in entity tables. Three Alert states pass; "deferred" vs "skipped" for exam-week disable initially missing — caught by invariant, escalated to step 17's disambiguations and resolved as "skipped permanently."

**Step 23 — Triple-draft.** Three prd-draft-orchestrator subagents spawn in parallel — angle A (parent-anchored), B (teacher-anchored), C (admin/admin-policy). Each receives `required_section_headings` and writes ~2200 words. **Per patch-1, the orchestrator skill instructs validation against the literal heading list before exit** — but the **agent prompt itself in `prd-draft-orchestrator.md` still says only "Headings are the literal required_section_headings. After writing, exit"** (no enforcement language inside the agent prompt). Draft B uses Title Case ("User Stories") and exits without self-blocking — partial landing.

**Step 24 — Synthesizer.** Single spawn, tool-locked to Read+Write, two passes. Pass 1: rough integrated draft from angle A lead with B's flow density and C's admin guard borrowed. Pass 2 per patch-6: cuts voice shifts AND expands under-developed sections (Edge cases section initially 180 words, expanded to 380 using already-present material). Synthesized PRD at ~2780 words. Heading capitalization carries Draft B's "User Stories" leak into pass 1; pass 2 catches it via `required_section_headings` re-check.

**Step 25 — Critics (4 in parallel).** Instruction-critic flags: 1 heading capitalization residue from Draft B (caught by synthesizer, low-severity in log); 0 missing headings. Business-value-critic per patch-9 flags any future-scope item with soft rationale ("when we have more data") at medium. Scope-creep-critic: clean (SMS, multi-guardian both correctly excluded). Integration-feasibility-critic: clean.

**Step 26 — Patcher (Read+Edit only).** Pre-stubbed log. Patcher applies ≤2 hunks (rename "class" → "Classroom" in one passage, tighten a soft-rationale future-scope item). Per patch-12, orchestrator inspects `patch-log.json.escalations` after return. If non-empty, one bounded re-loop through synthesizer → critics → patcher. In this run, escalations empty → re-loop not triggered. Net OK.

**Step 27 — Polish auditor (Read+Edit only).** Strips filler. Per patch-4, allowed product vocabulary preserved: "push notification", "inbox", "banner", "toggle", "dashboard", "roster", "screen" — none stripped despite looking architectural. Strips "queue", "endpoint", "API" if present. Net char delta negative (correct direction).

**Step 28 — Readability audit.** Recommender (Read+Write) writes JSON recommendations: merge two short paragraphs in Edge cases; bold the three Alert states on first use; convert acceptance-criteria prose to bulleted list. Orchestrator selectively Edits per its own judgment. Final artifact: `prd/notes/final_prd_parent-attendance-alert.md` shipped.

---

# Simulated final PRD (~2780 words)

# Parent attendance alert — ManageArk

## Overview

ManageArk parents need to know — within the school day, not at end-of-day — when their child has been marked absent. Today there is no notification surface for absences. Teachers mark attendance in the roster; parents discover absences through SMS sent in bulk hours later, or via word of mouth. This PRD introduces a parent-opt-in, per-category, in-app inbox alert with optional push notification, an acknowledgement signal teachers and admins can see, and a school-level kill switch admins can toggle during exam weeks. The feature is launched in English and Hindi for v1, reuses the existing Notification preferences screen pattern, and respects the parental-consent flow that already lives in onboarding. SMS and multi-guardian routing are out of scope for v1.

## Problem and goals

**Concrete user pain.** A parent of a Class 6 student in Lucknow currently learns of an unexplained absence at 6:47 pm when the school's bulk SMS goes out — six hours after the absence began. Two distinct harms follow: (a) the parent can't intervene during the day (call the child, call the school, check whether the child is actually at a tuition class), and (b) the parent can't confirm receipt to the school, so the teacher has no signal that the message arrived. Across the cohort, three out of four parents in our pre-launch interviews said they would value a same-period notification more than the end-of-day digest.

**Business outcome we are moving.** Reduce parent-side time-to-awareness from end-of-day (≥6 hours) to under 10 minutes for 85% of marked absences, measured per school week. Secondary outcome: drive Notification preferences screen adoption — every parent who opts into attendance alerts is a parent we can reach for marks and behaviour categories in v2.

**What success looks like (user-visible).** A parent receives an inbox alert (and a push, if device permission was granted) within 10 minutes of the teacher saving the roster. The parent acknowledges with one tap. The teacher sees acknowledgement state in their roster view. An admin can mute the school's parent alerts for an exam week without touching any other category.

## Personas

**Parent (P1) — primary.** A guardian of a single child or multiple children at the same ManageArk school. Receives alerts; opts in per child per category; acknowledges alerts. Speaks English or Hindi. May or may not have push permission granted on their device. Out-of-scope persona variants: secondary guardians (multi-guardian routing is v2).

**Teacher (P2) — actor.** Marks attendance on the daily roster. Sees per-parent acknowledgement state. Does not configure parent-side opt-in. Is informed (via a roster banner) when the school is in an exam-week disable window so they understand why parents may not have been notified.

**Admin (P3) — gatekeeper.** Configures the school-level exam-week disable. Sees aggregate (not individual) acknowledgement counts on the school dashboard. Does not see per-child Alert content. Cannot opt parents in or out — that remains the parent's choice.

**Out of persona scope:** students (no student-facing surface); school-workers other than teacher and admin (e.g., bursars, drivers).

## User stories

**S1 — Parent — C1, C2 — opt-in.** As a parent, on the Notification preferences screen, I want to toggle attendance alerts on per child, so I receive an alert only for the children I want covered. Acceptance: a per-child row with an Attendance toggle exists, persists immediately, and shows last-changed timestamp.

**S2 — Parent — C3 — receive alert.** As a parent who has opted in for my child, when the teacher marks my child absent, I want an inbox entry within 10 minutes and a push (if permitted), so I can act during the school day. Acceptance: inbox alert appears within 10 minutes 85% of the time; push delivered if device-permission and locale supported.

**S3 — Parent — C4 — acknowledge.** As a parent, after seeing an alert in the inbox, I want a one-tap acknowledgement, so the teacher knows I've seen it. Acceptance: tapping "I have seen this" transitions the Alert to acknowledged for that parent within 2 seconds, and the action is durable across app restarts.

**S4 — Teacher — C5 — see ack state.** As a teacher, in the roster, after I mark a student absent, I want to see which parents have acknowledged the alert, so I know whether to call the home. Acceptance: the roster row shows three states for the absence — not yet delivered, delivered but not acknowledged, acknowledged — visible per parent.

**S5 — Admin — C6 — see aggregate ack.** As an admin, on the school dashboard, I want to see the per-day percentage of alerts acknowledged, so I can spot under-performing communications. Acceptance: a single number per school day, updated within 15 minutes of the close-of-day. No individual content shown.

**S6 — Admin — C7 — exam-week disable.** As an admin, before an exam week, I want to disable parent alerts school-wide with a date range and a reason note, so parents aren't pinged during exam stress. Acceptance: setting the range is one screen; teachers see a banner explaining; alerts triggered during the disabled window are skipped permanently (not deferred); on resume, only new absences trigger alerts.

**S7 — Parent — C8 — reuse Notification preferences pattern.** As a parent, my Notification preferences screen looks and behaves like the rest of the app's preference screens, so I don't have to relearn controls. Acceptance: the screen reuses the existing Notification preferences screen pattern (toggle rows grouped by child, category sub-rows). This story exists explicitly because the reuse is a user-visible constraint, not an implementation detail.

**S8 — Parent — C2 — locale.** As a Hindi-speaking parent, when an alert arrives, the inbox entry and the push body are in Hindi, so I understand it instantly. Acceptance: locale derived from app setting; both inbox copy and push copy localized for v1 English and Hindi.

**Edge-case stories (negative).**
- **S1-neg.** Parent has not opted in. Outcome: no inbox entry, no push. Optional reminder banner in the inbox: "you missed N absences while alerts were off."
- **S2-neg.** Teacher saves the roster, then network drops. Outcome: roster saves offline with a "saved offline — will sync" indicator; once back online, alerts go out as if marked at the original time.
- **S3-neg.** Teacher accidentally marks absent then corrects to present within 60 seconds. Outcome: if the alert has not yet been sent, it is suppressed; if already sent, a "correction" alert replaces the original inbox entry.
- **S4-neg.** Same child marked absent three times in five minutes (teacher edits). Outcome: the parent sees one consolidated inbox alert, not three; the latest state wins.
- **S5-neg.** Parent's device has no push permission granted. Outcome: inbox-only delivery; no push attempted; no error surfaced to the parent.
- **S6-neg.** Parent's locale is Hindi but the alert template hasn't been translated. Outcome: fall back to English, log a missing-translation event for the localization team.
- **S7-neg.** Admin's exam-week disable starts mid-day. Outcome: alerts already queued for that day's absences are sent; new absences during the window are not.

## Integration with existing product

**Notification preferences screen.** A new "Attendance" toggle row is added inside each child's preferences group on the existing Notification preferences screen. The toggle uses the same control as Marks and Behaviour (forward-compatible). Marks and Behaviour rows remain visible but inactive in v1; the on/off state persists for v2.

**Inbox.** Alerts surface as a new inbox-card type with title "Absence today — \<child name\>", a body line "\<Classroom\> · marked absent at \<time\>", and a primary action "I have seen this." Acknowledgement state persists across devices.

**Teacher roster.** The attendance roster gains a thin status strip per absence row showing per-parent delivery and acknowledgement state. Hovering or tapping reveals the three Alert states.

**Admin school dashboard.** A new tile titled "Alert acknowledgement (last 7 school days)" appears on the school's overview dashboard. A separate Settings sub-page hosts the exam-week disable control.

**Onboarding parental-consent flow.** The existing parental-consent step in onboarding is the legal basis for sending alerts. No change to the consent text; the feature reuses the consent already captured. The PRD does not introduce a second consent moment.

## Acceptance criteria

1. A parent opts in per child per category from the Notification preferences screen; the toggle persists immediately and survives logout / re-login.
2. When a teacher saves the roster with an absence and the parent is opted in for that child's Attendance category, the parent receives an inbox alert within 10 minutes for 85% of cases, measured per school week.
3. If the device has notification permission granted and the locale (English or Hindi) is supported, a push notification is delivered with the same content as the inbox alert.
4. The parent can transition the Alert to acknowledged with one tap from the inbox; the change is visible to the teacher within 30 seconds.
5. The teacher's roster shows three states per absence per parent: not yet delivered, delivered but not acknowledged, acknowledged.
6. The admin can configure an exam-week disable (start date, end date, reason note) school-wide; during the window, absences trigger no alerts; on the day after end-date, alerts resume; absences marked during the window are skipped permanently and are NOT retroactively alerted.
7. Teachers see a banner in their roster while the school is in a disabled window, with the admin's reason note inlined.
8. The Notification preferences screen reuses the existing pattern's layout, toggle behavior, and grouping; no net-new control style is introduced for this feature.
9. All parent-facing copy (inbox card, push body, preferences row label) is available in English and Hindi for v1; missing translations fall back to English and log a missing-translation event.
10. Aggregate acknowledgement rate per day is visible to admins on the school dashboard; no individual alert content is visible at the admin tier.

## Edge cases

**Opt-in off at time of event.** Parent has not enabled the Attendance category for the affected child. No alert is generated. The next time the parent opens the inbox after a missed absence, a soft "you missed N absences while alerts were off" banner appears with a one-tap "turn on" link.

**Network drop during teacher save.** The roster persists the change to local storage with an "offline — will sync" badge. When network returns, the absence is committed and alerts go out as if marked at the original time (timestamps preserved).

**Multiple rapid edits for the same student.** The teacher marks Aisha absent at 09:01, undoes at 09:02, re-marks at 09:04. The parent sees exactly one inbox alert reflecting the latest state. Earlier in-flight alerts are suppressed or replaced; no parent sees a flapping inbox.

**Absence rescinded after alert sent.** A "correction — your child is present" inbox entry replaces the absence entry. The acknowledgement state resets.

**Non-default locale.** Parent's locale is Hindi. Inbox body and push body render in Hindi. If a Hindi translation is missing for a specific message, render English and log the gap; never render a blank or placeholder.

**No push capability.** Parent's device has push permission denied or no push channel available. Inbox-only delivery; no failed-push surface shown to the parent.

**Admin kill switch active.** School is in an exam-week disable window. No alerts triggered for absences marked during the window — these are skipped permanently. Alerts for absences marked before the window proceed normally. Teachers see a roster banner during the window; the banner disappears on the day after end-date.

## Out of scope

- SMS channel — v1 is in-app inbox plus optional push only.
- Multi-guardian routing rules — v1 assumes one parent account per child for delivery purposes. Households with two parent accounts each individually opt in.
- Marks alerts and Behaviour alerts — v1 surfaces the toggles for forward compatibility, but they are inactive.
- Languages other than English and Hindi — v1.
- Admin per-classroom disable — v1 is school-wide only.
- Parent-side delivery preference (push vs inbox) — v1 always delivers inbox; push follows device permission.

## Future scope

- **SMS channel for parents without smartphones.** Deferred because pre-launch interviews showed 88% of in-scope parents have a smartphone and an installed ManageArk app; SMS adds operational cost and a second consent surface. Trigger to revisit: when smartphone-coverage among new-school cohorts drops below 80%.
- **Multi-guardian routing.** Deferred because the underlying guardian-graph model does not yet exist in ManageArk. Trigger to revisit: after the guardian-relationship model ships in onboarding (planned Q3).
- **Marks and Behaviour alerts.** Toggles are visible-but-inactive in v1; activating them requires the marks-publication flow and the behaviour-incident flow, both currently in design. Trigger: when those flows ship.
- **Parent-side delivery channel preference.** Deferred until we have v1 telemetry on push delivery rates; if push proves unreliable in low-bandwidth schools we'll add inbox-only as an explicit choice. Trigger: 30 days of post-launch delivery-rate data.
- **Admin per-classroom disable.** Deferred because no school requested it in the pre-launch panel. Trigger: any school requesting it in support.

## Success metrics

- **Awareness time (primary).** 85% of marked absences result in a parent inbox alert (and push, if eligible) within 10 minutes, measured per school week.
- **Adoption.** 60% of parents in launch cohorts toggle Attendance alerts on within their first 30 days of the v1 release.
- **Acknowledgement.** 70% of delivered alerts are acknowledged within 24 hours, measured per school week.
- **Operational quiet.** Fewer than 2 support tickets per 1000 parents per month tagged "attendance alert" in the first 90 days.
- **Localization quality.** Hindi-locale alerts have ≤2% missing-translation fallback rate.

---

# Patch-landing check

| # | Patch | Landed? | Evidence |
|---|---|---|---|
| 1 | Per-draft heading capitalization gate (step 23) | **PARTIAL** | Skill `hyperresearch-prd-23-triple-draft.md` step 23.0 now includes the "EXACT spelling … validate before exiting" sentence. **But** `agents/prd/prd-draft-orchestrator.md` `Output` section still reads only "Headings are the literal required_section_headings … After writing, exit." with no validation step inside the agent prompt itself. Agent prompts are what subagents actually read at spawn time — the skill paragraph instructs the orchestrator, not the draft-writing subagent. Draft B can still ship Title Case undetected. |
| 2 | Pattern-reuse dual-classed (constraints + capabilities) | **YES** | Step 17.2 includes "Pattern-reuse constraints … count as BOTH a constraint AND a capability … so step 21 generates a user story." Simulated S7 (C8 reuse-pattern story) is now emitted. |
| 3 | Per-capability `disambiguations` field | **YES** | Step 17.2 capability bullet includes "ALSO record `disambiguations: []`. Empty list is allowed; missing field is a contract violation." Simulated C7 disambiguation about exam-week disable behavior surfaces and is resolved. |
| 4 | Polish-auditor allowed product vocabulary | **YES** | `prd-polish-auditor.md` Strict-rules includes the allow-list `push notification, inbox, banner, toggle, dashboard, roster, screen`. Simulated PRD retains "inbox", "banner", "roster", "screen", "push notification" untouched. |
| 5 | Greenfield invented-terms recording (step 19) | **YES** | Step 19.1 has the "Greenfield handling" block: "the orchestrator MUST invent canonical terms … record in `feature-decomposition.json` under `vocabulary.invented_terms`". Simulated greenfield case records `Alert`, `Notification preference`, etc. |
| 6 | Synthesizer pass-2 may EXPAND | **YES** | Step 24 Exit criterion: "If the synthesized PRD is below the floor, the synthesizer's pass 2 must EXPAND under-developed sections … pass 2 is not exclusively a cutting pass." `prd-synthesizer.md` Pass 2 also explicitly says "If you're under, look for capabilities … add one." |
| 7 | Step 22 story-to-entity cross-check invariant | **YES** | Step 22 Procedure has "Cross-check invariant. Before exiting, verify that every distinct state or value mentioned in any user story from step 21 appears as either an enumerated field value, a state transition, or a per-persona view difference in the entity tables." |
| 8 | Step 21 mandatory edge-case checklist (7 items) | **YES** | Step 21.4 has "Edge-case enumerator (mandatory). For every capability, generate edge stories from this checklist before stopping. Skip an item only if it is genuinely inapplicable, and record why in `prd/temp/edge-case-coverage.md`." 7 items listed. |
| 9 | Business-value critic: soft rationale = missing rationale | **YES** | `prd-business-value-critic.md` "Future scope without rationale" bullet: "SOFT rationale ('once a clearer requirement emerges', 'when we have more data') counts as MISSING rationale and is a medium finding." |
| 10 | Tier rationale persisted to `prd-decomposition.json` | **YES** | Step 17.6 schema includes `"tier_rationale": "<2-3 sentences>"` and `"format_rationale": "<2-3 sentences>"`. Step 17.8 also writes a Tier rationale subsection to scaffold (parallel persistence, OK). |
| 11 | Light tier now includes steps 20 + 21 | **YES** | Entry router Tier routing table: `light: 17 → 18 → 19 → 20 → 21 → 23 (single draft) → 27 → 28`, with explicit "Light-tier note" that steps 20 and 21 are KEPT because the required headings depend on them. |
| 12 | Step 26 escalation re-loop (bounded one pass) | **YES** | Step 26.2.5 "Escalation re-loop (one bounded pass)" with explicit termination: "If, after this single re-loop, escalations remain open, ship with a `## Known gaps` appendix … Do NOT extend the loop further." |

**Landed:** 11 of 12.
**Partial:** 1 (patch-1 only in skill, not in agent prompt — high-severity regression).

---

# Findings (iteration 2)

## HIGH

### F1 — HIGH — Patch-1 partial-landing (heading capitalization gate not in the agent prompt). REGRESSION.

The patch text landed in `hyperresearch-prd-23-triple-draft.md` step 23.0 (the orchestrator skill), but `agents/prd/prd-draft-orchestrator.md` is what each spawned draft subagent actually reads. Its `Output` section still says: *"Headings are the literal `required_section_headings`. Length is within the target band. No frontmatter. After writing, exit. The main orchestrator will validate and synthesize."* No per-draft self-validation gate. A spawned draft can still title-case "User Stories" and exit cleanly. Iteration-1's Finding 1 is not fully closed.

**Category:** agent-bug.
**Severity:** HIGH (regression — patch did not produce intended behavior).

## MEDIUM

### F2 — MEDIUM — Step 26 escalation re-loop has no idempotency / state-machine guard against cascading re-spawns. NEW.

The re-loop instruction (patch-12) says "re-spawn synthesizer ONCE, critics ONCE, patcher ONCE." It relies on the orchestrator counting. There is no on-disk re-loop counter (e.g., `patch-log.json.reloop_count`) and no schema enforcement. If the orchestrator gets compacted and resumed mid-re-loop, it may believe the re-loop hasn't run and re-spawn again. Second-order issue iteration 1 missed (recovery-from-compaction completeness).

**Category:** pipeline-bug (recovery).
**Severity:** MEDIUM.

### F3 — MEDIUM — Edge-case checklist over-generation risk for one_pager / simple features. NEW (caused by patch-8).

The mandatory 7-item enumerator is unconditional across tiers and prd_formats. For a one_pager (300–800 words, single-capability feature), 7 × N edge stories can blow length budget. The "skip if inapplicable" escape is allowed but requires the orchestrator to justify each skip in `edge-case-coverage.md` — heavyweight for a one-pager. Either (a) gate the full enumerator to standard_prd / detailed_prd, (b) require ≤2 edge cases for one_pager tier, or (c) explicitly note that skip-with-justification is the expected path for one_pagers.

**Category:** contract-bug (introduced by iter-1 patch).
**Severity:** MEDIUM.

### F4 — MEDIUM — Patch-1 / patch-7 / patch-22 validation gates are advisory text, not structured invariants. NEW.

Multiple iter-1 patches embed validation requirements as prose: "Each draft orchestrator must validate its draft's headings…", "Before exiting, verify that every distinct state or value…". None of these are encoded in a machine-checkable artifact (e.g., a `validation-gates.json` the orchestrator reads at boundary). The orchestrator has to remember to check; the subagent has to remember to self-check. Second-order issue.

**Category:** contract-bug.
**Severity:** MEDIUM.

### F5 — MEDIUM — Tier-rationale double-persistence (decomposition.json AND scaffold.md) creates drift risk. NEW (caused by patch-10).

Patch-10 added `tier_rationale` to the `prd-decomposition.json` schema (step 17.6), but step 17.8's "Append a Tier rationale subsection to `prd/scaffold.md`" was kept. Two persistence sites for the same value invites divergence if either is hand-edited later. Pick one canonical home (recommend the JSON; the scaffold can quote it).

**Category:** contract-bug.
**Severity:** MEDIUM.

## LOW

### F6 — LOW — `disambiguations` empty-list vs missing-field distinction is fragile. NEW (caused by patch-3).

Patch-3 says "Empty list is allowed; missing field is a contract violation." There is no validator that runs after step 17 to enforce presence. The instruction-critic checks PRD content; nothing checks `prd-decomposition.json` shape. Add a step-17.7 schema-validation sub-step or accept that this contract is unenforced.

**Category:** contract-bug.
**Severity:** LOW.

### F7 — LOW — Polish auditor allow-list lives only in the agent prompt, not in step-27 skill. NEW (caused by patch-4).

The allow-list `push notification, inbox, banner, toggle, dashboard, roster, screen` is in `prd-polish-auditor.md` Strict rules, but step-27 skill's hygiene-list still enumerates only the architecture words to strip. A reviewer reading step-27 alone wouldn't see the allow-list. Mirror it in the skill so the orchestrator can pre-flag false positives before spawning.

**Category:** contract-bug.
**Severity:** LOW.

### F8 — LOW — Light tier now risks length-floor underrun for standard_prd. NEW (caused by patch-11).

Patch-11 keeps light at single-draft (step 23 single-write, skips step 24 synthesizer). A single draft has no two-pass expansion loop, so a light-tier standard_prd that comes in under 1500 words has no recovery path. Either (a) add a brief "if under floor, re-pass" instruction in step 23's light-tier branch, or (b) require light tier to use prd_format = one_pager, not standard_prd.

**Category:** routing-bug.
**Severity:** LOW.

## PASSES / STRENGTHS (no patch needed)

### P1 — Patches 2, 3, 5, 6, 7, 8, 9, 11, 12 all land cleanly. The simulated PRD shows S7 (C8 reuse story), greenfield invented terms, expanded Edge cases section, exam-week skip-permanently disambiguation, and a clean tier-routing table.

### P2 — No iter-1 regressions other than F1 detected. Findings 3, 4, 6 (instruction critic), 8 (synthesizer floor) from iter-1 are fully closed.

---

# Recommended patches

```json
[
  {
    "id": "patch-2-1",
    "severity": "HIGH",
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/agents/prd/prd-draft-orchestrator.md",
    "old_string": "A single Markdown file at `output_path`. Headings are the literal `required_section_headings`. Length is within the target band. No frontmatter.\n\nAfter writing, exit. The main orchestrator will validate and synthesize.",
    "new_string": "A single Markdown file at `output_path`. Headings are the literal `required_section_headings`. Length is within the target band. No frontmatter.\n\n**Self-validation gate (mandatory before exit).** Re-read the file you just wrote. For each entry in `required_section_headings`, confirm an H2 line exists with EXACT spelling and EXACT capitalization (sentence-case headings like `User stories` must NOT be Title-Cased to `User Stories`). For every mismatch, Edit the heading in place before exiting. Do not exit while a mismatch remains.\n\nAfter the validation gate passes, exit. The main orchestrator will synthesize.",
    "rationale": "Closes F1. Moves patch-1's intent INTO the agent prompt that draft subagents actually read at spawn time. The skill paragraph alone does not bind a subagent — only its prompt does."
  },
  {
    "id": "patch-2-2",
    "severity": "MEDIUM",
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-26-patcher.md",
    "old_string": "## Step 26.2.5 — Escalation re-loop (one bounded pass)\n\nPatcher escalations are NOT closed by step 27 (polish cannot add content). After the patcher subagent returns, the orchestrator inspects `patch-log.json.escalations`. If the array is non-empty:",
    "new_string": "## Step 26.2.5 — Escalation re-loop (one bounded pass)\n\nPatcher escalations are NOT closed by step 27 (polish cannot add content). After the patcher subagent returns, the orchestrator inspects `patch-log.json.escalations`. **Re-loop counter:** read `patch-log.json.reloop_count` (default 0). If `reloop_count >= 1`, DO NOT re-loop — skip directly to the Known gaps appendix path. Before re-spawning, write `reloop_count: 1` to the log so a compaction-resumed run cannot accidentally re-loop again. If the array is non-empty AND reloop_count == 0:",
    "rationale": "Closes F2. Makes the bounded-one-pass guarantee state-machine-safe across compaction by persisting the counter on disk."
  },
  {
    "id": "patch-2-3",
    "severity": "MEDIUM",
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-21-personas-stories.md",
    "old_string": "**Edge-case enumerator (mandatory).** For every capability, generate edge stories from this checklist before stopping. Skip an item only if it is genuinely inapplicable, and record why in `prd/temp/edge-case-coverage.md`:",
    "new_string": "**Edge-case enumerator (tier- and format-aware).** For `standard_prd` and `detailed_prd`, for every capability, generate edge stories from this checklist before stopping. Skip an item only if it is genuinely inapplicable, and record why in `prd/temp/edge-case-coverage.md`. For `one_pager`, generate at most TWO edge stories total across the whole PRD — pick the two highest-impact items from the checklist and note the skipped items in a single line in `edge-case-coverage.md`:",
    "rationale": "Closes F3. Prevents over-generation in one_pager format introduced by patch-8."
  },
  {
    "id": "patch-2-4",
    "severity": "MEDIUM",
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-17-initialize.md",
    "old_string": "### 17.8 — Update the scaffold\n\nAppend a \"Tier rationale\" subsection to `prd/scaffold.md` with a 2-3 sentence justification for the tier classification.",
    "new_string": "### 17.8 — Update the scaffold\n\nAppend a \"Tier rationale\" subsection to `prd/scaffold.md` that QUOTES the `tier_rationale` field from `prd/prd-decomposition.json`. The JSON is canonical; the scaffold mirrors it for human readability. Never edit the scaffold copy independently — if you need to revise the rationale, edit the JSON and re-mirror.",
    "rationale": "Closes F5. Names the JSON as canonical and the scaffold as a mirror, eliminating drift risk from patch-10's double-persistence."
  },
  {
    "id": "patch-2-5",
    "severity": "LOW",
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-27-polish.md",
    "old_string": "Spawns prd-polish-auditor (Read+Edit). Strips any remaining pipeline-vocab leaks",
    "new_string": "Spawns prd-polish-auditor (Read+Edit). **Allowed user-visible product vocabulary (do NOT strip):** `push notification`, `inbox`, `banner`, `toggle`, `dashboard`, `roster`, `screen`. Strips any remaining pipeline-vocab leaks",
    "rationale": "Closes F7. Mirrors patch-4's allow-list into the step-27 skill so the orchestrator sees it without reading the agent file."
  },
  {
    "id": "patch-2-6",
    "severity": "LOW",
    "file": "/home/shivam-pansuriya/Downloads/manageark-main/hyperresearch-fork/src/hyperresearch/skills/hyperresearch-prd-23-triple-draft.md",
    "old_string": "**Tier gate:** Runs for ALL tiers. For `light`: write a single draft directly to `prd/notes/final_prd_<prd_tag>.md` and skip ahead to step 27 (polish). For `full`: run the triple-draft ensemble below — step 24 (synthesizer) will turn the 3 drafts into the final PRD.",
    "new_string": "**Tier gate:** Runs for ALL tiers. For `light`: write a single draft directly to `prd/notes/final_prd_<prd_tag>.md` and skip ahead to step 27 (polish). After writing, verify word count is within ±20% of the target band middle for the prd_format. If under the floor, run ONE expansion pass that adds user stories, acceptance criteria, or edge cases drawn from prior-step artifacts (do not invent); then exit. For `full`: run the triple-draft ensemble below — step 24 (synthesizer) will turn the 3 drafts into the final PRD.",
    "rationale": "Closes F8. Adds a single recovery pass in the light-tier branch so light + standard_prd can meet the floor without invoking the synthesizer."
  }
]
```

---

# Iteration-2 vs iteration-1 comparison

|  | Iter 1 | Iter 2 | Delta |
|---|---|---|---|
| Total findings | 15 | 8 | **−7** |
| HIGH | 3 | 1 (F1, regression) | **−2** |
| MEDIUM | 7 | 4 (F2–F5) | **−3** |
| LOW | 5 | 3 (F6–F8) | **−2** |
| Regressions | n/a | 1 (patch-1 partial) | +1 |
| Patches recommended | 12 | 6 | −6 |

**Net delta:** the pipeline moved from 3 HIGH / 7 MEDIUM / 5 LOW to 1 HIGH / 4 MEDIUM / 3 LOW. Eleven of twelve iter-1 patches landed cleanly. The remaining HIGH is a single regression (patch-1's intent text was added to the skill but not propagated into the agent prompt that the draft subagent actually reads at spawn time). Three of the four iter-2 MEDIUMs are second-order issues created or exposed by the iter-1 patches (re-loop idempotency, edge-case over-generation, tier-rationale double-persistence). None of the iter-2 findings re-flag a closed iter-1 finding.

---

# Summary

**Eval verdict on iteration 2: NOT YET SATISFACTORY.**

The bar is zero HIGH findings. Iteration 2 has **one HIGH (F1)** — patch-1's per-draft heading capitalization gate landed in the step-23 skill but was not propagated into the `prd-draft-orchestrator.md` agent prompt that draft subagents read at spawn time. The skill paragraph is advisory text seen by the orchestrator, not by the subagents that actually write drafts; a draft can still ship "User Stories" (Title Case) and exit cleanly. Patch-2-1 above closes this in one Edit and unblocks ship-readiness.

After patch-2-1 lands, iteration 3 should drop to **0 HIGH / 4 MEDIUM / 3 LOW** and meet the "zero-HIGH" satisfactory bar. The remaining MEDIUMs are quality-of-life: re-loop idempotency for compaction recovery (F2), tier-aware edge-case enumeration (F3), advisory-vs-machine-checkable gates (F4), and tier-rationale single canonical home (F5). LOWs are mirror-the-allow-list / single-flag-validation polish.

**Eleven of twelve iter-1 patches landed cleanly.** The pipeline made real progress: pattern-reuse dual-classing, greenfield invented terms, the synthesizer expand-floor branch, the step-22 cross-check invariant, the bounded re-loop, and the light-tier inclusion of steps 20–21 are all operational. The one partial landing is mechanical and fixable in one patch.

**Recommendation to parent:** apply patch-2-1 (the agent-prompt edit). Then re-run iteration 3 to confirm zero HIGH findings. Patches 2-2 through 2-6 can ship in the same wave or follow iteration 3 — none are blockers.
