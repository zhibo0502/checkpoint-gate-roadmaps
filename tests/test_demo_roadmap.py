import copy
import json
import pathlib
import subprocess
import sys
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "demo" / "fixtures" / "sample-roadmap.json"
SCRIPT_PATH = REPO_ROOT / "demo" / "check_demo_roadmap.py"


class DemoRoadmapAuditTests(unittest.TestCase):
    def load_fixture(self):
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_next_stays_on_first_gate_unpassed_checkpoint(self):
        from demo.check_demo_roadmap import evaluate_roadmap, next_incomplete

        roadmap = self.load_fixture()

        results = evaluate_roadmap(roadmap)
        current = next_incomplete(results)

        self.assertIsNotNone(current)
        self.assertEqual("CP2", current["key"])
        self.assertEqual("complete", current["status"])
        self.assertEqual("no", current["advance_ready"])
        self.assertIn("worktree_clean", current["missing"])

    def test_next_advances_after_current_checkpoint_gate_passes(self):
        from demo.check_demo_roadmap import evaluate_roadmap, next_incomplete

        roadmap = copy.deepcopy(self.load_fixture())
        roadmap["checkpoints"][1]["gate"][1]["passed"] = True

        results = evaluate_roadmap(roadmap)
        current = next_incomplete(results)

        self.assertIsNotNone(current)
        self.assertEqual("CP3", current["key"])
        self.assertEqual("in_progress", current["status"])

    def test_finished_state_reports_none(self):
        from demo.check_demo_roadmap import evaluate_roadmap, next_incomplete, render_report

        roadmap = copy.deepcopy(self.load_fixture())
        for checkpoint in roadmap["checkpoints"]:
            for proof in checkpoint["done_evidence"]:
                proof["found"] = True
            for gate in checkpoint["gate"]:
                gate["passed"] = True

        results = evaluate_roadmap(roadmap)

        self.assertIsNone(next_incomplete(results))
        report = render_report(results)
        self.assertIn("NEXT | none | all checkpoints are complete", report)

    def test_in_progress_status_for_partial_evidence(self):
        from demo.check_demo_roadmap import evaluate_checkpoint

        checkpoint = {
            "key": "X1",
            "name": "Partial work",
            "done_evidence": [
                {"label": "commit_subject", "found": True},
                {"label": "update_log_marker", "found": False},
            ],
            "gate": [{"label": "worktree_clean", "passed": True}],
        }

        result = evaluate_checkpoint(checkpoint)

        self.assertEqual("in_progress", result["status"])
        self.assertEqual("no", result["advance_ready"])
        self.assertIn("commit_subject", result["evidence"])
        self.assertIn("update_log_marker", result["missing"])

    def test_cli_renders_public_demo_output(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("ROADMAP | Public Demo Roadmap", completed.stdout)
        self.assertIn("NEXT | CP2 | Core implementation", completed.stdout)


    def test_missing_fixture_exits_with_error(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--fixture", "/nonexistent/file.json"],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("fixture not found", completed.stderr)

    def test_checkpoint_missing_key_raises(self):
        from demo.check_demo_roadmap import evaluate_checkpoint

        with self.assertRaises(ValueError):
            evaluate_checkpoint({"name": "no key"})

    def test_checkpoint_missing_name_raises(self):
        from demo.check_demo_roadmap import evaluate_checkpoint

        with self.assertRaises(ValueError):
            evaluate_checkpoint({"key": "X1"})

    def test_json_format_output(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        parsed = json.loads(completed.stdout)
        self.assertEqual("CP2", parsed["next"])
        self.assertEqual("CP2", parsed["NEXT"]["key"])
        self.assertEqual("no", parsed["NEXT"]["advance_ready"])
        self.assertEqual(5, len(parsed["checkpoints"]))

    def test_cli_writes_json_snapshot_for_resumable_gate(self):
        snapshot_path = REPO_ROOT / ".test-audit-snapshot.json"
        snapshot_path.unlink(missing_ok=True)
        self.addCleanup(snapshot_path.unlink, missing_ok=True)

        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json-out", str(snapshot_path)],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("NEXT | CP2 | Core implementation", completed.stdout)

        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual("Public Demo Roadmap", snapshot["roadmap_name"])
        self.assertEqual("CP2", snapshot["next"])
        self.assertEqual("CP2", snapshot["NEXT"]["key"])
        self.assertEqual("complete", snapshot["NEXT"]["status"])
        self.assertEqual("no", snapshot["NEXT"]["advance_ready"])
        self.assertIn("worktree_clean", snapshot["NEXT"]["missing"])

        checkpoints = snapshot["checkpoints"]
        self.assertEqual(5, len(checkpoints))
        for checkpoint in checkpoints:
            for field in ("key", "name", "status", "advance_ready", "evidence", "missing"):
                self.assertIn(field, checkpoint)

    def test_json_snapshot_finished_state_reports_next_none(self):
        from demo.check_demo_roadmap import build_snapshot, evaluate_roadmap

        roadmap = copy.deepcopy(self.load_fixture())
        for checkpoint in roadmap["checkpoints"]:
            for proof in checkpoint["done_evidence"]:
                proof["found"] = True
            for gate in checkpoint["gate"]:
                gate["passed"] = True

        snapshot = build_snapshot(
            evaluate_roadmap(roadmap),
            roadmap_name=roadmap.get("roadmap_name"),
        )

        self.assertIsNone(snapshot["next"])
        self.assertEqual("none", snapshot["NEXT"]["key"])
        self.assertEqual("all checkpoints are complete", snapshot["NEXT"]["name"])
        self.assertEqual([], snapshot["NEXT"]["missing"])

    def test_markdown_format_output(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--format", "markdown"],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("| Key |", completed.stdout)
        self.assertIn("**NEXT**: `CP2`", completed.stdout)

    def test_validate_flag_accepts_valid_fixture(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--validate"],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_validate_flag_rejects_invalid_fixture(self):
        import tempfile
        bad = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        bad.write('{"checkpoints": [{"key": 123}]}')
        bad.close()

        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--fixture", bad.name, "--validate"],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Schema validation failed", completed.stderr)

        import os
        os.unlink(bad.name)


if __name__ == "__main__":
    unittest.main()
