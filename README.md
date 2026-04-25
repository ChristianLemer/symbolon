# Token Dashboard

A local dashboard that reads the JSONL transcripts Claude Code writes to `~/.claude/projects/` and turns them into per-prompt cost analytics, tool/file heatmaps, subagent attribution, cache analytics, project comparisons, and a rule-based tips engine.

**Everything runs locally.** No data leaves your machine — no telemetry, no API calls for your data, no login.

![Overview tab — totals and daily charts](docs/images/dashboard-overview-top.jpg)

![Overview tab — per-project, per-model, top tools, recent sessions](docs/images/dashboard-overview-bottom.jpg)

> **Lineage** — This fork builds on [nateherkai/token-dashboard](https://github.com/nateherkai/token-dashboard), itself a substantial reimplementation inspired by [phuryn/claude-usage](https://github.com/phuryn/claude-usage). What I add on top: `uv` tooling + ruff/ty config, graceful shutdown UX (Ctrl+C / ⏻ button / browser-close watchdog), a "Today" range with honest monthly cost projection, source-IP guard on `/api/quit`, and a GitHub Actions CI. See [`docs/inspiration.md`](docs/inspiration.md) for the original feature set.

## What this is useful for

- Seeing which of your prompts are expensive (surprise: they usually involve large tool results).
- Comparing token usage across projects you've worked on.
- Spotting wasteful patterns — the same file read twenty times in a session, a tool call returning 80k tokens.
- Understanding what a "cache hit" actually saves you.
- If you're on Pro or Max, confirming you're getting your money's worth in API-equivalent dollars.

## Prerequisites

- **Claude Code** — installed and with at least one session run. If you just installed Claude Code and haven't used it yet, run at least one prompt first.
- **A web browser.** Any modern one.
- **Python 3.11+** — already on macOS and most Linux. On Windows: `winget install Python.Python.3.12`.
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — recommended but not required. If you don't have it, see the *Without uv* section below.

## Quickstart

### One-liner, no install (recommended)

```bash
uvx --from git+https://github.com/nateherkai/token-dashboard token-dashboard dashboard
```

No cloning, no venv setup. `uvx` fetches, isolates, and runs in one step. Stop with `Ctrl+C`.

### Install once, run from anywhere

```bash
uv tool install git+https://github.com/nateherkai/token-dashboard
token-dashboard dashboard
```

After the first install, `token-dashboard` is a global command — no need to be in any particular directory.

### Without uv

```bash
git clone https://github.com/nateherkai/token-dashboard.git
cd token-dashboard
python3 cli.py dashboard
```

> On Windows, substitute `py -3` for `python3`.

---

All three options:

1. Scan `~/.claude/projects/` on startup (first run can take 20–60 s on a heavy machine).
2. Start a local server at <http://127.0.0.1:8080>.
3. Open your default browser to that URL.

Leave it running; it re-scans every 30 seconds and pushes updates live. Stop with `Ctrl+C`, click the ⏻ button in the top bar, or just close the browser tab — the server auto-shuts 30 s after the last tab disconnects.

## Where the data comes from

Claude Code writes one JSONL file per session here:

| OS | Path |
|---|---|
| macOS / Linux | `~/.claude/projects/<project-slug>/<session-id>.jsonl` |
| Windows | `C:\Users\<you>\.claude\projects\<project-slug>\<session-id>.jsonl` |

The dashboard never modifies those files — it only reads them and keeps a local SQLite cache at `~/.claude/token-dashboard.db`.

To point at a different location:

```bash
python3 cli.py dashboard --projects-dir /path/to/projects --db /path/to/cache.db
```

### Environment variables

| Var | Default | Purpose |
|---|---|---|
| `PORT` | `8080` | Port the local web server listens on |
| `HOST` | `127.0.0.1` | Bind address. Keep the default. Setting `0.0.0.0` exposes your entire prompt history to anyone on your local network — don't do this on any network you don't fully control (no coffee-shop Wi-Fi, no coworking spaces). |
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Where to scan for session JSONL files |
| `TOKEN_DASHBOARD_DB` | `~/.claude/token-dashboard.db` | SQLite cache location |

Pricing lives in [`pricing.json`](pricing.json). Edit it directly if model prices change or to add a new plan.

## CLI reference

```bash
token-dashboard scan          # populate / refresh the local DB, then exit
token-dashboard today         # today's totals (terminal)
token-dashboard stats         # all-time totals (terminal)
token-dashboard tips          # active suggestions (terminal)
token-dashboard dashboard     # scan + serve the UI at http://localhost:8080

# dashboard flags
token-dashboard dashboard --no-open   # don't auto-open the browser
token-dashboard dashboard --no-scan   # skip the initial scan (use cached DB only)
```

Change the port: `PORT=9000 token-dashboard dashboard`.

> **Without uv:** replace `token-dashboard` with `python3 cli.py` in every command above.

## The 7 tabs

The dashboard is a single page with a hash-router tab bar across the top. Each tab is backed by its own JSON API under `/api/`:

- **Overview** — all-time input/output/cache tokens, sessions, turns, estimated cost on your chosen plan, daily work and cache-read charts, tokens-by-project, token share by model, top tools by call count, and recent sessions. This is the landing tab.
- **Prompts** — your most expensive user prompts ranked by tokens. Click any row to see the assistant response, tool calls made, and the size of each tool result.
- **Sessions** — turn-by-turn view of any single session, with per-turn tokens and tool calls.
- **Projects** — per-project comparison: tokens, session counts, and which files were touched most.
- **Skills** — which skills you invoke most often, and (where we can measure them) their token cost. See [limitations](docs/KNOWN_LIMITATIONS.md#skills-token-counts-are-partial).
- **Tips** — rule-based suggestions for reducing token usage (repeated file reads, oversized tool results, low cache-hit rate, etc.).
- **Settings** — switch pricing between API / Pro / Max / Max-20x so cost figures everywhere else reflect your actual plan.

The Overview tab also has a built-in "What do these numbers mean?" panel that explains input/output/cache tokens in plain English.

## Troubleshooting

**"No data" or empty charts.** Run `python3 cli.py scan` once to populate the DB, then reload.

**Port 8080 already in use.** `PORT=9000 python3 cli.py dashboard`.

**Numbers look wrong / stuck.** The DB lives at `~/.claude/token-dashboard.db`. Delete it and re-run `python3 cli.py scan` to rebuild from scratch.

**Running the dashboard twice at the same time.** Don't — both processes will fight over the SQLite DB. Stop all instances before starting a new one.

## Accuracy note

Claude Code writes each assistant response 2–3 times to disk while it streams (the same API message gets snapshotted as output grows). The dashboard dedupes these by `message.id` so the final tally matches what the API actually billed. If you compare against another tool that sums every JSONL row, expect this dashboard's numbers to be lower — and closer to reality.

## Privacy

Nothing leaves your machine. No telemetry. No remote calls for your data. The browser fetches its JSON from `127.0.0.1`, and all JS/CSS/fonts are served from that same local server — ECharts is vendored into `web/`, and the UI falls back to system fonts rather than pulling from a font CDN. If you want to verify: `grep -r "https://" token_dashboard/ web/` — you'll find nothing.

## Tech stack

Python 3.11+ (no runtime dependencies) for the CLI, scanner, and HTTP server. SQLite for the local cache. Vanilla JS + ECharts for the UI, no build step. Dark theme, hash-based router, server-sent events for live refresh.

Data flow: `token_dashboard/cli.py` → `token_dashboard/scanner.py` → SQLite DB; `token_dashboard/server.py` exposes `/api/*` JSON routes and serves `web/`.

## Integrations

- **nushell** — see [`nu/td/`](nu/td/) for a module that treats the dashboard as a headless daemon and the browser, nu, and scripts as equal clients. After `use /path/to/repo/nu/td`: `td start` launches the daemon (no browser, then prints today's totals), `td stop` / `td restart` / `td status` for lifecycle, `td dashboard` opens the browser view, `td today`, `td prompts --limit 50 | where billable_tokens > 50000`, `td tips | where category == "right-size"` for queries piping into native nu tables. `help td` lists every command. Override the host with `$env.TD_HOST`.

## Further reading

- [`CLAUDE.md`](CLAUDE.md) — conventions and architecture overview (also picked up automatically by Claude Code)
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to develop and test
- [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) — rough edges
- [`docs/inspiration.md`](docs/inspiration.md) — prior art and how this project diverges

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Short version: fork, `uv run pytest` before opening a PR, keep runtime dependencies at zero.

## License

[MIT](LICENSE).
