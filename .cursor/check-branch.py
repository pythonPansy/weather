#!/usr/bin/env python3
"""Pre-commit hook: enforce feature branch workflow.

Prevents direct commits to main branch.
All changes must be made via feature branches and submitted as PRs.
"""

from __future__ import annotations

import subprocess


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def is_feature_branch(branch: str) -> bool:
    """Check if branch name follows feature branch conventions."""
    allowed_patterns = [
        "feature/",
        "fix/",
        "cursor/",
        "bugfix/",
        "hotfix/",
        "refactor/",
        "docs/",
        "test/",
        "chore/",
    ]

    return any(branch.startswith(pattern) for pattern in allowed_patterns)


def main() -> int:
    """Check if commit is allowed on current branch."""
    current_branch = get_current_branch()

    if not current_branch:
        return 0

    if current_branch == "main":
        print("\nERROR: Direct commits to 'main' branch are not allowed!")
        print("\nPlease create a feature branch:")
        print("  git checkout -b feature/your-feature-name")
        print("  git checkout -b fix/your-bug-fix")
        print("\nMake your changes, commit, push, and create a PR.")
        print("\nSee CONTRIBUTING.md for workflow details.")
        print("\nTo bypass this check (emergency only): git commit --no-verify")
        return 1

    if is_feature_branch(current_branch):
        return 0

    print(f"\nWARNING: You are committing to '{current_branch}'")
    print("Consider using a feature branch for better workflow.")
    print("Allowed patterns: feature/*, fix/*, cursor/*, etc.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
