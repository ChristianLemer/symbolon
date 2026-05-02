# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project overview

**Symbolon** — a local dashboard for tracking Claude Code token usage, costs, and session history. Reads the JSONL transcripts Claude Code writes to `~/.claude/projects/` and turns them into per-prompt cost analytics, tool/file heatmaps, subagent attribution, cache analytics, project comparisons, and a rule-based tips engine.

Forked from [nateherkai/token-dashboard](https://github.com/nateherkai/token-dashboard) — a substantial reimplementation inspired by [phuryn/claude-usage](https://github.com/phuryn/claude-usage). The upstream diverges from claude-usage in UI (vanilla JS + ECharts, dark theme, hash router, SSE refresh) and scope (expensive-prompt drill-down, skills view, tips engine, streaming-snapshot dedup). This fork repositions the tool for non-developer users — `uv tool install` packaging, Today-first UX, daemon model, bundled Raycast/nushell integrations, and hardening. See [`docs/lineage.md`](docs/lineage.md) for the full chain and what each layer added.

## Status

Working codebase. 68 Python unit tests (`python3 -m unittest discover tests`). Seven UI tabs wired up (Overview, Prompts, Sessions, Projects, Skills, Tips, Settings). Runs on macOS, Windows, and Linux.

## Architecture

- `cli.py` → `symbolon/scanner.py` → `~/.claude/symbolon.db` (SQLite)
- `symbolon/server.py` exposes JSON APIs (`/api/*`) + SSE stream (`/api/stream`) + static frontend (`symbolon/web/`)
- `symbolon/web/` is vanilla JS, no build step — hash router + ECharts

## Data source

Claude Code writes one JSONL file per session to `~/.claude/projects/<project-slug>/<session-id>.jsonl`. Each line is a message record; usage fields live at `message.usage` and model identifier at `message.model`. The scanner is incremental — it tracks each file's mtime and byte offset in the `files` table and only reads new bytes on subsequent scans.

## Conventions

- **Fully local.** No telemetry, no remote calls for user data. Tests run offline.
- **Migrating to uv.** The project is moving from bare `python3` invocations to a `uv`-managed setup (pyproject.toml, ruff, ty, pytest). New work should follow the uv conventions; old `python3 -m unittest` invocations still work during the transition. The no-third-party-runtime-dependency constraint stays — uv is a dev/tooling dependency only.
- **SQLite parameter binding always.** Any f-string in a SQL statement must interpolate only internal, caller-controlled values (column names, placeholder lists). User-reachable values go through `?`.
- **Small files with clear responsibilities.** If a file grows past ~400 lines or accretes three distinct concerns, split it.
- **Streaming-snapshot dedup.** When adding scanner logic that joins the `messages` table, remember `(session_id, message_id)` is the dedup key, not `uuid`. See `scanner._evict_prior_snapshots` and the migration note in `db._migrate_add_message_id`.

## Commit hygiene

One commit, one concern. Lint fixes, typo fixes, dead-code removal, imports reordering — these get their own commits (`chore(lint)`, `chore(cleanup)`, etc.), never folded into a feature commit even when convenient. Each commit's description should accurately cover all of its content; if you're padding a feature commit's body with "also …", split.

Apply this even mid-PR: an extra small chore commit is cheaper than a review where reviewers have to mentally separate concerns inside one commit's diff.

## Customizing

Env vars: `PORT` (default 8080), `HOST` (default 127.0.0.1), `CLAUDE_PROJECTS_DIR`, `SYMBOLON_DB`. Pricing lives in `pricing.json`. See [`docs/configuration.md`](docs/configuration.md) for details.

## Known limitations

See `docs/KNOWN_LIMITATIONS.md`. Current summary: Skills `tokens_per_call` is populated only for skills installed under the three scanned roots (`~/.claude/skills/`, `~/.claude/scheduled-tasks/`, `~/.claude/plugins/`); project-local skills and subagent-dispatched skills show invocation counts but blank token counts.

## Tooling

When working with Python, invoke the relevant `/astral:<skill>` for uv, ty, and ruff. For project-level conventions (pyproject.toml setup, pytest migration, linting config), invoke `/trailofbits:modern-python`.

## Verifying changes

```bash
uv run pytest                                      # all tests
uv run symbolon dashboard --no-open         # start the server
curl http://127.0.0.1:8080/api/overview            # sanity-check an endpoint
uv run ruff check .                                # lint
uv run ty check                                    # type-check
# Legacy (still works during transition): python3 cli.py dashboard --no-open
```
