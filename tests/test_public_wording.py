import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN_PATH_PARTS = {"charlotte"}
FORBIDDEN_CONTENT = (
    "Charlotte",
    "charlotte",
    "owner-worktree",
    "integration-pack",
    "Charlotte-only",
)
TEXT_SUFFIXES = {".md", ".svg", ".yaml", ".yml", ".txt"}


class PublicWordingTests(unittest.TestCase):
    def iter_repo_files(self):
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or ".git" in path.parts:
                continue
            yield path

    def test_public_file_paths_are_generic(self):
        flagged = []
        for path in self.iter_repo_files():
            relative_parts = [part.lower() for part in path.relative_to(REPO_ROOT).parts]
            if any(token in part for part in relative_parts for token in FORBIDDEN_PATH_PARTS):
                flagged.append(str(path.relative_to(REPO_ROOT)))

        self.assertEqual([], flagged)

    def test_public_docs_and_assets_use_generic_wording(self):
        flagged = []
        for path in self.iter_repo_files():
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue

            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN_CONTENT:
                if token in text:
                    flagged.append(f"{path.relative_to(REPO_ROOT)} -> {token}")

        self.assertEqual([], flagged)


if __name__ == "__main__":
    unittest.main()
