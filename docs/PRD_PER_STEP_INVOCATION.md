# Per-step invocation reference

Just like the research pipeline's 16 steps, every PRD step is an independently invokable Claude Code skill. After `hyperresearch prd-install`, you can run any step in isolation — either as a slash command or via the `Skill` tool.

## Two equivalent invocation forms

### A. Slash command (preferred for manual reruns)

```
/hyperresearch-prd                              ← entry router (bootstraps + chains all steps)
/hyperresearch-prd-17-initialize
/hyperresearch-prd-18-product-inventory
/hyperresearch-prd-19-feature-decomposition
/hyperresearch-prd-20-integration-map
/hyperresearch-prd-21-personas-stories
/hyperresearch-prd-22-flows-entities
/hyperresearch-prd-23-triple-draft
/hyperresearch-prd-24-synthesize
/hyperresearch-prd-25-critics
/hyperresearch-prd-26-patcher
/hyperresearch-prd-27-polish
/hyperresearch-prd-28-readability-audit
```

Each is a real, registered Claude Code skill. Typing `/` in a Claude Code session lists them all alongside the research pipeline's `/hyperresearch-1-decompose`, `/hyperresearch-2-width-sweep`, etc.

### B. Skill tool (for chaining from inside a session)

```
Skill(skill: "hyperresearch-prd-17-initialize")
Skill(skill: "hyperresearch-prd-23-triple-draft")
Skill(skill: "hyperresearch-prd-28-readability-audit")
```

This is the form the entry router uses internally. You can use it too, when you want to drive the pipeline yourself.

## When you'd run a single step

| Scenario | Step to invoke |
|---|---|
| Reclassify tier after editing the feature request | `/hyperresearch-prd-17-initialize` |
| Re-scan the PRD directory after adding a new PRD to it | `/hyperresearch-prd-18-product-inventory` |
| Adjust scope envelope by hand-editing `feature-decomposition.json`, then refresh | `/hyperresearch-prd-19-feature-decomposition` |
| Add a new persona's stories without re-running the whole pipeline | `/hyperresearch-prd-21-personas-stories` |
| Re-do the 3-draft fan-out with a different angle assignment (edit `prd/temp/angle-assignment.md` first) | `/hyperresearch-prd-23-triple-draft` |
| Re-synthesize after editing `prd/temp/synthesis-plan.md` | `/hyperresearch-prd-24-synthesize` |
| Re-run a specific critic in isolation | (see "running one critic only" below) |
| Apply patcher-only after manually writing critic findings | `/hyperresearch-prd-26-patcher` |
| Final polish + readability without rerunning anything substantive | `/hyperresearch-prd-27-polish` then `/hyperresearch-prd-28-readability-audit` |

## Recovery contract (cold-entry)

Each step skill's `Recover state` section names the input artifacts the step needs. Before invoking a step in isolation, confirm those files exist on disk:

| Step | Required inputs |
|---|---|
| 17 | `prd/request-<prd_tag>.md`, `prd/scaffold.md`, research final report |
| 18 | `prd/prd-decomposition.json`, `prd/scaffold.md` |
| 19 | `prd/prd-decomposition.json`, `prd/product-inventory.json`, `prd/request-<prd_tag>.md` |
| 20 | `prd/feature-decomposition.json`, `prd/product-inventory.json` |
| 21 | `prd/feature-decomposition.json`, `prd/product-inventory.json`, `prd/integration-map.json` |
| 22 | `prd/feature-decomposition.json`, `prd/integration-map.json`, `prd/user-stories.md`, `prd/product-inventory.json` |
| 23 | All upstream (17–22 for full, 17–19 for light) |
| 24 | `prd/temp/draft-{a,b,c}.md` + all upstream |
| 25 | `prd/notes/final_prd_<prd_tag>.md` + all upstream |
| 26 | The 4 critic-findings JSONs + `prd/temp/critic-triage.md` |
| 27 | `prd/notes/final_prd_<prd_tag>.md` (+ patch-log for full tier) |
| 28 | `prd/notes/final_prd_<prd_tag>.md`, `prd/polish-log.json` |

If an input is missing, the step exits with a clear "MISSING: <path>" message. Run the responsible prior step first.

## Running one critic only (step 25 subset)

Step 25 spawns four critics in parallel. If you only want to re-run, say, the instruction critic after editing the PRD:

1. Manually re-spawn the `prd-instruction-critic` subagent via Claude Code's Task interface, using the spawn template documented in `hyperresearch-prd-25-critics.md` step 25.1.
2. Update `prd/temp/critic-triage.md` for the new findings.
3. Invoke `/hyperresearch-prd-26-patcher` to apply.

This is the same per-critic re-spawn flow the research pipeline supports for its 4 critics.

## Resuming after compaction

If your Claude Code session context was compacted mid-run and you're unsure where you are:

1. Open `prd/` and find the highest-numbered artifact present (see the recovery table in `hyperresearch-prd.md` — the entry router).
2. Invoke the NEXT step's skill.
3. The chain resumes.

The orchestrator's TodoWrite list (seeded by the entry router during bootstrap) also survives compaction and shows the integer step numbers — another recovery anchor.

## Parity with the research pipeline

This matches the research pipeline exactly. The 16 research steps are individually invokable as `/hyperresearch-1-decompose` … `/hyperresearch-16-readability-audit`; the 12 PRD steps are individually invokable as `/hyperresearch-prd-17-initialize` … `/hyperresearch-prd-28-readability-audit`. Both pipelines use the same skill-chain mechanic, the same recovery contract, the same artifact-on-disk hand-off model.
