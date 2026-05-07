"""HTTP server: static frontend + JSON endpoints + SSE diff stream."""
from __future__ import annotations

import http.server
import json
import mimetypes
import os
import queue
import signal
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .about import build_info
from .db import (
    daily_token_breakdown,
    expensive_prompts,
    model_breakdown,
    overview_totals,
    project_summary,
    recent_sessions,
    session_turns,
    skill_breakdown,
    tool_token_breakdown,
)
from .pricing import cost_for, get_plan, load_pricing, set_plan
from .scanner import scan_dir
from .skills import cached_catalog
from .tips import all_tips, dismiss_tip
from .util import DEFAULT_DAY_STARTS_AT_HOUR, today_range_local

WEB_ROOT = Path(__file__).resolve().parent / "web"
PRICING_JSON = Path(__file__).resolve().parent / "pricing.json"

EVENTS: queue.Queue[dict] = queue.Queue()
_heartbeat: dict = {"at": None}  # None = no client has connected yet

MAX_POST_BYTES = 1_000_000  # 1 MB — we only accept tiny JSON bodies (plan, tip key)
MAX_LIMIT = 1000


def _send_json(handler, obj, status: int = 200) -> None:
    body = json.dumps(obj, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _send_error(handler, status: int, msg: str) -> None:
    _send_json(handler, {"error": msg}, status=status)


def _clamp_limit(raw, default: int) -> int:
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(v, MAX_LIMIT))


def _serve_static(handler, rel: str) -> None:
    rel = rel.lstrip("/")
    p = (WEB_ROOT / rel).resolve()
    if not str(p).startswith(str(WEB_ROOT.resolve())) or not p.is_file():
        handler.send_response(404)
        handler.end_headers()
        return
    body = p.read_bytes()
    ctype, _ = mimetypes.guess_type(str(p))
    handler.send_response(200)
    handler.send_header("Content-Type", ctype or "application/octet-stream")
    handler.send_header("Content-Length", str(len(body)))
    # Force revalidation so the SPA picks up new bundles after a reinstall.
    # Without this the browser may keep serving stale app.js even on reload,
    # which silently breaks features added in the new build.
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    handler.wfile.write(body)


