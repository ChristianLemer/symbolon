# @raycast.schemaVersion 1
# @raycast.title Symbolon Start
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Launch the Symbolon daemon (no browser).

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& symbolon start
