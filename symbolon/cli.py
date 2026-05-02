"""Symbolon CLI."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from .db import default_db_path, init_db, model_breakdown, overview_totals
from .pricing import cost_for, load_pricing
from .scanner import scan_dir
from .tips import all_tips
from .util import today_range_local

RAYCAST_OWNER_MARKERS = (
    "@raycast.packageName Symbolon",
    # Legacy from before the rename — keep so users upgrading from
    # token-dashboard get their old scripts cleaned up on `--install`.
    "@raycast.packageName Token Dashboard",
)
RAYCAST_DEFAULT_DEST = "~/.raycast-scripts"


def _db_path(args) -> str:
    return args.db or os.environ.get("SYMBOLON_DB") or str(default_db_path())


def _projects(args) -> str:
    return (
        args.projects_dir
        or os.environ.get("CLAUDE_PROJECTS_DIR")
        or str(Path.home() / ".claude" / "projects")
    )


def _host_port() -> tuple[str, int]:
    return os.environ.get("HOST", "127.0.0.1"), int(os.environ.get("PORT", "8080"))


def _server_running(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _today_cost_usd(db: str, since: str, until: str) -> float:
    pricing_path = Path(__file__).resolve().parent / "pricing.json"
    pricing = load_pricing(pricing_path)
    total = 0.0
    for m in model_breakdown(db, since, until):
        c = cost_for(m["model"], m, pricing)
        if c["usd"] is not None:
            total += c["usd"]
    return total


def cmd_scan(args):
    db = _db_path(args)
    init_db(db)
    n = scan_dir(_projects(args), db)
    print(
        f"Symbolon: scanned {n['files']} files,"
        f" {n['messages']} messages, {n['tools']} tool calls"
    )


def cmd_today(args):
    db = _db_path(args)
    init_db(db)
    s, e, day = today_range_local()
    t = overview_totals(db, since=s, until=e)
    print(f"Symbolon — {day}")
    print(f"  sessions: {t['sessions']}    turns: {t['turns']}")
    print(f"  input:    {t['input_tokens']:>12,}    output: {t['output_tokens']:>12,}")
    cache_cr = t["cache_create_5m_tokens"] + t["cache_create_1h_tokens"]
    print(f"  cache rd: {t['cache_read_tokens']:>12,}    cache cr: {cache_cr:>12,}")


def cmd_stats(args):
    db = _db_path(args)
    init_db(db)
    t = overview_totals(db)
    print("Symbolon — all time")
    print(f"  sessions: {t['sessions']}    turns: {t['turns']}")
    print(f"  input:    {t['input_tokens']:>12,}    output: {t['output_tokens']:>12,}")


def cmd_tips(args):
    db = _db_path(args)
    init_db(db)
    tips = all_tips(db)
    if not tips:
        print("Symbolon: no suggestions")
        return
    for tip in tips:
        print(f"[{tip['category']}] {tip['title']}")
        print(f"  {tip['body']}\n")


def _spawn_daemon() -> None:
    """Start the dashboard daemon in a fully detached process."""
    cmd = [sys.argv[0], "dashboard", "--no-open"]
    kwargs: dict = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)


def _wait_for_server(host: str, port: int, timeout_s: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _server_running(host, port):
            return True
        time.sleep(0.1)
    return False


def _ensure_running(host: str, port: int) -> bool:
    """Ensure the daemon is up. Spawn it and wait if not. Return True on success."""
    if _server_running(host, port):
        return True
    _spawn_daemon()
    return _wait_for_server(host, port)


def cmd_start(args):
    host, port = _host_port()
    if _server_running(host, port):
        print(f"Symbolon: already running at http://{host}:{port}/")
        return
    print("Symbolon: starting daemon…")
    if not _ensure_running(host, port):
        print("Symbolon: failed to start within 5s", file=sys.stderr)
        sys.exit(1)
    print(f"Symbolon: running at http://{host}:{port}/")


def cmd_status(args):
    db = _db_path(args)
    init_db(db)
    host, port = _host_port()
    running = _server_running(host, port)
    s, e, _day = today_range_local()
    t = overview_totals(db, since=s, until=e)
    cost = _today_cost_usd(db, s, e)
    indicator = "running" if running else "stopped"
    glyph = "●" if running else "○"
    turns = t["turns"] or 0
    sessions = t["sessions"] or 0
    print(
        f"{glyph} {indicator} · today ${cost:.2f}"
        f" · {turns} prompts · {sessions} sessions"
    )


def cmd_stop(args):
    host, port = _host_port()
    url = f"http://{host}:{port}/api/quit"
    req = urllib.request.Request(url, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as r:  # noqa: S310 — localhost only
            json.loads(r.read() or b"{}")
        print("Symbolon: stopped.")
    except (urllib.error.URLError, ConnectionError, OSError):
        print("Symbolon: not running.")
        sys.exit(1)


def _integration_paths() -> dict[str, Path]:
    """Resolve bundled integration paths, with a clone-tree fallback for dev."""
    bundled = Path(__file__).resolve().parent / "_resources"
    if bundled.is_dir():
        return {"raycast": bundled / "raycast", "nu": bundled / "nu" / "td"}
    repo = Path(__file__).resolve().parent.parent
    return {"raycast": repo / "raycast", "nu": repo / "nu" / "td"}


def _install_raycast_scripts(src: Path) -> Path:
    dest = Path(RAYCAST_DEFAULT_DEST).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    variant = "ps1" if sys.platform == "win32" else "sh"
    variant_dir = src / variant
    if not variant_dir.is_dir():
        # Backwards-compat: pre-platform-split layout had .sh files at top.
        variant_dir = src
    for f in dest.iterdir():
        if f.is_file() and f.suffix in (".sh", ".ps1"):
            try:
                content = f.read_text(errors="ignore")
                if any(m in content for m in RAYCAST_OWNER_MARKERS):
                    f.unlink()
            except OSError:
                pass
    for script in variant_dir.iterdir():
        if script.is_file() and script.suffix in (".sh", ".ps1"):
            target = dest / script.name
            shutil.copy2(script, target)
            if sys.platform != "win32":
                target.chmod(0o755)
    return dest


def _pricing_path() -> Path:
    return Path(__file__).resolve().parent / "pricing.json"


def cmd_pricing_sync(args):
    from .pricing_sync import sync_from_litellm

    dest = _pricing_path()
    print("Symbolon: fetching pricing from LiteLLM…")
    try:
        new_pricing = sync_from_litellm(dest)
    except Exception as e:
        print(f"Symbolon: pricing sync failed: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Symbolon: updated {dest}")
    print(f"  models: {len(new_pricing['models'])}")
    print(f"  tiers:  {sorted(new_pricing['tier_fallback'])}")


def _maybe_auto_sync_pricing(skip: bool = False) -> None:
    """Refresh pricing.json on startup if it's older than a week."""
    if skip:
        return
    from .pricing_sync import is_stale, sync_from_litellm

    dest = _pricing_path()
    if not is_stale(dest):
        return
    print("Symbolon: pricing.json is stale, refreshing from LiteLLM…")
    try:
        sync_from_litellm(dest)
    except Exception as e:
        print(
            f"Symbolon: pricing auto-sync failed (continuing with cached): {e}",
            file=sys.stderr,
        )


