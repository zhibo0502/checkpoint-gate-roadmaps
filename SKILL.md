---
name: checkpoint-gate-roadmaps
description: Use when a roadmap, staged delivery plan, rollout plan, or integration sequence needs scriptable checkpoints with gate-based auto-advance, explicit NEXT semantics, and evidence-backed status reporting.
---

# Checkpoint Gate Roadmaps

## Overview

Use this skill when a multi-step roadmap should advance automatically only after the current checkpoint has really passed its gate. The core contract is simple: `NEXT` must point to the first checkpoint whose gate is not yet satisfied, not merely the first checkpoint missing some completion evidence.

## When to Use

- A user asks to "set checkpoints", "auto-advance to the next checkpoint", "audit roadmap progress", or "make this plan self-checking"
- A roadmap has ordered milestones such as `MVP1..MVP10`, `Phase 1..4`, or `Slice 1..5`
- You need a stable CLI or script that reports `status`, `advance_ready`, evidence, gaps, and `NEXT`
- Dirty worktrees, missing doc markers, missing commits, or failed verification must block automatic progression
- The user wants the roadmap to keep moving in a mostly unattended or non-interactive mode
- The roadmap mixes human documentation and code changes, so progress must be grounded in both

Do not use this skill for one-off todo lists that do not need durable audit semantics.

## Core Contract

For each checkpoint, define:

- `key`: stable identifier such as `MVP4` or `SLICE2`
- `name`: short human label
- `done evidence`: strongest proof that the checkpoint work landed
- `gate`: extra conditions required before auto-advance is allowed

Recommended output fields:

- `status`: `complete`, `in_progress`, or `pending`
- `advance_ready`: `yes` or `no`
- `evidence`: matched proofs
- `missing`: unmet proofs or gates
- `NEXT`: the first checkpoint whose gate is not fully passed

Rules:

1. `status=complete` means completion evidence was found.
2. `advance_ready=yes` means the checkpoint is actually safe to advance past.
3. `NEXT` is the first checkpoint where either:
   - `status != complete`, or
   - `advance_ready != yes`
4. When every checkpoint is both `complete` and `advance_ready=yes`, report:
   - `NEXT | none | all checkpoints are complete`

## Operating Modes

Support two explicit modes:

- Interactive:
  - good when scope is still moving
  - okay to pause for user confirmation at major design boundaries
- Non-interactive:
  - default after the roadmap and checkpoint contract are already agreed
  - automatically moves from one checkpoint to the next when the current gate passes
  - must stop instead of guessing when a hard blocker appears

If you expose a CLI, prefer a clear switch such as `--non-interactive` or a stable default that is documented in the runbook.

## Failure Thresholds

Auto-advance must not loop forever. Define a stop policy such as:

- stop after `3` consecutive failed repair attempts on the same checkpoint
- stop immediately on evidence ambiguity that could change public behavior or source-of-truth data
- stop when a required external input cannot be inferred safely
- stop when verification contradicts the roadmap's declared status

When the stop policy triggers, keep `NEXT` on the blocked checkpoint and surface the blocker explicitly in `missing` or a dedicated `blocking_reason`.

## Evidence Hierarchy

Prefer stronger, more stable evidence before weaker signals:

1. Committed code or commit subjects on the intended branch
2. Update-log or changelog markers that declare the checkpoint closed
3. Fresh verification output from the current branch
4. Live runtime audit results, when the checkpoint involves real scheduled jobs, deployed state, or external systems
5. Clean worktree state

Do not let a checkpoint auto-advance based on prose alone if the implementation or verification gate is still missing.

## Artifact Contract

For durable roadmap operation, keep a small set of stable artifacts:

- Plan artifact:
  - the roadmap spec or plan document that defines ordered checkpoints
- Audit artifact:
  - a CLI or script that computes `status`, `advance_ready`, and `NEXT`
- Update-log artifact:
  - the changelog marker proving a checkpoint was closed
- Optional status snapshot:
  - a machine-readable or human-readable file such as `CHECKPOINT_STATUS.md`, `ROADMAP_AUDIT.md`, or JSON output

Recommended per-checkpoint contract:

- `required_inputs`
  - what must already exist before this checkpoint can run
- `produces`
  - what new code, docs, outputs, or commits should exist after the checkpoint passes
