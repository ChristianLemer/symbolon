#!/usr/bin/env bash
# @raycast.schemaVersion 1
# @raycast.title Token Dashboard Start
# @raycast.mode compact
# @raycast.icon 🦉
# @raycast.packageName Token Dashboard
# @raycast.description Launch the Token Dashboard daemon and open it in the browser.

# Raycast launches scripts with a minimal PATH that excludes user-local bin
# directories. Prepend the standard `uv tool install` / `pipx` location.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

# If already up, just open the browser and report status.
if token-dashboard status 2>/dev/null | grep -q running; then
  token-dashboard open >/dev/null 2>&1
  exec token-dashboard status
fi

# Launch detached and wait for the server to bind.
nohup token-dashboard dashboard --no-open >/dev/null 2>&1 &
disown

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if token-dashboard status 2>/dev/null | grep -q running; then
    token-dashboard open >/dev/null 2>&1
    exec token-dashboard status
  fi
  sleep 0.3
done

echo "failed to start within 3s"
exit 1
