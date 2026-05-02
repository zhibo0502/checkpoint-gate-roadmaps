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