def build_handler(db_path: str, projects_dir: str):
    pricing = load_pricing(PRICING_JSON)

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            pass

        def do_HEAD(self):
            return self.do_GET()

        def do_GET(self):
            url = urlparse(self.path)
            qs = parse_qs(url.query or "")
            path = url.path
            since = qs.get("since", [None])[0]
            until = qs.get("until", [None])[0]
            if path in ("/", "/index.html"):
                return _serve_static(self, "index.html")
            if path.startswith("/web/"):
                return _serve_static(self, path[5:])
            if path == "/api/overview":
                totals = overview_totals(db_path, since, until)
                cost_usd = 0.0
                for m in model_breakdown(db_path, since, until):
                    c = cost_for(m["model"], m, pricing)
                    if c["usd"] is not None:
                        cost_usd += c["usd"]
                totals["cost_usd"] = round(cost_usd, 4)
                return _send_json(self, totals)
            if path == "/api/prompts":
                limit = _clamp_limit(qs.get("limit", ["50"])[0], 50)
                sort = qs.get("sort", ["tokens"])[0]
                rows = expensive_prompts(db_path, limit=limit, sort=sort)
                for r in rows:
                    c = cost_for(r["model"], {
                        "input_tokens": 0, "output_tokens": 0,
                        "cache_read_tokens": r["cache_read_tokens"],
                        "cache_create_5m_tokens": 0, "cache_create_1h_tokens": 0,
                    }, pricing)
                    r["estimated_cost_usd"] = c["usd"]
                return _send_json(self, rows)
            if path == "/api/projects":
                return _send_json(self, project_summary(db_path, since, until))
            if path == "/api/tools":
                return _send_json(self, tool_token_breakdown(db_path, since, until))
            if path == "/api/sessions":
                return _send_json(self, recent_sessions(
                    db_path, limit=_clamp_limit(qs.get("limit", ["20"])[0], 20),
                    since=since, until=until,
                ))
            if path == "/api/daily":
                return _send_json(self, daily_token_breakdown(db_path, since, until))
            if path == "/api/skills":
                rows = skill_breakdown(db_path, since, until)
                catalog = cached_catalog()
                for r in rows:
                    info = catalog.get(r["skill"])
                    r["tokens_per_call"] = info["tokens"] if info else None
                return _send_json(self, rows)
            if path == "/api/by-model":
                rows = model_breakdown(db_path, since, until)
                for r in rows:
                    c = cost_for(r["model"], r, pricing)
                    r["cost_usd"] = c["usd"]
                    r["cost_estimated"] = c["estimated"]
                return _send_json(self, rows)
            if path.startswith("/api/sessions/"):
                sid = path.rsplit("/", 1)[1]
                return _send_json(self, session_turns(db_path, sid))
            if path == "/api/tips":
                return _send_json(self, all_tips(db_path, pricing=pricing))
            if path == "/api/plan":
                return _send_json(self, {"plan": get_plan(db_path), "pricing": pricing})
            if path == "/api/about":
                return _send_json(self, build_info())
            if path == "/api/scan":
                n = scan_dir(projects_dir, db_path)
                return _send_json(self, n)
            if path == "/api/today/range":
                try:
                    offset = int(qs.get("offset", ["0"])[0])
                except ValueError:
                    offset = 0
                offset = max(0, min(offset, 365))
                since, until, day = today_range_local(offset_days=offset)
                return _send_json(self, {
                    "since": since,
                    "until": until,
                    "day": day,
                    "day_starts_at_hour": DEFAULT_DAY_STARTS_AT_HOUR,
                })
            if path == "/api/stream":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                while True:
                    try:
                        evt = EVENTS.get(timeout=15)
                        chunk = f"data: {json.dumps(evt, default=str)}\n\n".encode()
                    except queue.Empty:
                        chunk = b": ping\n\n"
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            url = urlparse(self.path)
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return _send_error(self, 400, "invalid Content-Length")
            if length < 0 or length > MAX_POST_BYTES:
                return _send_error(self, 413, f"body too large (max {MAX_POST_BYTES} bytes)")
            try:
                body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            except json.JSONDecodeError:
                return _send_error(self, 400, "invalid JSON")
            if not isinstance(body, dict):
                return _send_error(self, 400, "body must be a JSON object")
            if url.path == "/api/plan":
                set_plan(db_path, body.get("plan", "api"))
                return _send_json(self, {"ok": True})
            if url.path == "/api/tips/dismiss":
                dismiss_tip(db_path, body.get("key", ""))
                return _send_json(self, {"ok": True})
            if url.path == "/api/heartbeat":
                _heartbeat["at"] = time.time()
                info = build_info()
                return _send_json(self, {
                    "ok": True,
                    "version": info["version"],
                    "commit": info["commit"],
                })
            if url.path == "/api/quit":
                # Source IP is set by the kernel and unforgeable, unlike the
                # Host header. Prevents remote kill when HOST=0.0.0.0.
                if self.client_address[0] not in ("127.0.0.1", "::1"):
                    return _send_error(self, 403, "quit only allowed from localhost")
                _send_json(self, {"ok": True})
                def _shutdown():
                    time.sleep(0.1)
                    os.kill(os.getpid(), signal.SIGINT)
                threading.Thread(target=_shutdown, daemon=True).start()
                return
            self.send_response(404)
            self.end_headers()

    return H


def _watchdog(timeout: float = 30.0, interval: float = 5.0):
    """Shut down if no heartbeat has arrived within `timeout` seconds.

    Waits until the first heartbeat before starting the countdown, so the
    server stays up indefinitely if no browser ever connects (e.g. --no-open).
    """
    while _heartbeat["at"] is None:
        time.sleep(interval)
    while True:
        time.sleep(interval)
        if time.time() - _heartbeat["at"] > timeout:
            print("\nSymbolon: no client detected, shutting down…")
            os.kill(os.getpid(), signal.SIGINT)
            return


def _scan_loop(db_path: str, projects_dir: str, interval: float = 30.0):
    while True:
        try:
            n = scan_dir(projects_dir, db_path)
            if n["messages"] > 0:
                EVENTS.put({"type": "scan", "n": n, "ts": time.time()})
        except Exception as e:
            EVENTS.put({"type": "error", "message": str(e)})
        time.sleep(interval)


class _Server(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


def run(host: str, port: int, db_path: str, projects_dir: str):
    # When spawned as a background job by bash (`cmd &`, `nohup cmd &`),
    # SIGINT is inherited as SIG_IGN — `os.kill(getpid(), SIGINT)` from
    # /api/quit would then be silently dropped. Force the default handler
    # so KeyboardInterrupt fires regardless of how we were launched.
    signal.signal(signal.SIGINT, signal.default_int_handler)

    threading.Thread(target=_scan_loop, args=(db_path, projects_dir), daemon=True).start()
    threading.Thread(target=_watchdog, daemon=True).start()
    H = build_handler(db_path, projects_dir)
    httpd = _Server((host, port), H)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSymbolon stopping…")
    finally:
        httpd.shutdown()
