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
        self.assertEqual("pending", current["status"])

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


if __name__ == "__main__":
    unittest.main()
