# @raycast.schemaVersion 1
# @raycast.title Symbolon Dashboard
# @raycast.mode silent
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Open the Symbolon dashboard (starts the daemon if needed).

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& symbolon open
