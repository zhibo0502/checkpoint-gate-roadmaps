# Changelog

## Unreleased

- added `snapshot_schema_version` to JSON snapshots so downstream automation can detect the snapshot contract version
- added a dedicated snapshot output schema separate from the roadmap fixture input schema
- added explicit `--fail-on-blocked` exit policy for CI and unattended automation
- added derived `blocking_reason` to JSON snapshots for automation logs and operator summaries
- added `--json-out` parity to the git-backed collector demo

## v0.2.0

- added `in_progress` status for checkpoints with partial evidence (spec/code alignment)
- trimmed SKILL.md from 242 to 126 lines, removing redundant NEXT definitions
- added fixture format documentation to README (bilingual)
- added git-backed collector example (`demo/git_collector_example.py`) with 5 checkpoints
- added runnable fixtures for ten-stage and post-release examples
- added error handling: file-not-found, invalid JSON, missing required fields
- renamed `agents/openai.yaml` to `agents/codex.yaml`
- added `--format json|markdown` output options for CI integration
- added `--json-out` to persist the derived audit snapshot, including final `NEXT`, for resumable batch gates
- added `--validate` flag with JSON Schema (`demo/schema.json`)
- enhanced git collector: license, CI, tests, tags, recent activity checks
- tests: 8 → 21

## v0.1.2

- generalized public docs, scenario examples, and preview asset names to remove project-specific references
- removed tracked Python cache artifacts from the published repository

## v0.1.1

- added a self-contained runnable public demo under `demo/`
- added smoke tests for `NEXT` gate semantics under `tests/`
- moved the repository documentation to demo-first wording instead of project-specific usage
- added a public walkthrough in `examples/public-demo.md`

## v0.1.0

- published the initial `checkpoint-gate-roadmaps` skill
- added the packaged repository structure, license, examples, and first release tag
