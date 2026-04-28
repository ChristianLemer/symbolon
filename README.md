# Token Dashboard

Know what Claude Code is costing you. A local dashboard that turns your session history into clear answers — what you spent today, where the tokens went, and where you can save.

**Everything runs on your computer.** Nothing leaves your machine — no telemetry, no login, no API calls for your data.

## What you'll see

- What Claude Code cost you today, this week, this month — at a glance.
- Which prompts were expensive, and why (usually: a tool that returned a lot of data).
- How your usage compares across projects you've worked on.
- Which patterns are wasting tokens — the same file read twenty times, oversized tool results.
- If you're on Pro or Max: what your usage *would have cost* on pay-as-you-go, so you can tell whether the subscription is paying off.

## Install and run

We use [`uv`](https://docs.astral.sh/uv/) — a small modern tool that handles Python, virtual environments, and packaging in one step, with the same UX on macOS, Linux, and Windows. Two of the three options below need it; one doesn't.

### Install `uv` — optional, but recommended

If you don't have `uv` yet, pick the one for your system.

On Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On macOS:

```bash
brew install uv
```

On Windows:

```powershell
winget install astral-sh.uv
```

See [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) for other options.

### Try it (no install)

```bash
uvx --from git+https://github.com/ChristianLemer/token-dashboard token-dashboard dashboard
```

`uvx` fetches, runs, and discards in one step — nothing left behind on your machine. Good for trying it once before deciding.

### Install it

```bash
uv tool install git+https://github.com/ChristianLemer/token-dashboard
token-dashboard dashboard
```

`uv tool` puts `token-dashboard` on your PATH as a global command — run it from anywhere, upgrade later with `uv tool upgrade token-dashboard`.

### From source (no `uv` needed)

If you already have Python 3.11+ and would rather not add another tool:

```bash
git clone https://github.com/ChristianLemer/token-dashboard.git
cd token-dashboard
python3 cli.py dashboard
```

> On Windows, use `py -3` in place of `python3`.

See [Install without uv](docs/install-without-uv.md) for trade-offs and how to translate the rest of the docs' commands.

---

Once it runs:

- Your browser opens to the dashboard.
- The **Today** tab shows what you've spent so far.
- Use the range bar at the top to switch to **Yesterday**, the last 7 days, etc.
- Stop the dashboard with the **⏻** button in the top bar — or just close the browser tab. It shuts itself down 30 seconds later.

## Privacy

Nothing you see in the dashboard leaves your machine. No telemetry, no remote calls. The browser fetches everything from `127.0.0.1`, including charts and fonts. If you want to verify, search the source — there's nothing pointing outward.

## Going further

| Topic | What's there |
|---|---|
| [Getting started](docs/getting-started.md) | A walkthrough of each tab — what to look at first, what each number means |
| [Raycast integration](docs/raycast.md) | A hotkey that shows today's spend without opening the dashboard |
| [nushell integration](docs/nushell.md) | Query your usage from the shell |
| [CLI reference](docs/cli-reference.md) | Every command and flag |
| [Configuration](docs/configuration.md) | Environment variables, pricing tweaks |
| [Troubleshooting](docs/troubleshooting.md) | When something doesn't work |
| [Concepts](docs/concepts/) | Tokens, caching, accuracy — the things you'll wonder about eventually |
| [Known limitations](docs/KNOWN_LIMITATIONS.md) | Where the data is partial, and why |
| [Lineage](docs/lineage.md) | Where this fork comes from, and what's been added |

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Short version: fork, run the tests before opening a PR.

## License

[MIT](LICENSE). Built on top of [nateherkai/token-dashboard](https://github.com/nateherkai/token-dashboard) — see [lineage](docs/lineage.md) for the full story.