def cmd_integrations(args):
    paths = _integration_paths()
    missing = [k for k, p in paths.items() if not p.is_dir()]
    if missing:
        print(
            f"Symbolon: integration files for {missing} not found.\n"
            "  Reinstall with `uv tool install --reinstall symbolon`.",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.install:
        if args.kind not in (None, "raycast"):
            print("--install only applies to raycast integrations", file=sys.stderr)
            sys.exit(2)
        dest = _install_raycast_scripts(paths["raycast"])
        print(f"Installed Symbolon Raycast scripts to {dest}")
        print(
            "Register the directory in Raycast: "
            "Settings → Extensions → Scripts → Add Directories"
        )
        return
    if args.kind:
        print(paths[args.kind])
        return
    for name, p in paths.items():
        print(f"{name}: {p}")


def cmd_open(args):
    host, port = _host_port()
    url = f"http://{host}:{port}/"
    if not _server_running(host, port):
        print("Symbolon: starting daemon…")
        if not _ensure_running(host, port):
            print("Symbolon: failed to start within 5s", file=sys.stderr)
            sys.exit(1)
    webbrowser.open(url)
    print(f"Opened {url}")


def cmd_dashboard(args):
    db = _db_path(args)
    init_db(db)
    _maybe_auto_sync_pricing(skip=args.no_auto_sync)
    if not args.no_scan:
        scan_dir(_projects(args), db)
    from .server import run

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    url = f"http://{host}:{port}/"
    if not args.no_open:
        webbrowser.open(url)
    print(f"Symbolon listening on {url}  (Ctrl+C to stop)")
    run(host, port, db, _projects(args))
    print("Symbolon stopped.")


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", help="SQLite path (default ~/.claude/symbolon.db)")
    common.add_argument("--projects-dir", help="JSONL root (default ~/.claude/projects)")

    p = argparse.ArgumentParser(
        prog="symbolon", description="Local Claude Code usage dashboard", parents=[common]
    )
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("scan",   parents=[common]).set_defaults(func=cmd_scan)
    sub.add_parser("today",  parents=[common]).set_defaults(func=cmd_today)
    sub.add_parser("stats",  parents=[common]).set_defaults(func=cmd_stats)
    sub.add_parser("tips",   parents=[common]).set_defaults(func=cmd_tips)
    sub.add_parser("status", parents=[common]).set_defaults(func=cmd_status)
    sub.add_parser("start",  parents=[common]).set_defaults(func=cmd_start)
    sub.add_parser("stop",   parents=[common]).set_defaults(func=cmd_stop)
    sub.add_parser("open",   parents=[common]).set_defaults(func=cmd_open)
    integ = sub.add_parser(
        "integrations", parents=[common],
        help="Print the path to bundled integration files (Raycast, nushell)",
    )
    integ.add_argument("kind", nargs="?", choices=["raycast", "nu"],
                       help="If given, print only that path; otherwise print all.")
    integ.add_argument("--install", action="store_true",
                       help=f"Copy bundled Raycast scripts to {RAYCAST_DEFAULT_DEST}")
    integ.set_defaults(func=cmd_integrations)
    pricing = sub.add_parser(
        "pricing", parents=[common],
        help="Pricing-related commands (e.g. `pricing sync`)",
    )
    pricing_sub = pricing.add_subparsers(dest="pricing_cmd")
    pricing_sub.add_parser(
        "sync", parents=[common],
        help="Refresh pricing.json from LiteLLM's community model registry.",
    ).set_defaults(func=cmd_pricing_sync)
    d = sub.add_parser("dashboard", parents=[common])
    d.add_argument("--no-scan", action="store_true")
    d.add_argument("--no-open", action="store_true")
    d.add_argument("--no-auto-sync", action="store_true",
                   help="Skip the weekly pricing.json refresh from LiteLLM.")
    d.set_defaults(func=cmd_dashboard)
    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
