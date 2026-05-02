#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Symbolon Status
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Show whether the daemon is up and today's cost so far.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec symbolon status
