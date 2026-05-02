#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Symbolon Stop
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Shut down the Symbolon daemon.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec symbolon stop
