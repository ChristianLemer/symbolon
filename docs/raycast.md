# Raycast integration

If you use [Raycast](https://www.raycast.com/), the dashboard ships with four script commands that put today's spend a hotkey away.

## What it gives you

- **Token Dashboard Status** — today's cost and prompt count in a single line, without leaving the keyboard. Bind it to a hotkey for ambient awareness.
- **Token Dashboard Open** — opens the dashboard in your browser. Starts the daemon if it's not running.
- **Token Dashboard Start** — starts the daemon in the background (no browser).
- **Token Dashboard Stop** — asks the running daemon to shut down.

## Setup

```bash
token-dashboard integrations raycast --install
```

That copies the scripts to `~/.raycast-scripts/`. The right variant for your platform is picked automatically — bash on macOS / Linux, PowerShell on Windows.

Then in Raycast → **Settings** → **Extensions** → **Script Commands**, click **Add Directories** and pick `~/.raycast-scripts/`. The four commands appear under "Token Dashboard."

## Recommended hotkey

Bind **Token Dashboard Status** to a hotkey you reach for often. The result is a one-line glance — "today: $0.84 across 24 prompts" — that doesn't pull you out of whatever you were doing.

## Where the scripts live

If you'd rather copy them somewhere else, you can find the source path:

```bash
$ token-dashboard integrations raycast
/Users/.../site-packages/token_dashboard/_resources/raycast
```

The `--install` flag is the convenient path; the directory above is the source of truth.

## Updates

When you upgrade Token Dashboard (`uv tool upgrade token-dashboard`), the bundled scripts update with it. Re-run `token-dashboard integrations raycast --install` to pick up the new versions in `~/.raycast-scripts/`.
