import argparse
import json
import sys
from pathlib import Path


DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample-roadmap.json"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.json"
SNAPSHOT_SCHEMA_VERSION = 1


def load_roadmap(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: fixture not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def validate_roadmap(roadmap):
    """Validate roadmap against JSON Schema. Requires jsonschema package."""
    try:
        import jsonschema
    except ImportError:
        print("Error: --validate requires the jsonschema package: pip install jsonschema", file=sys.stderr)
        sys.exit(1)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=roadmap, schema=schema)


def evaluate_checkpoint(checkpoint):
    for field in ("key", "name"):
        if field not in checkpoint:
            raise ValueError(f"checkpoint missing required field: {field}")

    found_evidence = [
        proof["label"] for proof in checkpoint.get("done_evidence", []) if proof.get("found")
    ]
    missing_evidence = [
        proof["label"] for proof in checkpoint.get("done_evidence", []) if not proof.get("found")
    ]
    passed_gate = [gate["label"] for gate in checkpoint.get("gate", []) if gate.get("passed")]
    missing_gate = [gate["label"] for gate in checkpoint.get("gate", []) if not gate.get("passed")]

    if not missing_evidence:
        status = "complete"
    elif found_evidence:
        status = "in_progress"
    else:
        status = "pending"
    advance_ready = "yes" if status == "complete" and not missing_gate else "no"
    evidence = found_evidence + passed_gate
    missing = missing_evidence + missing_gate

    return {
        "key": checkpoint["key"],
        "name": checkpoint["name"],
        "status": status,
        "advance_ready": advance_ready,
        "evidence": evidence,
        "missing": missing,
    }


def evaluate_roadmap(roadmap):
    return [evaluate_checkpoint(checkpoint) for checkpoint in roadmap.get("checkpoints", [])]


def next_incomplete(results):
    for result in results:
        if result["status"] != "complete" or result["advance_ready"] != "yes":
            return result
    return None


def build_snapshot(results, roadmap_name=None):
    current = next_incomplete(results)
    if current is None:
        next_value = {
            "key": "none",
            "name": "all checkpoints are complete",
            "status": "complete",
            "advance_ready": "yes",
            "evidence": [],
            "missing": [],
        }
    else:
        next_value = dict(current)

    return {
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "roadmap_name": roadmap_name,
        "checkpoints": [dict(result) for result in results],
        "next": None if current is None else current["key"],
        "NEXT": next_value,
    }


def write_json_snapshot(snapshot, path):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(f".{output_path.name}.tmp")
    temp_path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(output_path)


def render_text(results, roadmap_name=None):
    lines = []
    if roadmap_name:
        lines.append(f"ROADMAP | {roadmap_name}")

    for result in results:
        evidence = ",".join(result["evidence"]) if result["evidence"] else "-"
        missing = ",".join(result["missing"]) if result["missing"] else "-"
        lines.append(
            "CHECKPOINT | {key} | {name} | status={status} | advance_ready={advance_ready} | "
            "evidence={evidence} | missing={missing}".format(
                key=result["key"],
                name=result["name"],
                status=result["status"],
                advance_ready=result["advance_ready"],
                evidence=evidence,
                missing=missing,
            )
        )

    current = next_incomplete(results)
    if current is None:
        lines.append("NEXT | none | all checkpoints are complete")
    else:
        lines.append(f"NEXT | {current['key']} | {current['name']}")

    return "\n".join(lines)


# Keep backward-compatible alias
render_report = render_text


def render_json(results, roadmap_name=None):
    return json.dumps(build_snapshot(results, roadmap_name=roadmap_name), indent=2)


def render_markdown(results, roadmap_name=None):
    lines = []
    if roadmap_name:
        lines.append(f"# {roadmap_name}\n")

    lines.append("| Key | Name | Status | Advance Ready | Evidence | Missing |")
    lines.append("|-----|------|--------|---------------|----------|---------|")
    for r in results:
        evidence = ", ".join(r["evidence"]) if r["evidence"] else "-"
        missing = ", ".join(r["missing"]) if r["missing"] else "-"
        lines.append(f"| {r['key']} | {r['name']} | {r['status']} | {r['advance_ready']} | {evidence} | {missing} |")

    lines.append("")
    current = next_incomplete(results)
    if current is None:
        lines.append("**NEXT**: none — all checkpoints are complete")
    else:
        lines.append(f"**NEXT**: `{current['key']}` — {current['name']}")

    return "\n".join(lines)


RENDERERS = {
    "text": render_text,
    "json": render_json,
    "markdown": render_markdown,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a self-contained checkpoint-gate roadmap demo."
    )
    parser.add_argument(
        "--fixture",
        default=str(DEFAULT_FIXTURE_PATH),
        help="Path to a roadmap fixture JSON file.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate fixture against JSON Schema before evaluating.",
    )
    parser.add_argument(
        "--json-out",
        help="Write the machine-readable audit snapshot JSON to a file.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    roadmap = load_roadmap(args.fixture)
    if args.validate:
        try:
            validate_roadmap(roadmap)
        except Exception as exc:
            print(f"Schema validation failed: {exc}", file=sys.stderr)
            sys.exit(1)
    results = evaluate_roadmap(roadmap)
    roadmap_name = roadmap.get("roadmap_name")
    if args.json_out:
        write_json_snapshot(
            build_snapshot(results, roadmap_name=roadmap_name),
            args.json_out,
        )
    renderer = RENDERERS[args.format]
    print(renderer(results, roadmap_name=roadmap_name))


if __name__ == "__main__":
    main()
