#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Symbolon Start
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Launch the Symbolon daemon (no browser).

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec symbolon start
