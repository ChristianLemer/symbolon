# @raycast.schemaVersion 1
# @raycast.title Symbolon Status
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Symbolon
# @raycast.description Show whether the Symbolon daemon is up and today's spend.

$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
& symbolon status
