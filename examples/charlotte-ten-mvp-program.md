# Charlotte Ten-MVP Program

This example shows how the skill was applied to a ten-MVP owner-worktree program.

## Checkpoint Shape

- `MVP1 .. MVP10`
- each checkpoint had:
  - update-log close-out marker
  - owner worktree cleanliness gate
  - optional commit evidence

## Expected Audit Output

```text
Charlotte Ten-MVP Program Audit
============================================================
MVP1 | status=complete | clean=yes | advance_ready=yes
...
MVP10 | status=complete | clean=yes | advance_ready=yes
NEXT | none | all ten MVP checkpoints are complete
```

## Why This Matters

- owner branch completion was kept separate from mainline integration
- dirty worktrees blocked false auto-advance
- `NEXT` always stayed aligned with the first gate-unpassed MVP
