# Public Demo Walkthrough

This walkthrough uses the repository's self-contained demo instead of any private project.

## Files

- `demo/fixtures/sample-roadmap.json`
- `demo/check_demo_roadmap.py`
- `tests/test_demo_roadmap.py`

## What It Demonstrates

- `CP1` is fully complete and gate-clean.
- `CP2` has landed evidence, but `worktree_clean` is still failing.
- `CP3` and later checkpoints are still incomplete.

The important outcome is:

```text
NEXT | CP2 | Core implementation
```

That proves the central rule of the skill:

- `NEXT` means the first gate-unpassed checkpoint
- not merely the first checkpoint missing one marker

## Run It

```text
python demo/check_demo_roadmap.py
python -m unittest tests/test_demo_roadmap.py
```

## Expected Learning

Use this demo when you want to understand or explain the method without relying on Charlotte:

1. completion evidence and gate status are different concepts
2. `status=complete` does not imply auto-advance
3. a clean terminal state must end with `NEXT | none | all checkpoints are complete`
