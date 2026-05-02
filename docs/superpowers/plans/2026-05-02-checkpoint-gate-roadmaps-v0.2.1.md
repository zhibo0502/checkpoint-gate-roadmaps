# Checkpoint Gate Roadmaps v0.2.1+ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `checkpoint-gate-roadmaps` from a strong demo skill into a stricter, reusable audit tool for real repositories and unattended batch workflows.

**Architecture:** Keep `demo/check_demo_roadmap.py` as the canonical pure evaluator and renderer. Add separate schema, exit-policy, and collector layers around that evaluator without weakening the existing `NEXT` semantics or making snapshots a source of truth.

**Tech Stack:** Python standard library, `unittest`, optional `jsonschema`, git CLI, Markdown docs.

---

## Scope Decisions

- Keep domain-specific examples out of this repository; generic batch wording is enough here.
- Keep default CLI behavior backward compatible unless a new opt-in flag is used.
- Treat this as a reusable CLI tool first, not just a teaching artifact.
- Prefer machine-parseable contracts over prose-only output for automation paths.
- Any behavior that changes automation pass/fail semantics must be explicit first, such as `--fail-on-blocked`.
- Prefer small publishable releases: `v0.2.1` for snapshot contract hardening, `v0.2.2` for explicit CI exit semantics and blocker summaries, `v0.3.0` for collector parity and configurable collectors.

## Accepted Direction

The user decision is: reusable CLI tool, explicit automation flags first, optimized for downstream automation parsing. This means schema, stable JSON fields, and stable exit codes outrank additional prose examples. Human-readable text and Markdown output should remain useful, but they are secondary compatibility surfaces.

## File Structure

- Modify `demo/check_demo_roadmap.py`: shared snapshot builder, renderer, and future exit-policy hooks.
- Create `demo/snapshot_schema.json`: schema for derived audit snapshots, separate from fixture schema.
- Modify `demo/git_collector_example.py`: later add `--json-out` parity and collector rule config support.
- Modify `tests/test_demo_roadmap.py`: CLI and snapshot contract tests.
- Create `tests/test_snapshot_schema.py`: schema validation tests for generated snapshots.
- Modify `tests/test_git_collector.py`: collector parity and configured collector tests.
- Modify `README.md`: operator-facing examples for snapshots, CI gates, and real repo collectors.
- Modify `SKILL.md`: concise rules for snapshot contract, exit policy, and collector configuration.
- Modify `CHANGELOG.md`: release notes under `Unreleased` until tagging.

---

### Task 1: Finish v0.2.1 Snapshot Contract Hardening

**Files:**
- Create: `demo/snapshot_schema.json`
- Create: `tests/test_snapshot_schema.py`
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Write the failing snapshot schema test**

Create `tests/test_snapshot_schema.py`:

