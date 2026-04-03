import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from demo.git_collector_example import collect_evidence


def make_run_result(returncode=0, stdout=""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    return result


class GitCollectorTests(unittest.TestCase):
    @patch("demo.git_collector_example.subprocess.run")
    @patch("demo.git_collector_example.Path.is_file")
    def test_clean_repo_all_gates_pass(self, mock_is_file, mock_run):
        mock_is_file.return_value = True
        mock_run.side_effect = [
            make_run_result(0, "abc1234 initial commit"),  # git log
            make_run_result(0, ""),                          # git status --porcelain
            make_run_result(0, "main"),                      # git branch --show-current
        ]

        roadmap = collect_evidence("/fake/repo")

        self.assertEqual(3, len(roadmap["checkpoints"]))
        # All evidence found and all gates should pass
        for cp in roadmap["checkpoints"]:
            for ev in cp["done_evidence"]:
                self.assertTrue(ev["found"], f"{cp['key']}: {ev['label']} should be found")
            for gate in cp["gate"]:
                self.assertTrue(gate["passed"], f"{cp['key']}: {gate['label']} should pass")

    @patch("demo.git_collector_example.subprocess.run")
    @patch("demo.git_collector_example.Path.is_file")
    def test_dirty_worktree_blocks_advance(self, mock_is_file, mock_run):
        mock_is_file.return_value = True
        mock_run.side_effect = [
            make_run_result(0, "abc1234 initial commit"),  # git log
            make_run_result(0, " M README.md"),             # git status (dirty)
            make_run_result(0, "main"),                      # git branch
        ]

        roadmap = collect_evidence("/fake/repo")

        docs_cp = roadmap["checkpoints"][1]
        self.assertFalse(docs_cp["gate"][0]["passed"])  # worktree_clean = False

    @patch("demo.git_collector_example.subprocess.run")
    @patch("demo.git_collector_example.Path.is_file")
    def test_missing_changelog_partial_evidence(self, mock_is_file, mock_run):
        def is_file_side_effect(self_path=None):
            # Path.is_file is called on specific paths
            path_str = str(self_path) if self_path else ""
            return "CHANGELOG" not in path_str

        # We need to mock at instance level
        mock_is_file.side_effect = lambda: True  # default

        mock_run.side_effect = [
            make_run_result(0, "abc1234 initial commit"),
            make_run_result(0, ""),
            make_run_result(0, "main"),
        ]

        # Patch Path.is_file more precisely
        original_is_file = Path.is_file
        def patched_is_file(p):
            if "CHANGELOG" in str(p):
                return False
            return True

        with patch.object(Path, "is_file", patched_is_file):
            roadmap = collect_evidence("/fake/repo")

        docs_cp = roadmap["checkpoints"][1]
        changelog_ev = next(e for e in docs_cp["done_evidence"] if e["label"] == "has_changelog")
        self.assertFalse(changelog_ev["found"])


if __name__ == "__main__":
    unittest.main()
