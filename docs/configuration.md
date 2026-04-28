# Configuration

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8080` | Port the local web server listens on. |
| `HOST` | `127.0.0.1` | Bind address. **Keep the default.** Setting `0.0.0.0` exposes your prompt history to anyone on your local network — don't do this on any network you don't fully control. |
| `CLAUDE_PROJECTS_DIR` | `~/.claude/projects` | Where to scan for Claude Code's session JSONL files. |
| `TOKEN_DASHBOARD_DB` | `~/.claude/token-dashboard.db` | SQLite cache location. |

Example:

```bash
PORT=9000 token-dashboard dashboard
```

## Where the data comes from

Claude Code writes one JSONL file per session here:

| OS | Path |
|---|---|
| macOS / Linux | `~/.claude/projects/<project-slug>/<session-id>.jsonl` |
| Windows | `C:\Users\<you>\.claude\projects\<project-slug>\<session-id>.jsonl` |

The dashboard never modifies these files — it only reads them and keeps a local SQLite cache.

To point at a different location:

```bash
token-dashboard dashboard --projects-dir /path/to/projects --db /path/to/cache.db
```

## Pricing

Pricing lives in `pricing.json` inside the package (`token_dashboard/pricing.json`). Each entry maps a model identifier to per-token rates and tier metadata.

For switching between plans (API / Pro / Max / Max-20×), use the **Settings** tab in the dashboard — that changes how all cost figures are computed in the UI without touching `pricing.json`.

If model prices change, edit `pricing.json` directly. Find its installed path with:

```bash
python3 -c "import token_dashboard, os; print(os.path.join(os.path.dirname(token_dashboard.__file__), 'pricing.json'))"
```

## Multiple dashboards on the same machine

Don't run two dashboards against the same database — they'll fight over the SQLite file. If you want to view the dashboard from a second device on your local network, set `HOST=0.0.0.0` on the running machine and point the second device's browser at it. (See the warning above before doing this on a shared network.)
