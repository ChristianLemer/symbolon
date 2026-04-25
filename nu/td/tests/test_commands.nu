# Smoke + behavioral tests for the td nushell module.
#
# Run from anywhere — nu resolves the import relative to this script's path:
#   nu nu/td/tests/test_commands.nu
#
# Exits non-zero on any failed assertion. Designed to be invoked from
# tests/test_nu_integration.py so it runs alongside the Python suite.

use std/assert
use ../../td

# ---- Test 1: every expected command is exported under the `td` namespace.

let expected = [
  "start" "stop" "restart" "status" "dashboard"
  "today" "overview"
  "prompts" "sessions" "projects" "tools" "daily" "skills" "by-model" "tips"
  "scan"
]
let exported = (
  scope commands
  | where name starts-with "td "
  | get name
  | each { |n| $n | str replace "td " "" }
)
for cmd in $expected {
  assert ($cmd in $exported) $"missing command: td ($cmd)"
}
print $"ok — ($expected | length) expected commands exported"

# ---- Test 2: `td status` returns {alive: false, host: ...} when no daemon.
# Use a deliberately wrong host so the test never accidentally hits a
# real running daemon. Port 9 is the TCP discard port — no listener.

with-env {TD_HOST: "http://127.0.0.1:9"} {
  let s = (td status)
  assert ($s.alive == false) $"td status.alive should be false when daemon is unreachable, got ($s.alive)"
  assert ($s.host == "http://127.0.0.1:9") $"td status.host should reflect TD_HOST, got ($s.host)"
  print "ok — td status returns {alive: false, host: ...} when daemon unreachable"
}

# ---- Test 3: `td stop` uses an empty string body, not an empty record.
# Regression for nu 0.112+ which rejects records as http post bodies.
# We check the source text directly because actually invoking stop would
# require a running daemon and risk shutting one down.

let mod_src = (open ($env.FILE_PWD | path join ".." "mod.nu"))
assert (
  ($mod_src | str contains "http post (url \"/api/quit\") \"\"")
) "td stop must pass an empty string body, not an empty record"
assert (
  not ($mod_src | str contains "http post (url \"/api/quit\") {}")
) "td stop must not pass an empty record body (nu 0.112+ rejects it)"
print "ok — td stop uses string body for http post"

print ""
print "all nu tests passed."
