#!/usr/bin/env python3
"""Cursor stop hook: run ruff on agent-edited Python files in git diff."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def changed_py_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "*.py", "src", "tests"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return files[:50]


def run_ruff_on(files: list[str], root: Path) -> None:
    if shutil.which("uv") is None:
        return
    print("Running ruff on agent-edited Python files...", file=sys.stderr)
    subprocess.run(
        ["uv", "run", "ruff", "check", "--fix", *files],
        cwd=root,
        stderr=sys.stderr,
        check=False,
    )
    subprocess.run(
        ["uv", "run", "ruff", "format", *files],
        cwd=root,
        stderr=sys.stderr,
        check=False,
    )
    subprocess.run(
        ["uv", "run", "ruff", "check", *files],
        cwd=root,
        stderr=sys.stderr,
        check=False,
    )


def main() -> int:
    root = repo_root()
    if shutil.which("uv") is None:
        return 0

    changed = changed_py_files(root)
    if not changed:
        return 0

    run_ruff_on(changed, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
