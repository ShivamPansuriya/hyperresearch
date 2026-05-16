---
name: hyperresearch-prd-28-readability-audit
description: >
  Step 28 (final) of the hyperresearch-PRD pipeline. Spawns the
  prd-readability-recommender subagent (Read+Write tool-locked) to
  audit the polished PRD and write JSON recommendations for paragraph
  merges, breaks, list/table conversions, bold injection, sentence
  splits, and HR removal. The orchestrator reads the recommendations
  and SELECTIVELY applies them via direct Edit calls (the recommender
  does NOT modify the PRD itself). Logs orchestrator decisions to a
  separate file. Runs for ALL tiers. Final step.
---

# Step 28 — Readability audit & selective apply (FINAL STEP)

**Tier gate:** Runs for ALL tiers.

**Goal:** the PRD is now substantively correct and hygienic. This pass improves visual structure and scannability: paragraph rhythm, lists where prose would be a slog, tables where comparison is useful, bold for key terms, no unnecessary horizontal rules, sentence splits where over-long.

**Why this step exists:** PRDs that ship as wall-of-text are skimmed and misread by stakeholders. Selective readability improvements raise the chance that the dev team, leadership, and other PMs actually consume the document.

## Recover state

- `prd/notes/final_prd_<prd_tag>.md` exists.
- `prd/polish-log.json` exists.

## Step 28.1 — Spawn the prd-readability-recommender

Single spawn. Tool-locked to `[Read, Write]`. Note this is different from polish/patcher — the recommender WRITES a recommendations file but cannot Edit the PRD. The orchestrator applies edits selectively.

**Spawn template:**
```
subagent_type: prd-readability-recommender
prompt: |
  FEATURE REQUEST (verbatim, gospel):
  > {{paste prd/request-<prd_tag>.md body}}

  REQUEST FILE: prd/request-<prd_tag>.md

  PIPELINE POSITION: You are step 28 of the hyperresearch-PRD
  pipeline — the final analytical pass. The PRD at draft_path has
  been drafted (step 23 or 24), critiqued (step 25, full tier),
  patched (step 26, full tier), and polish-audited (step 27). Your
  job: write JSON recommendations for paragraph rhythm, list/table
  conversions, bold key terms, sentence splits, and other structural
  readability improvements. You are tool-locked to [Read, Write] —
  you cannot Edit the report. The orchestrator reads your
  recommendations and decides which to apply.

  YOUR INPUTS:
  - draft_path: prd/notes/final_prd_<prd_tag>.md
  - recommendations_path: prd/readability-recommendations.json
  - prd_format: "<from decomposition>"

  Write recommendations as a JSON array per the schema:
  {
    "recommendations": [
      {
        "id": "R1",
        "kind": "merge-paragraphs | break-paragraph | make-list | make-table | bold-keyterms | split-sentence | remove-hr | add-whitespace",
        "anchor": "<exact short quote identifying location>",
        "before_excerpt": "<the existing text>",
        "after_excerpt": "<the proposed text>",
        "severity": "high | medium | low",
        "rationale": "<one sentence>",
        "category": "<copy of kind for sorting>"
      }
    ]
  }

  Cap at 50 recommendations. Prioritize by impact: long unbroken
  paragraphs first; comparison-prose-that-should-be-a-table second;
  acceptance-criteria-prose-that-should-be-a-list third; bold key
  terms only where it clarifies scanning. Avoid recommending bold
  on every other sentence (cognitive noise).
```

## Step 28.2 — Read the recommendations

After the recommender returns, read `prd/readability-recommendations.json`.

## Step 28.3 — Decide which to apply

For each recommendation, decide: apply / defer / dismiss. Decision heuristics:

- **Apply automatically (severity high):**
  - `make-list` when the existing prose contains ≥4 comma-or-semicolon-joined items.
  - `make-table` when the prose compares ≥3 entities across ≥2 attributes.
  - `split-sentence` when the sentence is >40 words AND contains 2+ independent clauses.
  - `break-paragraph` when the paragraph is >180 words.
  - `remove-hr` when the document has more than one HR and removing makes no information loss.

- **Apply with judgment (severity medium):**
  - `merge-paragraphs` when two adjacent paragraphs total ≤120 words and discuss the same idea. SKIP if they discuss different ideas.
  - `bold-keyterms` when the term is a defined entity name, persona name, or success-metric name on first prominent mention. SKIP if already bolded nearby.
  - `add-whitespace` between two visually crammed sections.

- **Defer (severity low):**
  - Stylistic micro-edits ("change semicolon to period", "title-case this header") that the polish step should have caught.
  - Bolding on minor words.

- **Dismiss:**
  - Recommendations that would re-introduce architecture vocabulary, pipeline vocabulary, or scaffold leaks.
  - Recommendations that would alter the required section headings.
  - Recommendations that would shrink the PRD below its `prd_format` minimum word count.

Avoid applying more than 25 changes total even if all 50 are good — the document needs to remain stable.

## Step 28.4 — Apply chosen recommendations via Edit

For each recommendation tagged "apply":

1. Use the Edit tool directly. The recommender already provided `before_excerpt` and `after_excerpt`; if these are precise, an Edit replacement is straightforward.
2. For `make-list` / `make-table`: the recommender's `after_excerpt` may be a sketch — refine it in line with the rest of the document's voice before applying.
3. Apply one Edit per recommendation. Do NOT batch unrelated changes into one Edit.

## Step 28.5 — Log decisions

Write `prd/readability-decisions.json`:

```json
{
  "decisions": [
    {"id": "R1", "decision": "apply | defer | dismiss", "rationale": "<one sentence>"},
    ...
  ],
  "applied_count": N,
  "deferred_count": M,
  "dismissed_count": K
}
```

## Exit criterion

- `prd/readability-recommendations.json` exists.
- `prd/readability-decisions.json` exists.
- All apply-tagged recommendations have been edited into the PRD.
- The PRD still passes: required headings in order, no architecture vocabulary, no pipeline vocabulary, no YAML frontmatter.

## Pipeline complete

The PRD pipeline is now finished. Final artifact: `prd/notes/final_prd_<prd_tag>.md`.

Print a short closing summary (≤15 lines) listing:
- `prd_tag`
- `pipeline_tier`
- `prd_format`
- Final word count
- Final file path
- Total recommendations applied / deferred / dismissed
- Any escalations or warnings the pipeline flagged for human attention

Then stop. The PRD is ready for the development team.
