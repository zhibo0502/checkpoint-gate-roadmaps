# Ten-Stage Delivery Program

This example shows how the skill can be applied to a ten-stage delivery program.

## Checkpoint Shape

- `STAGE1 .. STAGE10`
- each checkpoint had:
  - update-log close-out marker
  - worktree cleanliness gate
  - optional commit evidence

## Expected Audit Output

```text
Ten-Stage Delivery Program Audit
============================================================
STAGE1 | status=complete | clean=yes | advance_ready=yes
...
STAGE10 | status=complete | clean=yes | advance_ready=yes
NEXT | none | all delivery checkpoints are complete
```

## Run It

```text
python demo/check_demo_roadmap.py --fixture examples/fixtures/ten-stage-delivery.json
```

Expected output: `NEXT | STAGE4 | Integration layer` (complete but dirty worktree).

## Why This Matters

- delivery-stage completion was kept separate from later integration work
- dirty worktrees blocked false auto-advance
- `NEXT` always stayed aligned with the first gate-unpassed stage
