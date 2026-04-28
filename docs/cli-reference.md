# CLI reference

Every command and flag.

> **`uv` vs. `git clone`**: if you installed via `git clone`, replace `token-dashboard` with `python3 cli.py` in every command below.

## Subcommands

| Command | What it does |
|---|---|
| `token-dashboard scan` | Populate or refresh the local SQLite cache from the JSONL transcripts, then exit. |
| `token-dashboard today` | Print today's totals to the terminal. |
| `token-dashboard stats` | Print all-time totals to the terminal. |
| `token-dashboard tips` | Print active suggestions (the same content as the Tips tab). |
| `token-dashboard dashboard` | Scan and serve the UI at <http://127.0.0.1:8080>. The recommended entry point. |

### Daemon control

Useful for launchers like Raycast and Alfred, or for shell scripts.

| Command | What it does |
|---|---|
| `token-dashboard status` | One-line server up/down + today's cost + prompt count. Returns non-zero if the server is down. |
| `token-dashboard start` | Start the daemon in the background (no browser). |
| `token-dashboard open` | Open the dashboard in the browser. Starts the daemon if needed. |
| `token-dashboard stop` | Ask the running daemon to shut down. |

### Integrations

| Command | What it does |
|---|---|
| `token-dashboard integrations` | Print paths to the bundled Raycast scripts and nushell module. |
| `token-dashboard integrations raycast` | Print just the Raycast directory path. |
| `token-dashboard integrations raycast --install` | Copy Raycast scripts to `~/.raycast-scripts/` (platform-aware: bash on macOS/Linux, PowerShell on Windows). |
| `token-dashboard integrations nu` | Print just the nushell module path. |

## Dashboard flags

| Flag | What it does |
|---|---|
| `--no-open` | Don't auto-open the browser when starting. |
| `--no-scan` | Skip the initial scan and use the cached DB only. Useful for slow first scans. |
| `--projects-dir <path>` | Override `~/.claude/projects/`. |
| `--db <path>` | Override `~/.claude/token-dashboard.db`. |

Example:

```bash
token-dashboard dashboard --projects-dir /path/to/projects --db /path/to/cache.db
```

## Environment variables

See [Configuration](configuration.md) for the full list (`PORT`, `HOST`, `CLAUDE_PROJECTS_DIR`, `TOKEN_DASHBOARD_DB`).