- `gate`
  - what conditions must be true before auto-advance is allowed
- `next`
  - the next checkpoint key if the gate passes

This contract keeps the roadmap explainable even outside the agent session.

## Implementation Pattern

Use a small audit script with two layers:

1. Pure checkpoint evaluator
   - Input: checkpoint definition + evidence text + gate state
   - Output: normalized `status`, `advance_ready`, `evidence`, `missing`
2. Repo-backed collector
   - Reads branch log, update-log file, runtime audit output, and worktree cleanliness
   - Evaluates all checkpoints in order
   - Renders the final audit report

Keep the `NEXT` function pure and order-sensitive:

```python
def next_incomplete(results):
    for result in results:
        if result.status != "complete" or result.advance_ready != "yes":
            return result
    return None
```

This is the key guardrail. If the current checkpoint is complete but the worktree is dirty, `NEXT` must stay on the current checkpoint.

If the roadmap supports unattended execution, make the script print enough structure that another agent or operator can resume from the latest audit without replaying the whole conversation.

## Test Pattern

Lock the semantics with smoke tests before trusting the audit:

1. Red case:
   - current checkpoint has completion evidence
   - gate is still failing, such as `worktree_clean = no`
   - expected result: `NEXT` stays on the current checkpoint
2. Green case:
   - current checkpoint has completion evidence
   - gate passes
   - expected result: `NEXT` advances to the next checkpoint
3. Finished case:
   - all checkpoints complete and gate-clean
   - expected result: `NEXT | none | all checkpoints are complete`

If the audit script claims success without fresh verification, the roadmap is not trustworthy.

## Documentation Pattern

Whenever you add a checkpoint audit, update three kinds of docs together:

- Current-system or canonical operations doc:
  - where to run the audit
  - what `NEXT` means
- Runbook:
  - how operators should interpret `status` and `advance_ready`
- Update log or changelog:
  - what changed in the audit semantics
  - what the current frontier is

Do not leave docs saying "auto-advance" if the script still advances on incomplete gates.

If the roadmap is meant to survive thread resets or context compaction, add one durable place where the latest frontier can be read without recomputing history:

- `ROADMAP_AUDIT.md`
- `CHECKPOINT_STATUS.md`
- or a checked-in JSON summary generated by the audit script

This file should never become the sole source of truth; it is a snapshot, not a substitute for the audit logic.

## Persistence Pattern

Use snapshots only to improve resume speed, not to replace the real evaluator.

Good pattern:

- script recomputes truth from commits, docs, verification, and runtime state
- script may also write a snapshot for humans or later sessions

Bad pattern:

- agent edits a markdown file to mark progress complete
- no audit script or verification backs that state

If a snapshot is written, keep it obviously derived and easy to regenerate.

## Public Demo

This repository should include a self-contained runnable demo so the skill can be understood without any external project context.

Recommended demo shape:

- a small fixture file such as `demo/fixtures/sample-roadmap.json`
- a tiny CLI such as `demo/check_demo_roadmap.py`
- smoke tests that prove:
  - `NEXT` stays on the current checkpoint when completion evidence exists but the gate still fails
  - `NEXT` advances only after the current gate passes
  - terminal state is `NEXT | none | all checkpoints are complete`

If a user cannot access the original repository context, the public demo must still teach the method end to end.

## Scenario Examples

Use the bundled example docs when you need broader, non-runnable scenario shapes in addition to the public demo:

- `examples/ten-stage-delivery-program.md`
- `examples/post-release-integration-rollout.md`

These examples stay generic while demonstrating the same rule:

- `NEXT` is the first gate-unpassed checkpoint, not just the first checkpoint lacking one evidence marker.

## Common Mistakes

- Advancing based only on `status=complete`
- Treating dirty worktree state as irrelevant
- Having no stop policy for repeated failures in non-interactive mode
- Letting a snapshot file become the only status source
- Mixing "owner branch complete" with "mainline already integrated"
- Updating the script without updating the changelog marker contract
- Using brittle evidence such as unstaged local notes instead of committed or logged facts

## Verification

Before claiming the roadmap is self-advancing, run:

1. The audit smoke test
2. The audit CLI itself
3. The project's main verification command, if the checkpoint depends on repo health
4. A final `git status --short` or equivalent cleanliness check

No completion claim without fresh evidence.
