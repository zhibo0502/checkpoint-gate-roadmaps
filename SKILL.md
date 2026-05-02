---
name: checkpoint-gate-roadmaps
description: Use when a roadmap, staged delivery plan, rollout plan, or integration sequence needs scriptable checkpoints with gate-based auto-advance, explicit NEXT semantics, and evidence-backed status reporting.
---

# Checkpoint Gate Roadmaps

## When to Use

Use this skill when a multi-step roadmap should advance only after the current checkpoint passes its gate.

- User asks to "set checkpoints", "auto-advance", "audit roadmap progress", or "make this plan self-checking"
- Roadmap has ordered milestones (`MVP1..MVP10`, `Phase 1..4`, `Slice 1..5`)
- Dirty worktrees, missing doc markers, missing commits, or failed verification must block progression
- The roadmap mixes documentation and code changes, so progress must be grounded in both

Do not use for one-off todo lists without durable audit semantics.

## Core Contract

For each checkpoint, define:

- `key`: stable identifier (`MVP4`, `SLICE2`)
- `name`: short human label
- `done_evidence`: proof that work landed
- `gate`: conditions required before auto-advance

Output fields:

- `status`: `complete` | `in_progress` | `pending`
- `advance_ready`: `yes` | `no`
- `evidence`: matched proofs
- `missing`: unmet proofs or gates

Rules:

1. `status=complete` when all completion evidence found; `in_progress` when partial; `pending` when none.
2. `advance_ready=yes` only when `status=complete` AND all gates pass.
3. **`NEXT`** = first checkpoint where `status != complete` OR `advance_ready != yes`.
4. When all checkpoints pass: `NEXT | none | all checkpoints are complete`.

## Operating Modes

- **Interactive**: scope still fluid; pause at design boundaries for user confirmation.
- **Non-interactive** (default after contract agreed): auto-advance when gates pass; stop on hard blockers. Expose via `--non-interactive` flag.
- **Automation gating**: keep pass/fail semantics explicit first. A CLI may render reports with exit `0` by default, then use a flag such as `--fail-on-blocked` to exit non-zero when `NEXT` is blocked.

## Failure Thresholds

Auto-advance must not loop forever. Stop when:

- 3 consecutive failed repair attempts on the same checkpoint
- Evidence ambiguity affecting public behavior or source-of-truth data
- Required external input cannot be inferred safely
- Verification contradicts declared status

On stop, keep `NEXT` on the blocked checkpoint; surface blockers in `missing` or `blocking_reason`.

## Evidence Hierarchy

Prefer stronger evidence first:

1. Committed code or commit subjects on intended branch
2. Update-log / changelog markers declaring checkpoint closed
3. Fresh verification output from current branch
4. Live runtime audit results (scheduled jobs, deployed state)
5. Clean worktree state

Prose alone cannot enable auto-advance when implementation or verification gates are missing.

## Artifacts

Maintain these stable artifacts:

- **Plan**: roadmap spec defining ordered checkpoints
- **Audit script**: CLI computing `status`, `advance_ready`, `NEXT`
- **Update log**: changelog marker proving checkpoint closure
- **Snapshot** (optional): `CHECKPOINT_STATUS.md` / `ROADMAP_AUDIT.md` / JSON via `--json-out` — derived, never sole source of truth

## Implementation Pattern

Two-layer audit script:

1. **Pure checkpoint evaluator**: checkpoint definition + evidence + gate state -> `status`, `advance_ready`, `evidence`, `missing`
2. **Repo-backed collector**: reads git log, update-log, runtime audit, worktree state; evaluates all checkpoints; renders report

The `NEXT` function must be pure and order-sensitive:

```python
def next_incomplete(results):
    for result in results:
        if result.status != "complete" or result.advance_ready != "yes":
            return result
    return None
```

For unattended execution, print enough structure for resumption without conversation replay.

## Test Pattern

Lock semantics with three smoke tests:

1. **Red**: completion evidence exists, gate failing -> `NEXT` stays on current checkpoint
2. **Green**: completion evidence exists, gate passes -> `NEXT` advances
3. **Finished**: all complete and gate-clean -> `NEXT | none | all checkpoints are complete`

## Persistence

Scripts recompute truth from commits, docs, verification, and runtime state. Snapshots improve resume speed but never replace the evaluator. JSON snapshots should include `snapshot_schema_version`, per-checkpoint `status`, `advance_ready`, `evidence`, `missing`, and the final `NEXT`. If a JSON snapshot is part of an automation contract, keep a schema file for the snapshot output separate from the fixture input schema. Never let an agent edit markdown to mark progress without audit script backing.

## Common Mistakes

- Advancing based only on `status=complete` without checking gates
- Treating dirty worktree as irrelevant
- No stop policy for repeated failures in non-interactive mode
- Letting snapshot files become the only status source
- Conflating "owner branch complete" with "mainline integrated"
- Using brittle evidence (unstaged local notes) instead of committed facts

## Verification

Before claiming self-advancing capability, run:

1. Audit smoke tests
2. Audit CLI itself
3. Project's main verification command (if checkpoint depends on repo health)
4. `git status --short` cleanliness check
