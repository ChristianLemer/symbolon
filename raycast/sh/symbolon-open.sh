#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Symbolon Open
# @raycast.mode silent
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Open the Symbolon in the browser (starts the daemon if needed).

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec symbolon open
