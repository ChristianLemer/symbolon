# CLI reference

Every command and flag.

> **`uv` vs. `git clone`**: if you installed via `git clone`, replace `symbolon` with `python3 cli.py` in every command below.

## Subcommands

| Command | What it does |
|---|---|
| `symbolon scan` | Populate or refresh the local SQLite cache from the JSONL transcripts, then exit. |
| `symbolon today` | Print today's totals to the terminal. |
| `symbolon stats` | Print all-time totals to the terminal. |
| `symbolon tips` | Print active suggestions (the same content as the Tips tab). |

### Daemon control

| Command | What it does |
|---|---|
| `symbolon open` | Open the dashboard in the browser. Starts the daemon if needed. The recommended entry point for humans. |
| `symbolon start` | Start the daemon in the background (no browser). For scripts, autostart, or service managers. |
| `symbolon start --foreground` | Run the server in the foreground (logs visible, Ctrl+C to stop). For systemd, launchd, Docker, or debugging. |
| `symbolon stop` | Ask the running daemon to shut down. |
| `symbolon status` | One-line server up/down + today's cost + prompt count. Returns non-zero if the server is down. |

### Integrations

| Command | What it does |
|---|---|
| `symbolon integrations` | Print paths to the bundled Raycast scripts and nushell module. |
| `symbolon integrations raycast` | Print just the Raycast directory path. |
| `symbolon integrations raycast --install` | Copy Raycast scripts to `~/.raycast-scripts/` (platform-aware: bash on macOS/Linux, PowerShell on Windows). |
| `symbolon integrations nu` | Print just the nushell module path. |

## `start --foreground` flags

| Flag | What it does |
|---|---|
| `--no-scan` | Skip the initial scan and use the cached DB only. Useful for slow first scans. |
| `--no-auto-sync` | Skip the weekly `pricing.json` refresh from LiteLLM. |

## Common flags

| Flag | What it does |
|---|---|
| `--projects-dir <path>` | Override `~/.claude/projects/`. |
| `--db <path>` | Override `~/.claude/symbolon.db`. |

Example:

```bash
symbolon start --foreground --projects-dir /path/to/projects --db /path/to/cache.db
```

## Environment variables

See [Configuration](configuration.md) for the full list (`PORT`, `HOST`, `CLAUDE_PROJECTS_DIR`, `SYMBOLON_DB`).
