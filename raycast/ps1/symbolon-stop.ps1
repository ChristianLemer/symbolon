# @raycast.schemaVersion 1
# @raycast.title Symbolon Stop
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Stop the running Symbolon daemon.

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& symbolon stop
