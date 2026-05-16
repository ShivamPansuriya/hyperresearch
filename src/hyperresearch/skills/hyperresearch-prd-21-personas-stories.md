---
name: hyperresearch-prd-21-personas-stories
description: >
  Step 21 of the hyperresearch-PRD pipeline. Writes the persona
  descriptions and per-persona user stories that ground the rest of
  the PRD in real user motivation. Full tier only. Produces
  personas.md and user-stories.md.
---

# Step 21 — Personas & user stories

**Tier gate:** Full tier ONLY.

**Goal:** convert the persona-capability matrix from step 19 into prose that the synthesizer subagent can lift directly into the final PRD. Personas get a concrete, named description. Each in-scope capability gets at least one user story per relevant persona.

**Why this step exists:** PRDs that skip explicit persona narratives end up feature-centric instead of user-centric — the dev team builds the screens but the value proposition is muddled. Anchoring every capability to a "as a X I want Y so that Z" line keeps the document honest.

## Recover state

- `prd/feature-decomposition.json` (step 19)
- `prd/product-inventory.json` (step 18)
- `prd/integration-map.json` (step 20)

## Procedure

### 21.1 — Persona profiles

For each persona in `personas_in_scope`, write a short profile (4–8 lines):

```markdown
### <Canonical persona name>

**Context.** <Where this user typically interacts with the product — at home / at school / mobile / desktop / time of day.>

**Goals relevant to this feature.** <2–3 bullets describing what the user is trying to achieve.>

**Pain points the feature addresses.** <2–3 bullets — concrete pains, not vague "wants better UX".>

**Tech proficiency assumption.** <e.g., "Comfortable with mobile apps but not a power user. Likely to use defaults rather than configure preferences.">

**Constraint to respect.** <One sentence about a constraint the design must respect — e.g., for parents: "may speak a different language from the school's official medium; localized strings matter.">
```

If the inventory lists persona variations (e.g., "Class Teacher" vs "Subject Teacher"), choose the variation(s) actually relevant to this feature and use those names exactly.

Write all persona profiles to `prd/personas.md`. Start the file with a one-paragraph intro: "This feature serves the following personas. Profiles below describe each persona's relationship to this feature specifically — not their full role in ManageArk."

### 21.2 — User stories per persona

For each in-scope capability, for each persona with a non-`—` verb in the matrix, write 1–3 user stories. Format:

```markdown
**Story <id>** — <persona> — <capability-id>

> As a <persona>,
> I want to <action in user-visible terms>,
> so that <user-visible outcome>.

**Acceptance signals (user-visible)**
- <observable behavior 1>
- <observable behavior 2>

**Linked entities:** <E1>, <E2>
**Linked flows:** <F1>
```

Rules:
- The "I want to" line must be in user-visible language. Never write "I want the system to update the database" — write "I want to mark a student absent and see the absence reflected immediately on my class list."
- Acceptance signals are what a tester would *see* when the story is delivered. Not test cases; user-visible behavior.
- Stories with multiple personas in the same handoff (e.g., teacher acts, parent receives) should be written as TWO stories (one per persona), not one collapsed story. Cross-link them via "see related story <id>".

### 21.3 — Coverage check

Build a one-line check: every in-scope capability has at least one story. Every persona in scope has at least one story. Write the gap list — if any cell in the matrix has a verb but no story, fix it.

### 21.4 — Edge-case and negative stories

**Edge-case enumerator (tier- and format-aware).** For `standard_prd` and `detailed_prd`, for every capability, generate edge stories from this checklist before stopping. Skip an item only if it is genuinely inapplicable, and record why in `prd/temp/edge-case-coverage.md`. For `one_pager`, generate at most TWO edge stories total across the whole PRD — pick the two highest-impact items from the checklist and note the skipped items in a single line in `edge-case-coverage.md`:

1. Opt-in-off then triggering event.
2. Network drop during user action.
3. Same triggering event occurs N times in quick succession.
4. The triggering event is undone / rescinded after the alert went out.
5. The actor's locale is the non-default language.
6. The actor is on a device-class with no push capability.
7. The feature is globally disabled (admin kill switch) at the moment of the event.

For each in-scope capability, ask: what's the most likely user-visible failure mode? Write at least one "negative" story per capability:

```markdown
**Story <id>-neg** — <persona> — <capability-id> — edge case

> As a <persona>,
> when <unhappy-path trigger>,
> I expect <user-visible behavior>.

**Examples:**
- A parent who has not yet opted in to attendance alerts opens the app the day after an absence. Expectation: the alert appears in the inbox (so they don't miss anything), with a "you missed N alerts while opt-in was off" banner suggesting they enable alerts.
- A teacher marks attendance after a network drop. Expectation: a clear "saved offline — will sync" indicator; once back online, the absence-trigger alerts go out as if marked at the original time.
```

### 21.5 — Write `prd/user-stories.md`

Structure:

```markdown
# User stories

## By persona

### <Persona 1>
<stories>

### <Persona 2>
<stories>

## Edge-case / negative stories
<stories>

## Story → capability coverage map

| Capability | Stories |
|---|---|
| C1 | S1.1, S1.2, S1-neg |
| C2 | S2.1 |
```

## Exit criterion

- `prd/personas.md` exists with one profile per in-scope persona.
- `prd/user-stories.md` exists with at least one positive story per (capability × involved persona) cell and at least one negative story per capability.
- The coverage map at the bottom shows zero empty rows.

## Next step

Return to the entry skill. Invoke step 22:

```
Skill(skill: "hyperresearch-prd-22-flows-entities")
```
