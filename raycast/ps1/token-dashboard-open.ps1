# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Open
# @raycast.mode silent
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Open the Token Dashboard in the browser (starts the daemon if needed).

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& token-dashboard open
