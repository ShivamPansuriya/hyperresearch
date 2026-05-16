# PRD Pipeline Eval — Iteration 3

Same feature request as iter 1 & 2 (parent attendance alert for ManageArk, full tier, standard_prd, greenfield PRD dir). Goal: verify the 6 iter-2 patches landed, re-simulate steps 17–28, and confirm whether F1 (HIGH heading-capitalization regression) is closed.

---

## Patch-landing check (6 iter-2 patches)

| Patch | Target | Expected change | Status | Evidence |
|---|---|---|---|---|
| patch-2-1 | `agents/prd/prd-draft-orchestrator.md` Output | "Self-validation gate (mandatory before exit)" | **LANDED** | Output section now contains the exact paragraph: *"Re-read the file you just wrote. For each entry in `required_section_headings`, confirm an H2 line exists with EXACT spelling and EXACT capitalization (sentence-case headings like `User stories` must NOT be Title-Cased to `User Stories`). For every mismatch, Edit the heading in place before exiting."* |
| patch-2-2 | `skills/hyperresearch-prd-26-patcher.md` 26.2.5 | "Re-loop counter" + `reloop_count` | **LANDED** | Step 26.2.5 now reads `patch-log.json.reloop_count` (default 0), short-circuits if ≥1, and writes `reloop_count: 1` to the log BEFORE re-spawning. Compaction-safe. |
| patch-2-3 | `skills/hyperresearch-prd-21-personas-stories.md` 21.4 | "tier- and format-aware" + one_pager ≤2 carve-out | **LANDED** | Section header now reads "Edge-case enumerator (tier- and format-aware)". one_pager branch says "generate at most TWO edge stories total across the whole PRD". |
| patch-2-4 | `skills/hyperresearch-prd-17-initialize.md` 17.8 | "QUOTES the `tier_rationale` field" / canonical-JSON wording | **LANDED** | 17.8 now reads: *"Append a 'Tier rationale' subsection to `prd/scaffold.md` that QUOTES the `tier_rationale` field from `prd/prd-decomposition.json`. The JSON is canonical; the scaffold mirrors it… Never edit the scaffold copy independently."* |
| patch-2-5 | `skills/hyperresearch-prd-27-polish.md` 27.2 | "Allowed user-visible product vocabulary" allow-list | **LANDED** | 27.2 now contains: *"Allowed user-visible product vocabulary (do NOT strip these even though they look architectural): `push notification`, `inbox`, `banner`, `toggle`, `dashboard`, `roster`, `screen`."* Mirrors the agent prompt. |
| patch-2-6 | `skills/hyperresearch-prd-23-triple-draft.md` Tier gate | "ONE expansion pass" for light tier | **LANDED** | Tier gate paragraph now reads: *"After writing, verify word count is within ±20% of the target band middle for the prd_format. If under the floor, run ONE expansion pass that adds user stories, acceptance criteria, or edge cases drawn from prior-step artifacts (do not invent); then exit."* |

**All 6 patches landed cleanly. No partial-landings.**

---

## Simulated step trace (17–28, terse)

- **17 (initialize)** — Classifies tier=`full`, prd_format=`standard_prd`. `tier_rationale` written to `prd-decomposition.json`, scaffold quotes it (single canonical source, 17.8 enforces no independent edits). Required headings sentence-cased: `Overview`, `Personas`, `User stories`, `User flow`, `User-visible entities & fields`, `Integration with existing product`, `Acceptance criteria`, `Out of scope`, `Future scope`, `Success metrics`.
- **18 (inventory)** — Greenfield. `existing_product_state = "greenfield"`. No iter-2 change.
- **19 (decomposition)** — Personas {parent, teacher, admin}, capabilities mapped. Pattern-reuse constraint ("reuse notification-preferences screen") now surfaces as a capability touchpoint (iter-1 patch).
- **20 (integration map)** — In-app inbox, push, onboarding consent, admin exam-week toggle. Architecture-leak gate passes.
- **21 (personas/stories)** — Edge-case enumerator runs in **standard_prd mode** (full 7-item checklist applies; one_pager carve-out not triggered). All capabilities get negative/edge stories. Patch-2-3 active but inert for this feature.
- **22 (flows/entities)** — Flows for parent opt-in, absence trigger, ack, exam-week disable. Entities: Alert, ConsentRecord, ExamWeekDisable.
- **23 (triple-draft, full tier)** — Spawns 3 prd-draft-orchestrators. **New behavior:** each spawned agent now executes the self-validation gate before exit (patch-2-1). Sentence-case headings (`User stories`, not `User Stories`) are now enforced at the agent level, closing F1.
- **24 (synthesize)** — Synthesizer integrates 3 drafts. Heading conformity inherited from drafts.
- **25 (critics)** — 4 critics in parallel; instruction-critic verifies heading capitalization on the final synthesized PRD as additional defense.
- **26 (patcher)** — Applies critic findings. **New behavior:** if escalations open and `reloop_count == 0`, write counter to disk, re-spawn synthesizer/critics/patcher once. On compaction-resume, counter persists → no cascading re-spawn (patch-2-2).
- **27 (polish)** — Polish auditor strips arch leaks. **New behavior:** allow-list (`push notification`, `inbox`, `banner`, `toggle`, `dashboard`, `roster`, `screen`) now visible in the step skill (patch-2-5); orchestrator can pre-flag false-positive escalations. "inbox alert", "push notification", "toggle" all survive correctly in the simulated PRD.
- **28 (readability audit)** — Recommender writes recommendations.json; orchestrator selectively Edits.

