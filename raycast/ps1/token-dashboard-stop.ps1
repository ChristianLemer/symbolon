# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Stop
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Stop the running Token Dashboard daemon.

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& token-dashboard stop
