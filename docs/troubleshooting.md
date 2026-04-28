# Troubleshooting

## "No data" or empty charts

Run `token-dashboard scan` once to populate the database, then reload the page.

## Port 8080 already in use

Another program is on that port. Pick a different one:

```bash
PORT=9000 token-dashboard dashboard
```

## Numbers look wrong, or stuck

The cache is stale or got into a bad state. Delete it and rebuild:

```bash
rm ~/.claude/token-dashboard.db
token-dashboard scan
```

The next scan will be slower than usual — it has to read every JSONL from scratch — but subsequent ones are incremental.

## First scan is slow

Expected on heavy users (hundreds of sessions, tens of MB of JSONL). The scanner reads everything once, then tracks file mtime and byte offsets, so subsequent scans are fast.

If you don't want to wait, start without scanning:

```bash
token-dashboard dashboard --no-scan
```

The dashboard runs against the existing cache. The scanner will catch up on the next 30-second cycle.

## Two dashboards running at once

Don't. Both processes will fight over the SQLite database — you'll see inconsistent numbers and occasional `database is locked` errors. Stop all instances before starting a new one:

```bash
token-dashboard stop
```

## I closed the browser but the server is still running

Either:

- It's still in its 30-second grace window — wait, or click the **⏻** button if you can.
- You stopped your only tab, but another tab is still open elsewhere — close it.
- Force it: `token-dashboard stop`.

## "command not found: token-dashboard"

`uv` installs executables to `~/.local/bin` (Unix) or `%USERPROFILE%\.local\bin` (Windows). If that directory isn't on your `PATH`, run:

```bash
uv tool update-shell
```

That adds the right line to your shell config (`.bashrc` / `.zshrc` / PowerShell profile). Open a new terminal afterward.

For nushell users, add manually to `env.nu`:

```nu
$env.Path = ($env.Path | split row (char esep) | append ($nu.home-path | path join '.local' 'bin'))
```

## Numbers don't match Anthropic Console

Expected — the dashboard sees only Claude Code, not Claude Desktop, claude.ai web, or direct API calls. See [Known limitations](KNOWN_LIMITATIONS.md) for the full picture.

## My number is much lower than another tracking tool's

Also expected, and probably correct. Claude Code writes each assistant response 2–3 times to disk while it streams (the same API message gets snapshotted as output grows). This dashboard dedupes those snapshots so the final tally matches what the API actually billed. A naive tool that sums every JSONL row will report higher — and wrong — numbers. See [Concepts → Dedup and accuracy](concepts/dedup-and-accuracy.md).