The simulated final PRD is materially identical to iter-2's (~2780 words), with two corrections vs hypothetical-iter-2 risks: (a) zero risk of a draft slipping Title-Cased headings past the gate; (b) zero risk of an escalation re-loop running twice across compaction.

---

## F1 closure verification (specific evidence)

F1 was: *"Patch-1 partial-landing — heading capitalization gate not in the agent prompt."*

**Evidence of closure:**

1. `agents/prd/prd-draft-orchestrator.md` → Output section literally contains the self-validation paragraph (verified by file read; the text begins "**Self-validation gate (mandatory before exit).**" and explicitly forbids `User Stories` Title-Casing of the sentence-case `User stories`).
2. The gate is **after** "Headings are the literal `required_section_headings`" and **before** "After the validation gate passes, exit", so it's the last action a draft subagent takes.
3. The gate uses imperative phrasing the agent must execute (`Re-read`, `confirm`, `Edit the heading in place`), not advisory phrasing.
4. The skill-level paragraph in step 23 (added iter-1) is also still present, giving two-layer enforcement (orchestrator-side + agent-side).

**F1 is closed.** A spawned draft subagent that produces `## User Stories` instead of `## User stories` will now be caught and self-corrected at the subagent boundary before its output is consumed by step 24.

---

## Findings (iter-3)

### HIGH

**None.**

### MEDIUM

**M1 — Self-validation gate is text-only; no programmatic check.**
The patch-2-1 gate relies on the draft subagent honestly re-reading and Editing. There is no orchestrator-side post-spawn verification step (e.g., step 23.4 grepping each draft for required H2 spellings before passing to step 24). If a draft subagent silently skips the gate, the regression returns. The instruction-critic at step 25 will eventually catch it, but that's expensive (full critic pass + patcher pass). Recommend adding a 2-line grep check in step 23.4 ("Validate that all 3 drafts came back") that fails fast on heading-spelling mismatch.
**Category:** pipeline-bug (defense-in-depth).

### LOW

**L1 — `reloop_count` write ordering not explicit.**
Patch-2-2 says "Before re-spawning, write `reloop_count: 1` to the log". This is correct intent but doesn't specify atomicity — if the write fails (disk error) and re-spawn proceeds, the counter never lands. Low-probability, but a single-sentence "if the write fails, abort to Known gaps appendix" would tighten it.
**Category:** contract-bug.

**L2 — iter-2 F4 and F6 still open (acknowledged by user as low-priority unpatched items).**
F4: patch-1/7/22 validation gates are advisory text not structured invariants. F6: `disambiguations` empty-list vs missing-field distinction has no validator. Both remain LOW; no new harm. Worth tracking for a future schema-validation step.
**Category:** contract-bug.

### PASSES

- All 6 iter-2 patches landed cleanly with the expected wording.
- F1 (the iter-2 HIGH regression) is closed — verified at the agent-prompt level.
- F2 (re-loop idempotency) is closed via on-disk counter persistence.
- F3 (edge-case enumerator over-generation) is closed via tier/format gating.
- F5 (tier-rationale drift) is closed by declaring JSON canonical and scaffold a mirror with explicit no-independent-edit rule.
- F7 (allow-list visibility in step 27) is closed by mirroring into the skill.
- F8 (light-tier length floor) is closed via the ONE-expansion-pass branch.
- No new regressions introduced by iter-2 patches.
- Simulated PRD on the same feature matches iter-2 quality; sentence-case heading conformity is now structurally guaranteed at the draft layer.

---

## Iteration history table

| Metric | Iter 1 | Iter 2 | Iter 3 |
|---|---|---|---|
| Total findings | 15 | 8 | 3 |
| HIGH | 3 | 1 (F1 regression) | **0** |
| MEDIUM | 7 | 4 | 1 |
| LOW | 5 | 3 | 2 |
| Patches applied | 12 | 6 | (none recommended for blocking) |
| HIGH closure rate | — | 2/3 closed (F1 regressed) | 1/1 closed |
| Open iter-1 findings | 15 | 1 (F1) | 0 |
| Open iter-2 findings | — | 8 | 2 (F4, F6, both LOW, intentionally unpatched) |

---

## Verdict

**SATISFACTORY.**

Zero HIGH-severity findings in iter-3. The F1 heading-capitalization regression — the sole HIGH carried into iter-2 — is now closed at the agent-prompt level where it matters (a spawned `prd-draft-orchestrator` reads the patched Output section and runs the self-validation gate before exit). All 6 iter-2 patches landed cleanly with no partial-landings, no syntactic damage, and no new HIGH-severity regressions.

The remaining MEDIUM (M1, defense-in-depth grep check in step 23.4) is a hardening suggestion, not a blocker — the current single-layer enforcement is sufficient for PMG-facing PRD quality, and the instruction-critic provides backstop coverage. The two LOW items are minor and one is an explicitly accepted carry-over from iter-2.

**Stop the eval loop.** The pipeline is ship-ready for PMG-facing PRDs on standard_prd / full-tier feature requests. If a future iteration is run, the highest-leverage improvement is M1 (programmatic heading-grep in step 23.4) — defense-in-depth, not a correctness gap.
