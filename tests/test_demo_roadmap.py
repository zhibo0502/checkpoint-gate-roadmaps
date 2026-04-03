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


if __name__ == "__main__":
    unittest.main()
