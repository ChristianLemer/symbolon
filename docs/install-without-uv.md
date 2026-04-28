# Install without uv

Already have Python set up and would rather not install another tool? You can run Token Dashboard directly from a `git clone`.

## Requirements

- Python 3.11 or newer
- A web browser

## Steps

```bash
git clone https://github.com/ChristianLemer/token-dashboard.git
cd token-dashboard
python3 cli.py dashboard
```

> On Windows, use `py -3` in place of `python3`.

The dashboard runs the same way as the `uv tool install` route: it scans `~/.claude/projects/` on startup, opens your browser to <http://127.0.0.1:8080>, and re-scans every 30 seconds.

## Trade-offs vs. `uv tool install`

| | `uv tool install` | `git clone` |
|---|---|---|
| Setup steps | 2 | 3 |
| Global `token-dashboard` command | yes | no — you stay in the cloned directory |
| Updates | `uv tool upgrade token-dashboard` | `git pull` |
| Bundled Raycast / nushell integrations | yes (inside the wheel) | yes (in the cloned tree under `raycast/` and `nu/`) |

## Replacing the CLI command in the docs

Throughout the rest of the documentation, you'll see commands like:

```bash
token-dashboard scan
token-dashboard status
token-dashboard integrations raycast --install
```

When using the `git clone` route, replace `token-dashboard` with `python3 cli.py`:

```bash
python3 cli.py scan
python3 cli.py status
python3 cli.py integrations raycast --install
```

Everything else works the same.
