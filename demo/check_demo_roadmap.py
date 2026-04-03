import argparse
import json
from pathlib import Path


DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample-roadmap.json"


def load_roadmap(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_checkpoint(checkpoint):
    found_evidence = [
        proof["label"] for proof in checkpoint.get("done_evidence", []) if proof.get("found")
    ]
    missing_evidence = [
        proof["label"] for proof in checkpoint.get("done_evidence", []) if not proof.get("found")
    ]
    passed_gate = [gate["label"] for gate in checkpoint.get("gate", []) if gate.get("passed")]
    missing_gate = [gate["label"] for gate in checkpoint.get("gate", []) if not gate.get("passed")]

    status = "complete" if not missing_evidence else "pending"
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


def render_report(results, roadmap_name=None):
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a self-contained checkpoint-gate roadmap demo."
    )
    parser.add_argument(
        "--fixture",
        default=str(DEFAULT_FIXTURE_PATH),
        help="Path to a roadmap fixture JSON file.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    roadmap = load_roadmap(args.fixture)
    results = evaluate_roadmap(roadmap)
    print(render_report(results, roadmap_name=roadmap.get("roadmap_name")))


if __name__ == "__main__":
    main()
