# @raycast.schemaVersion 1
# @raycast.title Symbolon Open
# @raycast.mode silent
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Open the Symbolon in the browser (starts the daemon if needed).

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& symbolon open
