# Raycast integration

If you use [Raycast](https://www.raycast.com/), Symbolon ships with one script command that puts the dashboard a hotkey away.

## What it gives you

- **Symbolon Dashboard** — opens the dashboard in your browser. Starts the daemon if it's not running. The daemon shuts itself down 30 s after the browser tab is closed, so there's nothing to clean up.

If you need finer-grained control (start without browser, explicit stop, status from a script), the CLI has it — see [the CLI reference](cli-reference.md).

## Setup

```bash
symbolon integrations raycast --install
```

That copies the script to `~/.raycast-scripts/`. The right variant for your platform is picked automatically — bash on macOS / Linux, PowerShell on Windows.

Then in Raycast → **Settings** → **Extensions** → **Script Commands**, click **Add Directories** and pick `~/.raycast-scripts/`. The command appears under "Symbolon."

## Recommended hotkey

Bind **Symbolon Dashboard** to a hotkey you reach for often. One keystroke, browser tab opens with today's costs.

## Where the script lives

If you'd rather copy it somewhere else, you can find the source path:

```bash
$ symbolon integrations raycast
/Users/.../site-packages/symbolon/_resources/raycast
```

The `--install` flag is the convenient path; the directory above is the source of truth.

## Updates

When you upgrade Symbolon (`uv tool upgrade symbolon`), the bundled scripts update with it. Re-run `symbolon integrations raycast --install` to pick up the new version in `~/.raycast-scripts/`. The installer recognises older Symbolon scripts (by package marker) and removes them, so leftover `Symbolon Status`/`Open`/`Start`/`Stop` entries from earlier installs are cleaned up automatically.
