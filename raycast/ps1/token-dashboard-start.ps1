# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Start
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Launch the Token Dashboard daemon (no browser).

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& token-dashboard start
