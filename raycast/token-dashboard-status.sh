#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Status
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Show whether the daemon is up and today's cost so far.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec token-dashboard status
