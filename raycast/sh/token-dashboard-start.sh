#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Start
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Launch the Token Dashboard daemon (no browser).

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec token-dashboard start
