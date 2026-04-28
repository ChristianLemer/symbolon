# Lineage

Token Dashboard's design didn't appear from nowhere. Here's the chain.

## phuryn/claude-usage — the original idea

[phuryn/claude-usage](https://github.com/phuryn/claude-usage) was the first project to take Claude Code's local JSONL transcripts (`~/.claude/projects/<project>/<session>.jsonl`) and turn them into a usable token / cost dashboard.

What it brought:

- Single-page HTML/JS dashboard backed by a small Python HTTP server
- SQLite cache (`~/.claude/usage.db`) populated by an incremental scanner
- Stdlib-only: no `pip install`, no Node, no build step
- CLI subcommands: `scan`, `today`, `stats`, `dashboard`
- Chart.js visualizations for daily / weekly trends

Limitations of that version:

- Cost calculations only matched `opus` / `sonnet` / `haiku` model identifiers
- No drill-down into individual prompts or sessions
- No per-project comparison
- API rates shown for everyone (misleading for Pro / Max users)
- 30-second polling refresh; no live tailing

## nateherkai/token-dashboard — substantial reimplementation

[nateherkai/token-dashboard](https://github.com/nateherkai/token-dashboard) is a substantial reimplementation of the same core idea, by Nate Herk. It takes phuryn's data source and CLI shape and delivers a much fuller product.

What Nate added on top:

- Seven dashboard tabs: Overview, Prompts, Sessions, Projects, Skills, Tips, Settings
- Drill-down into individual prompts (response text, tool calls, tool result sizes)
- Per-session turn-by-turn view
- Per-project comparison with file heatmaps
- Skills tab tracking which skills you invoke most
- Rule-based **Tips** engine (cache hit rate, repeat reads, oversized tool results, outliers)
- Plan-aware pricing (API / Pro / Max / Max-20×) in Settings
- Streaming-snapshot deduplication (each assistant response gets snapshotted 2–3 times during streaming; dedup matches what the API actually billed)
- Server-Sent Events stream for live UI refresh
- ECharts visualizations, dark theme, hash-based router
- Robust scanner: incremental mtime + byte-offset tracking, sidechain handling, partial-flush recovery
- OSS release pass: security audit, HEAD-method fix, privacy review

## This fork — for people who just want to make it run

This fork (Christian Lemer) takes Nate's complete dashboard and changes who it's for: someone who isn't a developer but uses Claude Code daily, and would like to know what it's costing them — without having to set up a Python project.

What this fork adds:

- **One-command install via `uv tool install`** — no `git clone`, no virtualenv, no PATH setup. Same UX on macOS, Linux, and Windows.
- **Today-first UX** — Overview defaults to today's spend with a 4 a.m. cutoff; per-day drill-down for the past week; monthly cost projection.
- **Daemon model** — `start` / `status` / `stop` / `open` subcommands let the dashboard run in the background while you check in on your own schedule.
- **Bundled integrations** — Raycast scripts and a nushell module ship inside the wheel; one command discovers their location, another installs them in place.
- **Point-and-click control** — ⏻ button in the UI to shut down, browser-close watchdog, graceful Ctrl-C, offline detection with a dimmed UI and a reconnect button.
- **Hardening** — source-IP guard on `/api/quit`, ruff/ty configuration, GitHub Actions CI running pytest + ruff on push and PR.
- **Modern Python tooling** — `pyproject.toml`, `uv` for dev workflow, `ruff` for lint, `ty` for types.

## Acknowledgements

Thanks to **phuryn** for proving the idea was worth building, and to **Nate Herk** for the dashboard this fork stands on. Most of the code that makes Token Dashboard useful is theirs; this fork is hospitality on top.
