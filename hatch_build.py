"""Hatchling build hook: stamp the wheel with the source commit + build time.

Runs at `uv build` / `hatch build` / `uv tool install`. Writes a
`_build_info.py` to a temp path and force-includes it into the artifact
as `symbolon/_build_info.py`. Using a tempfile (rather than writing into
the source tree) keeps the source tree clean and sidesteps hatchling's
VCS filter, which would otherwise drop the gitignored file.

At runtime the package imports `symbolon._build_info` if present; for
editable / source-clone installs (where this hook hasn't run), it falls
back to `git rev-parse` against the working tree. See
`symbolon/about.py`.
"""
from __future__ import annotations

import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class BuildInfoHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:  # noqa: ARG002
        del version
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip() or "unknown"
        except (subprocess.CalledProcessError, FileNotFoundError):
            commit = "unknown"

        built_at = datetime.now(UTC).isoformat(timespec="seconds")
        body = f'COMMIT = "{commit}"\nBUILT_AT = "{built_at}"\n'

        tmp = Path(tempfile.mkdtemp(prefix="symbolon-buildinfo-")) / "_build_info.py"
        tmp.write_text(body, encoding="utf-8")
        build_data.setdefault("force_include", {})[str(tmp)] = "symbolon/_build_info.py"
