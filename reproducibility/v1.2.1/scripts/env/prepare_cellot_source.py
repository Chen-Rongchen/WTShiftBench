#!/usr/bin/env python3
"""Prepare the exact CellOT source checkout used by staged training scripts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPOSITORY = "https://github.com/bunnech/cellot"
REVISION = "522d2b953da8ad244fcf36f64521487fdf763788"
TARGET = Path("/tmp/wtko_cellot_install")


def run(*args: str, capture: bool = False) -> str:
    completed = subprocess.run(
        args,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        env={**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"},
    )
    return completed.stdout.strip() if capture else ""


def main() -> None:
    git_dir = TARGET / ".git"
    if TARGET.exists() and not git_dir.is_dir():
        raise RuntimeError(f"Refusing to replace non-Git path: {TARGET}")

    if not TARGET.exists():
        run("git", "clone", "--filter=blob:none", "--no-checkout", REPOSITORY, str(TARGET))
    else:
        origin = run("git", "-C", str(TARGET), "remote", "get-url", "origin", capture=True)
        if origin.rstrip("/") != REPOSITORY:
            raise RuntimeError(f"Unexpected CellOT origin: {origin}")
        dirty = run("git", "-C", str(TARGET), "status", "--porcelain", capture=True)
        if dirty:
            raise RuntimeError(f"Refusing to overwrite modified CellOT checkout: {TARGET}")

    run("git", "-C", str(TARGET), "fetch", "--depth", "1", "origin", REVISION)
    run("git", "-C", str(TARGET), "checkout", "--detach", REVISION)
    actual = run("git", "-C", str(TARGET), "rev-parse", "HEAD", capture=True)
    if actual != REVISION:
        raise RuntimeError(f"CellOT revision mismatch: expected {REVISION}, got {actual}")
    print(f"CellOT source ready: {TARGET} @ {actual}")


if __name__ == "__main__":
    main()
