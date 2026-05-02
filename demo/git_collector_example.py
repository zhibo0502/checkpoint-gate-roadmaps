"""Git-backed evidence collector.

Demonstrates the 'repo-backed collector' pattern from SKILL.md:
reads real git state and feeds it into the same evaluator used by
the static-fixture demo.

Usage:
    python -m demo.git_collector_example [--repo /path/to/repo] [--format text|json|markdown]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from demo.check_demo_roadmap import (
    build_snapshot,
    evaluate_roadmap,
    RENDERERS,
    write_json_snapshot,
)


def run_git(args, cwd):
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.returncode, result.stdout.strip()


def collect_evidence(repo_path):
    """Collect evidence from a real git repository.

    Returns a roadmap dict compatible with evaluate_roadmap().
    """
    repo = Path(repo_path).resolve()

    # --- Evidence collection ---

    # Has at least one commit
    rc, log_output = run_git(["log", "--oneline", "-1"], cwd=repo)
    has_commits = rc == 0 and bool(log_output)

    # CHANGELOG.md exists
    has_changelog = (repo / "CHANGELOG.md").is_file()

    # README.md exists
    has_readme = (repo / "README.md").is_file()

    # LICENSE file exists
    has_license = (repo / "LICENSE").is_file()

    # Has CI configuration
    has_ci = (
        (repo / ".github" / "workflows").is_dir()
        and any((repo / ".github" / "workflows").iterdir())
    )

    # Has tests directory with test files
    tests_dir = repo / "tests"
    has_tests = tests_dir.is_dir() and any(tests_dir.glob("test_*.py"))

    # Has git tags (releases)
    rc, tags_output = run_git(["tag", "--list"], cwd=repo)
    has_tags = rc == 0 and bool(tags_output)

    # Recent commit within last 30 days
    rc, recent = run_git(
        ["log", "-1", "--since=30 days ago", "--oneline"], cwd=repo
    )
    has_recent_activity = rc == 0 and bool(recent)

    # --- Gate collection ---

    # Worktree is clean
    rc, status_output = run_git(["status", "--porcelain"], cwd=repo)
    worktree_clean = rc == 0 and status_output == ""

    # On main or master branch
    rc, branch = run_git(["branch", "--show-current"], cwd=repo)
    on_main = branch in ("main", "master")

    # No untracked files
    rc, untracked = run_git(
        ["ls-files", "--others", "--exclude-standard"], cwd=repo
    )
    no_untracked = rc == 0 and untracked == ""

    return {
        "roadmap_name": f"Git Collector: {repo.name}",
        "checkpoints": [
            {
                "key": "INIT",
                "name": "Repository initialized",
                "done_evidence": [
                    {"label": "has_commits", "found": has_commits},
                    {"label": "has_readme", "found": has_readme},
                    {"label": "has_license", "found": has_license},
                ],
                "gate": [
                    {"label": "on_main_branch", "passed": on_main},
                ],
            },
            {
                "key": "DOCS",
                "name": "Documentation complete",
                "done_evidence": [
                    {"label": "has_changelog", "found": has_changelog},
                    {"label": "has_readme", "found": has_readme},
                    {"label": "has_license", "found": has_license},
                ],
                "gate": [
                    {"label": "worktree_clean", "passed": worktree_clean},
                ],
            },
            {
                "key": "TEST",
                "name": "Testing infrastructure",
                "done_evidence": [
                    {"label": "has_tests", "found": has_tests},
                    {"label": "has_ci", "found": has_ci},
                ],
                "gate": [
                    {"label": "worktree_clean", "passed": worktree_clean},
                    {"label": "on_main_branch", "passed": on_main},
                ],
            },
            {
                "key": "RELEASE",
                "name": "Release ready",
                "done_evidence": [
                    {"label": "has_tags", "found": has_tags},
                    {"label": "has_changelog", "found": has_changelog},
                    {"label": "has_ci", "found": has_ci},
                ],
                "gate": [
                    {"label": "worktree_clean", "passed": worktree_clean},
                    {"label": "no_untracked_files", "passed": no_untracked},
                    {"label": "on_main_branch", "passed": on_main},
                ],
            },
            {
                "key": "ACTIVE",
                "name": "Actively maintained",
                "done_evidence": [
                    {"label": "has_recent_activity", "found": has_recent_activity},
                    {"label": "has_tests", "found": has_tests},
                    {"label": "has_ci", "found": has_ci},
                ],
                "gate": [
                    {"label": "worktree_clean", "passed": worktree_clean},
                ],
            },
        ],
    }


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


def main():
    parser = argparse.ArgumentParser(
        description="Collect checkpoint evidence from a real git repository."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to git repository (default: current directory).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--json-out",
        help="Write the machine-readable audit snapshot JSON to a file.",
    )
    parser.add_argument(
        "--rules",
        help="Path to collector rules JSON. When omitted, use the built-in demo collector.",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    rc, _ = run_git(["rev-parse", "--git-dir"], cwd=repo_path)
    if rc != 0:
        print(f"Error: {repo_path} is not a git repository.", file=sys.stderr)
        sys.exit(1)

    if args.rules:
        rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
        roadmap = collect_configured_evidence(repo_path, rules)
    else:
        roadmap = collect_evidence(repo_path)
    results = evaluate_roadmap(roadmap)
    if args.json_out:
        write_json_snapshot(
            build_snapshot(results, roadmap_name=roadmap["roadmap_name"]),
            args.json_out,
        )
    renderer = RENDERERS[args.format]
    print(renderer(results, roadmap_name=roadmap["roadmap_name"]))


if __name__ == "__main__":
    main()
