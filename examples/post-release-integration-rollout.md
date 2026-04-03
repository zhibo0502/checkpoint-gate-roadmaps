# Post-Release Integration Rollout

This example shows how the skill can be applied to a post-release integration rollout.

## Parent Roadmap

- `PHASE1 | export stabilization`
- `PHASE2 | monthly close workflow`
- `PHASE3 | retrieval and reporting`
- `PHASE4 | editorial tooling`
- `PHASE5 | final reconciliation`

## Detailed Checkpoint Set

The parent roadmap was paired with a finer-grained `CP1..CP12` checkpoint set.

That allowed:

- long-running non-interactive execution
- stable recovery after context compaction
- parent `NEXT` and child `NEXT` to remain independently truthful

## Run It

```text
python demo/check_demo_roadmap.py --fixture examples/fixtures/post-release-rollout.json
```

Expected output: `NEXT | PHASE3 | Retrieval and reporting` (partial evidence, dirty worktree).

## Gate Behavior

Even after focused tests and full verification were green, `NEXT` did not advance while the worktree was still dirty.

Only after:

- completion commit landed
- update-log marker existed
- worktree became clean

did the parent roadmap move from:

```text
NEXT | PHASE4 | editorial tooling
```

to:

```text
NEXT | PHASE5 | final reconciliation
```

and finally:

```text
NEXT | none | all rollout checkpoints are complete
```
