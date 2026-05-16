---
name: hyperresearch-prd-26-patcher
description: >
  Step 26 of the hyperresearch-PRD pipeline. Spawns the prd-patcher
  subagent (TOOL-LOCKED to Read + Edit) to apply patch-doable critic
  findings as surgical Edit hunks against the synthesized PRD. Zero
  regeneration. Pre-stubs the patch log because Edit cannot create
  files. Handles orchestrator-escalated structural restructures inline.
  Full tier only.
---

# Step 26 — PRD patcher

**Tier gate:** Full tier ONLY.

**Goal:** apply the patch-doable findings from step 25 as small Edit hunks. The patcher cannot Write a new file — only Edit the existing PRD. Structural findings come back to the orchestrator (you) for hand-written Edits.

**Why this step exists:** if the synthesizer had been allowed to "fix everything" via re-write, voice and structure would drift on every pass. Tool-locking the patcher to Read+Edit enforces surgical changes.

## Recover state

- `prd/notes/final_prd_<prd_tag>.md` exists.
- All 4 critic findings JSONs exist.
- `prd/temp/critic-triage.md` exists.

## Step 26.1 — Pre-create the patch log stub

The patcher has `[Read, Edit]` only and cannot create a new file. Stub it first:

```bash
echo '{"applied": [], "escalations": [], "dismissed": []}' > prd/patch-log.json
```

## Step 26.2 — Spawn the prd-patcher

Single spawn. Tool-locked.

**Spawn template:**
```
subagent_type: prd-patcher
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  REQUEST FILE: prd/request-<prd_tag>.md

  PIPELINE POSITION: You are step 26 (patcher) of the hyperresearch-PRD
  pipeline. Step 25's 4 critics produced findings JSONs. After you
  apply patch-doable findings as Edit hunks, step 27 (polish auditor)
  runs the final hygiene pass. You are TOOL-LOCKED to [Read, Edit].

  YOUR INPUTS:
  - draft_path: prd/notes/final_prd_<prd_tag>.md
  - critic_findings_paths: [
      "prd/prd-critic-findings-business-value.json",
      "prd/prd-critic-findings-scope-creep.json",
      "prd/prd-critic-findings-integration-feasibility.json",
      "prd/prd-critic-findings-instruction.json"
    ]
  - triage_path: prd/temp/critic-triage.md
  - patch_log_path: prd/patch-log.json   (already stubbed)
  - feature_decomposition_path: prd/feature-decomposition.json
  - product_inventory_path: prd/product-inventory.json

  Procedure:
  1. Read draft_path, all critic findings, and the triage.
  2. For each finding tagged "patch-doable":
     - Locate the anchor in the PRD.
     - Apply a SURGICAL Edit hunk. Hunks must be ≤200 chars of changed
       text per hunk. Multiple small hunks beat one big hunk.
     - For severity high findings: hunks may grow to ≤500 chars if
       absolutely necessary, but escalate if even that is insufficient.
     - Append the applied hunk record to patch_log_path via Edit
       (open the JSON file, find the empty "applied": [] array, insert
       a record). Record: {"finding_id": "...", "severity": "...",
       "anchor": "...", "before": "...", "after": "...", "rationale": "..."}.
  3. For each finding tagged "structural" or any finding whose
     required edit exceeds the size cap: do NOT apply. Append to the
     "escalations": [] array in patch_log_path:
     {"finding_id": "...", "reason": "...", "needs_orchestrator": true}.
  4. For each finding tagged "dismiss" by the triage: append to
     "dismissed": [] array with the dismissal rationale.

  STRICT RULES:
  - You can only Read and Edit. No Write, no Bash, no Task.
  - Do NOT rewrite whole sections. If a finding requires that, escalate.
  - Do NOT introduce new capabilities, personas, or entities even if a
    critic implies them. Stay within feature-decomposition.in_scope.
  - Keep the required section headings exactly as they are.
  - Keep the PRD free of architecture vocabulary and pipeline vocabulary.
```

## Step 26.2.5 — Escalation re-loop (one bounded pass)

Patcher escalations are NOT closed by step 27 (polish cannot add content). After the patcher subagent returns, the orchestrator inspects `patch-log.json.escalations`. **Re-loop counter:** read `patch-log.json.reloop_count` (default 0). If `reloop_count >= 1`, DO NOT re-loop — skip directly to the Known gaps appendix path. Before re-spawning, write `reloop_count: 1` to the log so a compaction-resumed run cannot accidentally re-loop again. If the array is non-empty AND reloop_count == 0:

1. Re-spawn step 24's synthesizer ONCE with the escalation list appended to its inputs and a directive: "Apply the missing content named in these escalations. Use existing prior-step artifacts (personas, user-stories, flows, entities, integration-map) as your only sources — do not invent."
2. Re-spawn step 25's critics ONCE.
3. Re-spawn the patcher ONCE.

If, after this single re-loop, escalations remain open, ship with a `## Known gaps` appendix in the final PRD listing each unresolved escalation and the reason it remained unresolved. Do NOT extend the loop further — escalations that survive one synthesis re-pass indicate a genuine product-decision gap and need PM input, not more pipeline iteration.

## Step 26.3 — Handle escalations

After the patcher returns, read `prd/patch-log.json` → `escalations`. For each escalation:

1. **Restructure findings** (e.g., "section X needs reordering" or "section Y is missing"): you (the orchestrator) read the relevant finding and craft a hand-written Edit. Keep it surgical. Do NOT rewrite the section from scratch — restructure existing content. If you genuinely need new content, pull it verbatim from prior-step artifacts (personas.md, user-stories.md, flows.md, entities.md) — never invent.

2. **Wrong-format findings** (e.g., "wrong length", "missing required heading"): apply directly via Edit. If a required heading is missing, insert it at the correct position with content pulled from the appropriate prior-step artifact.

3. **Architecture-leak escalations**: rewrite the leak in user-visible terms. If you can't translate, delete the offending sentence.

Log every orchestrator-applied edit to `prd/patch-log.json` → `applied` with `applied_by: "orchestrator"`.

## Step 26.4 — Net length check

Patcher and orchestrator should produce roughly net-zero or slightly-negative net char delta. If the patch log shows a large positive delta, the patcher may have started rewriting. Re-read the changes; revert any that exceed the size cap and re-escalate.

## Exit criterion

- `prd/patch-log.json` exists and is non-empty (some applied/escalations/dismissed records).
- No critic finding is in "patch-doable" state without being either applied or escalated.
- All escalations have been resolved (orchestrator-edited or explicitly dismissed with rationale).

## Next step

Return to the entry skill. Invoke step 27:

```
Skill(skill: "hyperresearch-prd-27-polish")
```
