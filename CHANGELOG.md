# Changelog

## v0.2.0

- added `in_progress` status for checkpoints with partial evidence (spec/code alignment)
- trimmed SKILL.md from 242 to 126 lines, removing redundant NEXT definitions
- added fixture format documentation to README (bilingual)
- added git-backed collector example (`demo/git_collector_example.py`) with tests
- added runnable fixtures for ten-stage and post-release examples
- added error handling: file-not-found, invalid JSON, missing required fields
- renamed `agents/openai.yaml` to `agents/codex.yaml`

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
