import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.proj = self.tmp / "projects"
        (self.proj / "demo").mkdir(parents=True, exist_ok=True)
        with (self.proj / "demo" / "s.jsonl").open("w", encoding="utf-8") as f:
            f.write('{"type":"user","uuid":"u1","sessionId":"s1","timestamp":"2026-04-19T00:00:00Z","isSidechain":false,"message":{"role":"user","content":"hi"}}\n')
            f.write('{"type":"assistant","uuid":"a1","parentUuid":"u1","sessionId":"s1","timestamp":"2026-04-19T00:00:01Z","isSidechain":false,"message":{"model":"claude-haiku-4-5","usage":{"input_tokens":1,"output_tokens":1}}}\n')
        self.db = self.tmp / "t.db"

    def _run(self, *args, port: int | None = None):
        env = {**os.environ, "TOKEN_DASHBOARD_DB": str(self.db)}
        if port is not None:
            env["PORT"] = str(port)
        return subprocess.run(
            [sys.executable, "cli.py", *args],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )

    def test_scan_then_today(self):
        r1 = self._run("scan", "--projects-dir", self.proj)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        self.assertIn("scanned", r1.stdout)
        r2 = self._run("today")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("Token Dashboard", r2.stdout)

    def test_stats(self):
        self._run("scan", "--projects-dir", self.proj)
        r = self._run("stats")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("all time", r.stdout)

    def test_tips_runs_without_data(self):
        r = self._run("tips")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no suggestions", r.stdout)

    def test_status_when_server_down(self):
        self._run("scan", "--projects-dir", self.proj)
        r = self._run("status", port=_free_port())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("stopped", r.stdout)
        self.assertIn("today $", r.stdout)
        self.assertIn("prompts", r.stdout)

    def test_stop_when_server_down(self):
        r = self._run("stop", port=_free_port())
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not running", r.stdout)

    def test_start_command_is_registered(self):
        # `start` is the new auto-start daemon launcher. We don't actually
        # spawn here — just confirm the CLI knows the subcommand.
        r = self._run("start", "--help")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_integrations_lists_all_paths(self):
        r = self._run("integrations")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("raycast:", r.stdout)
        self.assertIn("nu:", r.stdout)

    def test_integrations_specific_kind(self):
        r = self._run("integrations", "raycast")
        self.assertEqual(r.returncode, 0, r.stderr)
        # The path printed must point at a real directory containing our scripts.
        path = Path(r.stdout.strip())
        self.assertTrue(path.is_dir(), f"raycast path not a dir: {path}")
        self.assertTrue((path / "sh" / "token-dashboard-start.sh").is_file())
        self.assertTrue((path / "ps1" / "token-dashboard-start.ps1").is_file())

    def test_integrations_nu_kind(self):
        r = self._run("integrations", "nu")
        self.assertEqual(r.returncode, 0, r.stderr)
        path = Path(r.stdout.strip())
        self.assertTrue(path.is_dir(), f"nu path not a dir: {path}")
        self.assertTrue((path / "mod.nu").is_file())


if __name__ == "__main__":
    unittest.main()
