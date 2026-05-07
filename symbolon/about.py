"""Build provenance for the About tab.

At build time, `hatch_build.py` writes a `_build_info` module with the source
commit and build timestamp. At runtime that module is imported when present
(installed wheels). For editable / source-clone installs, fall back to a
`git rev-parse` against the working tree.
"""
from __future__ import annotations

import importlib
import subprocess
from pathlib import Path

from . import __version__


def _git_short_sha() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return out or None


def build_info() -> dict[str, str | None]:
    commit: str | None
    built_at: str | None
    try:
        bi = importlib.import_module("symbolon._build_info")
        commit = bi.COMMIT
        built_at = bi.BUILT_AT
    except ImportError:
        commit = _git_short_sha()
        built_at = None
    return {
        "version": __version__,
        "commit": commit,
        "built_at": built_at,
    }
