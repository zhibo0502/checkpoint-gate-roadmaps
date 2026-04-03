# Charlotte Post-MVP Integration

This example shows how the skill was applied to a post-MVP integration roadmap.

## Parent Roadmap

- `SLICE1 | weekly export hardening`
- `SLICE2 | monthly closure stack`
- `SLICE3 | topic retrieval / table evidence / memory delta`
- `SLICE4 | editorial workbench`
- `SLICE5 | canonical reconciliation`

## Child Pack

The parent roadmap was paired with a finer-grained `CP1..CP12` integration pack.

That allowed:

- long-running non-interactive execution
- stable recovery after context compaction
- parent `NEXT` and child `NEXT` to remain independently truthful

## Gate Behavior

Even after focused tests and full verification were green, `NEXT` did not advance while the worktree was still dirty.

Only after:

- completion commit landed
- update-log marker existed
- worktree became clean

did the parent roadmap move from:

```text
NEXT | SLICE4 | editorial workbench
```

to:

```text
NEXT | SLICE5 | canonical reconciliation
```

and finally:

```text
NEXT | none | all post-mvp integration checkpoints are complete
```
