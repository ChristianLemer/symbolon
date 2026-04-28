# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Status
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Show whether the Token Dashboard daemon is up and today's spend.

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& token-dashboard status
