# nushell integration

If you live in [nushell](https://www.nushell.sh/), the dashboard ships as a daemon-friendly nu module. Your shell scripts and the browser become equal clients of the same running dashboard.

## What it gives you

- A `td` command suite for status, start / stop / restart, and querying today's totals as a record
- Pipe-friendly output for `td prompts`, `td tips`, etc. — chain with `where`, `select`, `to csv`
- The dashboard becomes a headless data source you can script against

## Setup

```nu
use (symbolon integrations nu)
```

Add that line to your nushell config (typically `~/.config/nushell/config.nu`).

To find the path manually:

```bash
$ symbolon integrations nu
/Users/.../site-packages/symbolon/_resources/nu/td
```

## Common commands

```nu
td start            # launch the daemon (no browser, prints today's totals)
td status           # is it up? today's spend?
td stop             # ask the daemon to shut down
td restart          # stop + start
td dashboard        # open the browser view
td today            # today's totals as a record (input/output/cache tokens, cost)
```

## Querying

```nu
td prompts --limit 50 | where billable_tokens > 50000
td tips | where category == "right-size"
td today | get cost
```

Anything from the dashboard's JSON API is reachable through `td` and pipes into the rest of nu.

`help td` lists every available command.

## Configuration

Override the host the module talks to:

```nu
$env.TD_HOST = "http://127.0.0.1:9000"
```

Useful if you're running the dashboard on a non-default port (see [Configuration](configuration.md)).

## Updates

When you upgrade Symbolon (`uv tool upgrade symbolon`), the bundled module updates with it. The `use` line in your config keeps pointing at the latest installed version.
