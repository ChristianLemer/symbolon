"""Integration tests for the nushell module under nu/td/.

Three layers:

1. Static check on the source — runs always, catches regressions like
   `http post {}` instead of `http post ""` (nu 0.112+ rejects record bodies).
2. Subprocess invocation of the nu test suite — skipped cleanly if
   nushell is not on PATH, so the Python-only CI path stays green.
3. Real `/api/quit` cycle — spawns a daemon on a free port and asserts
   that POST /api/quit causes the process to actually exit. Catches
   behavioural regressions in the shutdown path.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_DIR = ROOT / "nu" / "td"
NU_TEST = MOD_DIR / "tests" / "test_commands.nu"
NU = shutil.which("nu")
DASHBOARD_BIN = ROOT / ".venv" / "bin" / "symbolon"


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_until(predicate, timeout: float = 5.0, interval: float = 0.1) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


class NuModuleStaticTests(unittest.TestCase):
    def test_quit_uses_string_body_not_record(self):
        src = (MOD_DIR / "mod.nu").read_text()
        self.assertIn(
            'http post (url "/api/quit") ""',
            src,
            "td quit must pass an empty string body, not an empty record",
        )
        self.assertNotIn(
            'http post (url "/api/quit") {}',
            src,
            "td quit must not pass an empty record body (nu 0.112+ rejects it)",
        )


@unittest.skipIf(NU is None, "nushell not installed")
class NuTestSuiteRuns(unittest.TestCase):
    def test_module_loads_and_self_tests_pass(self):
        assert NU is not None  # narrow Optional[str] for type checker
        result = subprocess.run(
            [NU, str(NU_TEST)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(ROOT),
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"nu test suite failed:\n--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}",
        )
        self.assertIn("all nu tests passed.", result.stdout)


def _reachable(base: str) -> bool:
    try:
        urllib.request.urlopen(f"{base}/api/plan", timeout=0.5)
        return True
    except (urllib.error.URLError, ConnectionRefusedError, OSError):
        return False


@unittest.skipIf(
    not DASHBOARD_BIN.exists(),
    f"dashboard binary not found at {DASHBOARD_BIN} (run `uv sync`)",
)
class QuitCycleTest(unittest.TestCase):
    """Spawn a daemon directly via Popen, hit /api/quit, assert it dies."""

    def test_quit_endpoint_terminates_a_directly_spawned_daemon(self):
        port = _free_port()
        env = {**os.environ, "PORT": str(port)}
        proc = subprocess.Popen(
            [str(DASHBOARD_BIN), "dashboard", "--no-open"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            self.assertTrue(
                _wait_until(lambda: _reachable(base)),
                "daemon never came up",
            )
            r = urllib.request.urlopen(
                urllib.request.Request(
                    f"{base}/api/quit", method="POST", data=b""
                ),
                timeout=2,
            )
            self.assertEqual(r.status, 200)
            self.assertTrue(
                _wait_until(lambda: proc.poll() is not None, timeout=5.0),
                "daemon did not exit within 5 s of POST /api/quit",
            )
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=2)


@unittest.skipIf(
    not DASHBOARD_BIN.exists(),
    f"dashboard binary not found at {DASHBOARD_BIN} (run `uv sync`)",
)
@unittest.skipIf(
    sys.platform == "win32",
    "bash/nohup/lsof are Unix-only — this regression test is meaningless on Windows",
)
class BashBackgroundQuitCycleTest(unittest.TestCase):
    """Regression: when bash backgrounds a job with `&` (the pattern used by
    `td start`), it sets SIGINT=SIG_IGN on the child for job-control
    reasons. Without an explicit signal.signal(SIGINT, default_int_handler)
    in run(), POST /api/quit's os.kill(getpid(), SIGINT) is silently dropped
    and the daemon stays alive forever.
    """

    def test_quit_endpoint_terminates_a_bash_backgrounded_daemon(self):
        port = _free_port()
        # Reproduce the exact spawn pattern used by `td start`.
        subprocess.run(
            [
                "bash", "-c",
                f"nohup {DASHBOARD_BIN} dashboard --no-open "
                ">/dev/null 2>&1 &",
            ],
            env={**os.environ, "PORT": str(port)},
            check=True,
            timeout=2,
        )
        base = f"http://127.0.0.1:{port}"
        try:
            self.assertTrue(
                _wait_until(lambda: _reachable(base)),
                "bash-backgrounded daemon never came up",
            )
            r = urllib.request.urlopen(
                urllib.request.Request(
                    f"{base}/api/quit", method="POST", data=b""
                ),
                timeout=2,
            )
            self.assertEqual(r.status, 200)
            self.assertTrue(
                _wait_until(lambda: not _reachable(base), timeout=5.0),
                "daemon survived /api/quit — SIGINT may be inherited as "
                "SIG_IGN from bash job control; ensure run() reinstalls "
                "the default SIGINT handler",
            )
        finally:
            # Best-effort cleanup if the test failed and a daemon is still up.
            if _reachable(base):
                try:
                    pids = subprocess.run(
                        ["lsof", "-ti", f"tcp:{port}"],
                        capture_output=True, text=True, timeout=2,
                        check=False,
                    ).stdout.split()
                    for pid in pids:
                        subprocess.run(
                            ["kill", "-TERM", pid],
                            check=False, timeout=2,
                        )
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()