```python
import json
import pathlib
import subprocess
import sys
import unittest

import jsonschema


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "demo" / "check_demo_roadmap.py"
SNAPSHOT_SCHEMA_PATH = REPO_ROOT / "demo" / "snapshot_schema.json"


class SnapshotSchemaTests(unittest.TestCase):
    def load_schema(self):
        return json.loads(SNAPSHOT_SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_snapshot_schema_accepts_cli_json_output(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        jsonschema.validate(
            instance=json.loads(completed.stdout),
            schema=self.load_schema(),
        )

    def test_snapshot_schema_requires_version(self):
        snapshot = {
            "roadmap_name": "Roadmap",
            "checkpoints": [],
            "next": None,
            "NEXT": {
                "key": "none",
                "name": "all checkpoints are complete",
                "status": "complete",
                "advance_ready": "yes",
                "evidence": [],
                "missing": [],
            },
        }

        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance=snapshot, schema=self.load_schema())


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run the failing test**

Run:

```text
python -m unittest discover -s tests -p "test_snapshot_schema.py"
```

Expected result:

```text
ERROR: file demo/snapshot_schema.json does not exist
```

- [x] **Step 3: Add the snapshot schema**

Create `demo/snapshot_schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Checkpoint Gate Roadmap Snapshot",
  "description": "Schema for derived checkpoint-gate-roadmaps audit snapshots.",
  "type": "object",
  "required": ["snapshot_schema_version", "roadmap_name", "checkpoints", "next", "NEXT"],
  "properties": {
    "snapshot_schema_version": { "type": "integer", "const": 1 },
    "roadmap_name": { "type": ["string", "null"] },
    "checkpoints": {
      "type": "array",
      "items": { "$ref": "#/$defs/checkpoint_result" }
    },
    "next": { "type": ["string", "null"] },
    "NEXT": { "$ref": "#/$defs/checkpoint_result" }
  },
  "$defs": {
    "checkpoint_result": {
      "type": "object",
      "required": ["key", "name", "status", "advance_ready", "evidence", "missing"],
      "properties": {
        "key": { "type": "string" },
        "name": { "type": "string" },
        "status": { "type": "string", "enum": ["complete", "in_progress", "pending"] },
        "advance_ready": { "type": "string", "enum": ["yes", "no"] },
        "evidence": { "type": "array", "items": { "type": "string" } },
        "missing": { "type": "array", "items": { "type": "string" } }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

- [x] **Step 4: Run the schema test**

Run:

```text
python -m unittest discover -s tests -p "test_snapshot_schema.py"
```

Expected result:

```text
Ran 2 tests
OK
```

- [x] **Step 5: Update docs**

Add one README sentence near the JSON snapshot section:

```markdown
The generated snapshot also validates against `demo/snapshot_schema.json`, which is separate from the fixture schema because snapshots are derived outputs rather than user-authored roadmap inputs.
```

Add one SKILL.md sentence under `Persistence`:

```markdown
If a JSON snapshot is part of an automation contract, keep a schema file for the snapshot output separate from the fixture input schema.
```

- [x] **Step 6: Verify and commit**

Run:

```text
python -m unittest discover -s tests -p "test_*.py"
git status --short
```

Expected result:

```text
OK
```

Commit:

```text
git add demo/snapshot_schema.json tests/test_snapshot_schema.py README.md SKILL.md CHANGELOG.md
git commit -m "Add snapshot schema validation"
```

---

### Task 2: Add CI-Friendly Exit Policy

**Files:**
- Modify: `demo/check_demo_roadmap.py`
- Modify: `tests/test_demo_roadmap.py`
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Write failing tests for blocked and complete states**

Add to `tests/test_demo_roadmap.py`:

```python
    def test_fail_on_blocked_returns_exit_code_two_when_next_exists(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--fail-on-blocked"],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(2, completed.returncode)
        self.assertIn("NEXT | CP2 | Core implementation", completed.stdout)

    def test_fail_on_blocked_returns_zero_when_all_checkpoints_pass(self):
        import tempfile
        roadmap = copy.deepcopy(self.load_fixture())
        for checkpoint in roadmap["checkpoints"]:
            for proof in checkpoint["done_evidence"]:
                proof["found"] = True
            for gate in checkpoint["gate"]:
                gate["passed"] = True

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fixture:
            json.dump(roadmap, fixture)
            fixture_path = fixture.name

        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--fixture",
                    fixture_path,
                    "--fail-on-blocked",
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
        finally:
            pathlib.Path(fixture_path).unlink(missing_ok=True)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("NEXT | none | all checkpoints are complete", completed.stdout)
```

- [x] **Step 2: Run the failing tests**

Run:

```text
python -m unittest discover -s tests -p "test_demo_roadmap.py"
```

Expected result:

```text
error: unrecognized arguments: --fail-on-blocked
```

- [x] **Step 3: Implement minimal exit policy**

In `demo/check_demo_roadmap.py`, add:

```python
EXIT_BLOCKED = 2
```

In `parse_args()`:

```python
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="Exit with code 2 when NEXT is not complete.",
    )
```

At the end of `main()`:

```python
    print(renderer(results, roadmap_name=roadmap_name))
    if args.fail_on_blocked and next_incomplete(results) is not None:
        sys.exit(EXIT_BLOCKED)
```

- [x] **Step 4: Verify**

Run:

```text
python -m unittest discover -s tests -p "test_demo_roadmap.py"
python -m unittest discover -s tests -p "test_*.py"
```

Expected result:

```text
OK
```

- [x] **Step 5: Document operator behavior**

Add README example:

```text
python demo/check_demo_roadmap.py --fail-on-blocked
```

Add explanation:

```markdown
Use `--fail-on-blocked` in CI or unattended runs. It preserves normal output but exits `2` when `NEXT` still points to a blocked checkpoint.
```

- [x] **Step 6: Commit**

```text
git add demo/check_demo_roadmap.py tests/test_demo_roadmap.py README.md SKILL.md CHANGELOG.md
git commit -m "Add blocked checkpoint exit policy"
```

---

### Task 3: Add Actionable Blocker Summaries

**Files:**
- Modify: `demo/check_demo_roadmap.py`
- Modify: `tests/test_demo_roadmap.py`
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Write failing tests for blocker text**

Add to `tests/test_demo_roadmap.py`:

```python
    def test_snapshot_includes_blocking_reason_for_current_next(self):
        from demo.check_demo_roadmap import build_snapshot, evaluate_roadmap

        snapshot = build_snapshot(
            evaluate_roadmap(self.load_fixture()),
            roadmap_name="Public Demo Roadmap",
        )

        self.assertEqual(
            "CP2 is complete but cannot advance because gates are failing: worktree_clean",
            snapshot["blocking_reason"],
        )

    def test_finished_snapshot_has_no_blocking_reason(self):
        from demo.check_demo_roadmap import build_snapshot, evaluate_roadmap

        roadmap = copy.deepcopy(self.load_fixture())
        for checkpoint in roadmap["checkpoints"]:
            for proof in checkpoint["done_evidence"]:
                proof["found"] = True
            for gate in checkpoint["gate"]:
                gate["passed"] = True

        snapshot = build_snapshot(evaluate_roadmap(roadmap))

        self.assertIsNone(snapshot["blocking_reason"])
```

- [x] **Step 2: Run failing tests**

```text
python -m unittest discover -s tests -p "test_demo_roadmap.py"
```

Expected result:

```text
KeyError: 'blocking_reason'
```

- [x] **Step 3: Implement blocker summary**

Add to `demo/check_demo_roadmap.py`:

```python
def describe_blocker(current):
    if current is None:
        return None
    missing = ", ".join(current["missing"]) if current["missing"] else "unknown blocker"
    if current["status"] == "complete":
        return f"{current['key']} is complete but cannot advance because gates are failing: {missing}"
    return f"{current['key']} is {current['status']} and still missing: {missing}"
```

Add to `build_snapshot()`:

```python
        "blocking_reason": describe_blocker(current),
```

- [x] **Step 4: Verify and document**

Run:

```text
python -m unittest discover -s tests -p "test_*.py"
```

Add README text:

```markdown
`blocking_reason` is derived from the current `NEXT`; it is a convenience field for operators, not a replacement for per-checkpoint `missing`.
```

- [x] **Step 5: Commit**

```text
git add demo/check_demo_roadmap.py tests/test_demo_roadmap.py README.md SKILL.md CHANGELOG.md
git commit -m "Add snapshot blocking reason"
```

---

### Task 4: Bring `--json-out` Parity To Git Collector

**Files:**
- Modify: `demo/git_collector_example.py`
- Modify: `tests/test_git_collector.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Write failing collector CLI test**

Add to `tests/test_git_collector.py`:

```python
    def test_collector_cli_writes_json_snapshot(self):
        import json
        import subprocess
        import sys
        import tempfile

        snapshot_path = Path(tempfile.gettempdir()) / "checkpoint-gate-collector-snapshot.json"
        snapshot_path.unlink(missing_ok=True)
        self.addCleanup(snapshot_path.unlink, missing_ok=True)

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "demo.git_collector_example",
                "--repo",
                ".",
                "--json-out",
                str(snapshot_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        parsed = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(1, parsed["snapshot_schema_version"])
        self.assertTrue(parsed["roadmap_name"].startswith("Git Collector:"))
```

- [x] **Step 2: Run failing test**

```text
python -m unittest discover -s tests -p "test_git_collector.py"
```

Expected result:

```text
error: unrecognized arguments: --json-out
```

- [x] **Step 3: Implement collector parity**

In `demo/git_collector_example.py`, import:

```python
from demo.check_demo_roadmap import build_snapshot, evaluate_roadmap, RENDERERS, write_json_snapshot
```

Add parser argument:

```python
    parser.add_argument(
        "--json-out",
        help="Write the machine-readable audit snapshot JSON to a file.",
    )
```

Before printing:

```python
    if args.json_out:
        write_json_snapshot(
            build_snapshot(results, roadmap_name=roadmap["roadmap_name"]),
            args.json_out,
        )
```

- [x] **Step 4: Verify and commit**

```text
python -m unittest discover -s tests -p "test_git_collector.py"
python -m unittest discover -s tests -p "test_*.py"
git add demo/git_collector_example.py tests/test_git_collector.py README.md CHANGELOG.md
git commit -m "Add json snapshot output to git collector"
```

---

### Task 5: Make Real-Repo Collector Configurable

**Files:**
- Create: `demo/fixtures/repo-collector-rules.json`
- Modify: `demo/git_collector_example.py`
- Modify: `tests/test_git_collector.py`
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write the desired rules fixture**

Create `demo/fixtures/repo-collector-rules.json`:

```json
{
  "roadmap_name": "Configurable Repository Audit",
  "checkpoints": [
    {
      "key": "DOCS",
      "name": "Documentation present",
      "done_evidence": [
        { "label": "README.md", "type": "file_exists", "path": "README.md" },
        { "label": "CHANGELOG.md", "type": "file_exists", "path": "CHANGELOG.md" }
      ],
      "gate": [
        { "label": "worktree_clean", "type": "git_status_clean" }
      ]
    }
  ]
}
```

- [ ] **Step 2: Write failing tests for configured collection**

Add to `tests/test_git_collector.py`:

```python
    def test_collect_configured_evidence_from_rules_file(self):
        from demo.git_collector_example import collect_configured_evidence

        rules = {
            "roadmap_name": "Configured",
            "checkpoints": [
                {
                    "key": "DOCS",
                    "name": "Docs",
                    "done_evidence": [
                        {"label": "README.md", "type": "file_exists", "path": "README.md"}
                    ],
                    "gate": [
                        {"label": "worktree_clean", "type": "git_status_clean"}
                    ],
                }
            ],
        }

        with patch.object(Path, "is_file", return_value=True), \
             patch("demo.git_collector_example.run_git", return_value=(0, "")):
            roadmap = collect_configured_evidence("/fake/repo", rules)

        checkpoint = roadmap["checkpoints"][0]
        self.assertTrue(checkpoint["done_evidence"][0]["found"])
        self.assertTrue(checkpoint["gate"][0]["passed"])
```

- [ ] **Step 3: Run failing test**

```text
python -m unittest discover -s tests -p "test_git_collector.py"
```

Expected result:

```text
ImportError: cannot import name 'collect_configured_evidence'
```

- [ ] **Step 4: Implement the minimal rule engine**

Add to `demo/git_collector_example.py`:

```python
def evaluate_rule(repo, rule):
    rule_type = rule["type"]
    if rule_type == "file_exists":
        return (repo / rule["path"]).is_file()
    if rule_type == "git_status_clean":
        rc, output = run_git(["status", "--porcelain"], cwd=repo)
        return rc == 0 and output == ""
    raise ValueError(f"unsupported collector rule type: {rule_type}")


def collect_configured_evidence(repo_path, rules):
    repo = Path(repo_path).resolve()
    checkpoints = []
    for checkpoint in rules["checkpoints"]:
        checkpoints.append(
            {
                "key": checkpoint["key"],
                "name": checkpoint["name"],
                "done_evidence": [
                    {
                        "label": rule["label"],
                        "found": evaluate_rule(repo, rule),
                    }
                    for rule in checkpoint.get("done_evidence", [])
                ],
                "gate": [
                    {
                        "label": rule["label"],
                        "passed": evaluate_rule(repo, rule),
                    }
                    for rule in checkpoint.get("gate", [])
                ],
            }
        )
    return {"roadmap_name": rules.get("roadmap_name"), "checkpoints": checkpoints}
```

Add CLI argument:

```python
    parser.add_argument(
        "--rules",
        help="Path to collector rules JSON. When omitted, use the built-in demo collector.",
    )
```

Select collector:

```python
    if args.rules:
        rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
        roadmap = collect_configured_evidence(repo_path, rules)
    else:
        roadmap = collect_evidence(repo_path)
```

- [ ] **Step 5: Verify and commit**

```text
python -m unittest discover -s tests -p "test_git_collector.py"
python -m unittest discover -s tests -p "test_*.py"
git add demo/git_collector_example.py demo/fixtures/repo-collector-rules.json tests/test_git_collector.py README.md SKILL.md CHANGELOG.md
git commit -m "Add configurable git collector rules"
```

---

### Task 6: Prepare Release Closure

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `README.md`

- [ ] **Step 1: Decide version boundary**

Use this rule:

```text
v0.2.1 = snapshot schema only
v0.2.2 = explicit exit policy and blocker summary
v0.3.0 = git collector --json-out parity plus configurable collector rules
```

- [ ] **Step 2: Run full verification**

```text
python -m unittest discover -s tests -p "test_*.py"
python demo/check_demo_roadmap.py --format json
python demo/check_demo_roadmap.py --json-out CHECKPOINT_STATUS.json
python -m demo.git_collector_example --repo . --format json
Remove-Item -LiteralPath CHECKPOINT_STATUS.json -ErrorAction SilentlyContinue
git status --short
```

Expected result:

```text
OK
```

`git status --short` should show only intended tracked release edits before commit, then clean after commit.

- [ ] **Step 3: Tag only from main after merge**

After review and merge:

```text
git checkout main
git pull --ff-only origin main
git tag -a v0.2.1 -m "v0.2.1"
git push origin main v0.2.1
```

Do not tag from the development branch.

---

## Answered Decision Questions

1. This should become a reusable CLI utility, not only a teaching artifact.
2. Blocked checkpoints should affect automation only through explicit flags first; `--fail-on-blocked` should not become the default yet.
3. Snapshots should be optimized for downstream automation parsing first, with human-readable output kept as a compatible secondary surface.

## Recommended Execution Order

1. Finish Task 1 and release `v0.2.1`.
2. Implement Tasks 2 and 3 together as `v0.2.2`.
3. Implement Task 4 before Task 5 so the built-in git collector reaches output parity before becoming configurable.
4. Implement Task 5 as `v0.3.0`, because configurable collectors are the point where this becomes a reusable CLI tool rather than a fixed demo.
5. Use Task 6 for every release closure.
