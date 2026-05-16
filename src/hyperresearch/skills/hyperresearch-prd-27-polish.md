---
name: hyperresearch-prd-27-polish
description: >
  Step 27 of the hyperresearch-PRD pipeline. Spawns the prd-polish-auditor
  subagent (TOOL-LOCKED to Read + Edit) for the final hygiene + readability
  pass. Strips pipeline-reference leaks, YAML frontmatter, scaffold
  references, architecture vocabulary remnants, filler phrases, run-on
  sentences. Escalates structural mismatches rather than fabricating
  content. Runs for ALL tiers. Followed by step 28 (readability audit).
---

# Step 27 — Polish audit

**Tier gate:** Runs for ALL tiers.

**Goal:** the PRD is now substantively correct. This pass enforces hygiene: no pipeline vocabulary, no architecture words, no filler, no run-on sentences, no scaffold-leak. The polish auditor is the last line of defense before the readability pass.

## Recover state

- `prd/notes/final_prd_<prd_tag>.md` exists (from step 24 for full tier, or step 23 for light tier).
- Light tier: no patch log expected. Full tier: `prd/patch-log.json` exists.

## Step 27.1 — Pre-create the polish log stub

The polish auditor has `[Read, Edit]` only and cannot create a new file. Stub it first:

```bash
echo '{"applied": [], "escalations": []}' > prd/polish-log.json
```

## Step 27.2 — Spawn the prd-polish-auditor

Single spawn.

**Spawn template:**
```
subagent_type: prd-polish-auditor
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  REQUEST FILE: prd/request-<prd_tag>.md

  PIPELINE POSITION: You are step 27 (polish auditor) of the
  hyperresearch-PRD pipeline. Step 26 (patcher) applied critic
  findings as Edit hunks (full tier) or step 23 wrote the draft
  directly (light tier). After you return, step 28 (readability
  audit) runs a final formatting pass. You are TOOL-LOCKED to
  [Read, Edit].

  YOUR INPUTS:
  - draft_path: prd/notes/final_prd_<prd_tag>.md
  - polish_log_path: prd/polish-log.json   (already stubbed)
  - prd_decomposition_path: prd/prd-decomposition.json
  - required_section_headings: [<from decomposition>]
  - prd_format: "<from decomposition>"
```

**Allowed user-visible product vocabulary (do NOT strip these even though they look architectural):** `push notification`, `inbox`, `banner`, `toggle`, `dashboard`, `roster`, `screen`. These are the words users see in the product UI.

The polish auditor strips:

- **Pipeline reference leaks** — any mention of `hyperresearch`, `prd-decomposition`, `scaffold`, `coverage matrix`, `atomic items`, `synthesis plan`, `integration map`, `feature-decomposition`, `product-inventory`, `draft a/b/c`, `triple draft`, `critic findings`, `patch log`, `polish log`.
- **YAML frontmatter** at the top of the PRD (the final PRD has no frontmatter).
- **Architecture vocabulary** that survived earlier passes: `API`, `endpoint`, `database`, `schema`, `table`, `column`, `foreign key`, `queue`, `cache`, `microservice`, `service layer`, `pub/sub`, `JSONB`, `VARCHAR`, `INT`, `NULL`, `p99`, `p95`, `QPS`, `SLA`, `K8s`, names of programming languages, frameworks, libraries.
- **Filler phrases** — "It is worth noting", "Importantly", "Notably", "Furthermore", "Additionally", "It should be mentioned", "As we all know".
- **Hedge words** — "may potentially", "could possibly", "might perhaps", "in some cases possibly".
- **Redundant sentences** that restate prior content.
- **Run-on sentences** (>40 words without a clause break) — break into two via Edit.
- **Pre-existing engineering speak** the synthesizer may have leaked: "the system queries...", "the backend handles...", "the API returns...". Rewrite as user-visible: "the user sees..."

The polish auditor PRESERVES:
- The literal required section headings, in order, in their exact spelling.
- Quoted user voices / personas described as themselves.
- Any explicit user-visible latency claim ("appears within 2 minutes") — that's a user expectation, not an SLA.

## Step 27.3 — Handle escalations

The polish auditor ESCALATES structural mismatches (wrong format for the request, missing required sections, etc.) rather than fabricating content. Read escalations in the polish log.

If an escalation names a structural issue (e.g., "user asked for an explicit acceptance criteria list; PRD has acceptance in prose"), you have one shot to fix it — craft a hand-written Edit, then continue.

**Sanity-check net length.** Polish should have NEGATIVE net char delta. If the polish log shows positive net chars added, something went wrong — polish is for cutting, not expanding.

**Do not apply polish edits yourself in 27.2.** The polish auditor's tool lock is the mechanism. Calling Edit directly bypasses the hygiene-check logic baked into the auditor's prompt. If the auditor returned empty edits, re-spawn it; don't do the work yourself unless 27.3 escalations require it.

## Step 27.4 — Final integrity gate

Before declaring step 27 complete, verify every expected artifact exists. The required set depends on the tier:

- **light tier:** only `prd/polish-log.json` is required (steps 24–26 are skipped, so no critic findings or patch log).
- **full tier:** require all four critic findings + patch-log + polish-log:

```bash
for f in prd/prd-critic-findings-business-value.json \
         prd/prd-critic-findings-scope-creep.json \
         prd/prd-critic-findings-integration-feasibility.json \
         prd/prd-critic-findings-instruction.json \
         prd/patch-log.json \
         prd/polish-log.json; do
  test -f "$f" || echo "MISSING: $f"
done
```

If any artifact is missing, the responsible step failed silently. Re-spawn the responsible agent ONCE with the missing output path as its explicit required output. If it fails a second time, write a minimal stub (`{"findings":[]}` for critic files, canonical empty-log schema for patch-log.json / polish-log.json) and log the failure before proceeding.

## Exit criterion

- `prd/polish-log.json` exists, has applied edits (or escalation records).
- Architecture-vocabulary grep on `prd/notes/final_prd_<prd_tag>.md` returns ZERO hits.
- Pipeline-vocabulary grep returns ZERO hits.
- No YAML frontmatter at the top of the PRD.
- Required section headings present in order.

## Next step

Return to the entry skill. Invoke step 28:

```
Skill(skill: "hyperresearch-prd-28-readability-audit")
```
