#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Stop
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Shut down the Token Dashboard daemon.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec token-dashboard stop
