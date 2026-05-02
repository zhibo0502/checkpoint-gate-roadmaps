import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from demo.git_collector_example import collect_evidence


REPO_ROOT = Path(__file__).resolve().parents[1]


def make_run_result(returncode=0, stdout=""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    return result


class GitCollectorTests(unittest.TestCase):
    @patch("demo.git_collector_example.subprocess.run")
    def test_clean_repo_all_gates_pass(self, mock_run):
        mock_run.side_effect = [
            make_run_result(0, "abc1234 initial commit"),  # git log -1
            make_run_result(0, "v0.1.0"),                   # git tag --list
            make_run_result(0, "def5678 recent work"),       # git log --since
            make_run_result(0, ""),                           # git status --porcelain
            make_run_result(0, "main"),                       # git branch
            make_run_result(0, ""),                           # git ls-files untracked
        ]

        with patch.object(Path, "is_file", return_value=True), \
             patch.object(Path, "is_dir", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter(["ci.yml"])), \
             patch.object(Path, "glob", return_value=iter(["test_foo.py"])):
            roadmap = collect_evidence("/fake/repo")

        self.assertEqual(5, len(roadmap["checkpoints"]))
        keys = [cp["key"] for cp in roadmap["checkpoints"]]
        self.assertEqual(["INIT", "DOCS", "TEST", "RELEASE", "ACTIVE"], keys)

        # All gates should pass in clean state
        for cp in roadmap["checkpoints"]:
            for gate in cp["gate"]:
                self.assertTrue(gate["passed"], f"{cp['key']}: {gate['label']} should pass")

    @patch("demo.git_collector_example.subprocess.run")
    def test_dirty_worktree_blocks_advance(self, mock_run):
        mock_run.side_effect = [
            make_run_result(0, "abc1234 initial commit"),
            make_run_result(0, ""),                           # no tags
            make_run_result(0, "abc recent"),
            make_run_result(0, " M README.md"),               # dirty
            make_run_result(0, "main"),
            make_run_result(0, ""),
        ]

        with patch.object(Path, "is_file", return_value=True), \
             patch.object(Path, "is_dir", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter(["ci.yml"])), \
             patch.object(Path, "glob", return_value=iter(["test_foo.py"])):
            roadmap = collect_evidence("/fake/repo")

        # DOCS checkpoint gate should fail
        docs_cp = roadmap["checkpoints"][1]
        self.assertFalse(docs_cp["gate"][0]["passed"])

    @patch("demo.git_collector_example.subprocess.run")
    def test_missing_tests_partial_evidence(self, mock_run):
        mock_run.side_effect = [
            make_run_result(0, "abc1234 initial commit"),
            make_run_result(0, "v0.1.0"),
            make_run_result(0, "abc recent"),
            make_run_result(0, ""),
            make_run_result(0, "main"),
            make_run_result(0, ""),
        ]

        original_is_file = Path.is_file
        original_is_dir = Path.is_dir

        def fake_is_file(self):
            if "LICENSE" in str(self):
                return False
            return True

        def fake_is_dir(self):
            # tests dir does not exist
            if "tests" in str(self):
                return False
            if "workflows" in str(self):
                return False
            return original_is_dir(self)

        with patch.object(Path, "is_file", fake_is_file), \
             patch.object(Path, "is_dir", fake_is_dir):
            roadmap = collect_evidence("/fake/repo")

        test_cp = roadmap["checkpoints"][2]  # TEST checkpoint
        has_tests = next(e for e in test_cp["done_evidence"] if e["label"] == "has_tests")
        self.assertFalse(has_tests["found"])
        has_ci = next(e for e in test_cp["done_evidence"] if e["label"] == "has_ci")
        self.assertFalse(has_ci["found"])

    @patch("demo.git_collector_example.subprocess.run")
    def test_format_flag_json(self, mock_run):
        """Verify the collector produces valid JSON output."""
        import json as json_mod
        from demo.check_demo_roadmap import evaluate_roadmap, RENDERERS

        mock_run.side_effect = [
            make_run_result(0, "abc1234 initial commit"),
            make_run_result(0, ""),
            make_run_result(0, ""),
            make_run_result(0, ""),
            make_run_result(0, "main"),
            make_run_result(0, ""),
        ]

        with patch.object(Path, "is_file", return_value=True), \
             patch.object(Path, "is_dir", return_value=True), \
             patch.object(Path, "iterdir", return_value=iter(["ci.yml"])), \
             patch.object(Path, "glob", return_value=iter(["test_foo.py"])):
            roadmap = collect_evidence("/fake/repo")

        results = evaluate_roadmap(roadmap)
        output = RENDERERS["json"](results, roadmap_name=roadmap["roadmap_name"])
        parsed = json_mod.loads(output)
        self.assertIn("checkpoints", parsed)
        self.assertIn("next", parsed)

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
            cwd=REPO_ROOT,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        parsed = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(1, parsed["snapshot_schema_version"])
        self.assertTrue(parsed["roadmap_name"].startswith("Git Collector:"))


if __name__ == "__main__":
    unittest.main()
