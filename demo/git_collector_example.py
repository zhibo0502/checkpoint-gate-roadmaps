"""Minimal git-backed evidence collector.

Demonstrates the 'repo-backed collector' pattern from SKILL.md:
reads real git state and feeds it into the same evaluator used by
the static-fixture demo.

Usage:
    python demo/git_collector_example.py [--repo /path/to/repo]
"""

import argparse
import subprocess
import sys
from pathlib import Path

from demo.check_demo_roadmap import evaluate_roadmap, render_report


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

    # Evidence: has at least one commit
    rc, log_output = run_git(["log", "--oneline", "-1"], cwd=repo)
    has_commits = rc == 0 and bool(log_output)

    # Evidence: CHANGELOG.md exists
    has_changelog = (repo / "CHANGELOG.md").is_file()

    # Evidence: README.md exists
    has_readme = (repo / "README.md").is_file()

    # Gate: worktree is clean
    rc, status_output = run_git(["status", "--porcelain"], cwd=repo)
    worktree_clean = rc == 0 and status_output == ""

    # Gate: on main or master branch
    rc, branch = run_git(["branch", "--show-current"], cwd=repo)
    on_main = branch in ("main", "master")

    return {
        "roadmap_name": f"Git Collector: {repo.name}",
        "checkpoints": [
            {
                "key": "INIT",
                "name": "Repository initialized",
                "done_evidence": [
                    {"label": "has_commits", "found": has_commits},
                    {"label": "has_readme", "found": has_readme},
                ],
                "gate": [
                    {"label": "on_main_branch", "passed": on_main},
                ],
            },
            {
                "key": "DOCS",
                "name": "Documentation present",
                "done_evidence": [
                    {"label": "has_changelog", "found": has_changelog},
                    {"label": "has_readme", "found": has_readme},
                ],
                "gate": [
                    {"label": "worktree_clean", "passed": worktree_clean},
                ],
            },
            {
                "key": "CLEAN",
                "name": "Release ready",
                "done_evidence": [
                    {"label": "has_commits", "found": has_commits},
                    {"label": "has_changelog", "found": has_changelog},
                ],
                "gate": [
                    {"label": "worktree_clean", "passed": worktree_clean},
                    {"label": "on_main_branch", "passed": on_main},
                ],
            },
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Collect checkpoint evidence from a real git repository."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to git repository (default: current directory).",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    rc, _ = run_git(["rev-parse", "--git-dir"], cwd=repo_path)
    if rc != 0:
        print(f"Error: {repo_path} is not a git repository.", file=sys.stderr)
        sys.exit(1)

    roadmap = collect_evidence(repo_path)
    results = evaluate_roadmap(roadmap)
    print(render_report(results, roadmap_name=roadmap["roadmap_name"]))


if __name__ == "__main__":
    main()
