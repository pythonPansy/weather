#!/usr/bin/env python3
"""Cursor afterFileEdit hook: auto-fix ruff on edited Python files."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def in_scope(file_path: str) -> bool:
    if not file_path.endswith(".py"):
        return False
    normalized = file_path.replace("\\", "/")
    return normalized.startswith(("src/", "tests/"))


def run_ruff(file_path: str, root: Path) -> None:
    if shutil.which("uv") is None:
        return
    rel = Path(file_path)
    if not rel.is_absolute():
        rel = root / rel
    subprocess.run(
        ["uv", "run", "ruff", "check", "--fix", str(rel)],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    subprocess.run(
        ["uv", "run", "ruff", "format", str(rel)],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    file_path = payload.get("file_path") or payload.get("path") or ""
    if not file_path or not in_scope(file_path):
        return 0

    run_ruff(file_path, repo_root())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
