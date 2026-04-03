# checkpoint-gate-roadmaps

A reusable Codex skill for roadmap audits that use explicit checkpoints, gate-based auto-advance, durable `NEXT` semantics, and evidence-backed status reporting.

## Contents

- `SKILL.md`: main skill body
- `agents/openai.yaml`: display metadata

## Use Cases

Use this skill when a roadmap or rollout needs:

- ordered checkpoints such as `MVP1..MVP10`, `Phase 1..4`, or `Slice 1..5`
- a stable `NEXT` that points to the first gate-unpassed checkpoint
- blocking on dirty worktrees, missing doc markers, missing commits, or failed verification
- optional derived snapshots without replacing the real audit logic

## Example

The skill was used to drive Charlotte's:

- ten-MVP owner-worktree audit
- post-MVP integration slice audit
- child integration-pack checkpoint audit

## Install

Copy this directory into your Codex skills directory as:

```text
$CODEX_HOME/skills/checkpoint-gate-roadmaps
```
