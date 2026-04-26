#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Open
# @raycast.mode silent
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Open the Token Dashboard in the browser (server must be running).

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec token-dashboard open
