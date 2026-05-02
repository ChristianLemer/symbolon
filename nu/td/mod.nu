# Symbolon — nushell integration
#
# Hits the local dashboard's JSON API and returns nu-native records / tables.
# Override the host with $env.TD_HOST (default: http://127.0.0.1:8080).
#
# Install (in your nu config or one-off):
#   use /path/to/symbolon/nu/td
#
# Common commands:
#   td start        # launch the daemon (no browser) and show today's totals
#   td stop         # stop the daemon gracefully
#   td restart      # stop + start
#   td status       # {alive: bool, host: string}
#   td dashboard    # open the browser UI (starts daemon if needed)
#   td today        # today's totals
#   td prompts --limit 50 | where billable_tokens > 50000
#   td tips | where category == "right-size"
#
# Run `help td` for the full command list, `help td <command>` for details.
#
# Or import without the `td` prefix:
#   use /path/to/symbolon/nu/td *
#   start
#   today
#   prompts --limit 50 | sort-by billable_tokens

def info [text: string] { print $"(ansi yellow)($text)(ansi reset)" }
def ok   [text: string] { print $"(ansi green)($text)(ansi reset)" }
def fail [text: string] { print $"(ansi red)($text)(ansi reset)" }

def host []: nothing -> string {
  $env.TD_HOST? | default "http://127.0.0.1:8080"
}

def url [path: string, params: record = {}]: nothing -> string {
  let qs = (
    $params
    | transpose key value
    | where value != null
    | each { |row| $"($row.key)=($row.value)" }
    | str join "&"
  )
  if ($qs | is-empty) {
    $"(host)($path)"
  } else {
    $"(host)($path)?($qs)"
  }
}

def is-alive []: nothing -> bool {
  try {
    http get (url "/api/plan") | ignore
    true
  } catch {
    false
  }
}

# Daemon reachability — returns {alive, host}.
export def status []: nothing -> record {
  { alive: (is-alive), host: (host) }
}

# Start the dashboard daemon in the background (headless — no browser).
# Idempotent: returns immediately if the daemon is already up.
# Polls /api/plan until reachable (max ~30 s) so the daemon is actually
# ready when this returns. On success, returns today's totals.
# Use `td dashboard` to open the browser, `td stop` to stop.
export def start [] {
  if (is-alive) {
    ok "Symbolon daemon is already running."
    return (today)
  }
  if (which symbolon | is-empty) {
    error make {
      msg: "symbolon not found on PATH"
      help: "install with: uv tool install git+https://github.com/ChristianLemer/symbolon"
    }
  }
  ^bash -c "nohup symbolon dashboard --no-open >/dev/null 2>&1 &"
  info "Symbolon daemon starting…"
  for _ in 0..60 {
    sleep 500ms
    if (is-alive) {
      ok "Symbolon daemon ready."
      return (today)
    }
  }
  error make {
    msg: "daemon did not become reachable within 30 s"
    help: "try running it in foreground to see errors: `^symbolon dashboard --no-open`"
  }
}

# Stop the daemon gracefully (only allowed from localhost).
# Polls until the daemon is actually unreachable so subsequent
# `td status` reflects reality.
export def stop []: nothing -> record {
  info "Symbolon daemon stopping…"
  let response = (http post (url "/api/quit") "")
  for _ in 0..30 {
    if not (is-alive) {
      ok "Symbolon daemon stopped."
      return $response
    }
    sleep 100ms
  }
  fail "Symbolon daemon may still be running (timeout reached)."
  $response
}

# Stop the daemon if running, then start. Useful after upgrading the
# `symbolon` binary so the new code takes effect.
export def restart [] {
  if (is-alive) { stop | ignore }
  start
}

# Open the web dashboard in your default browser.
# Starts the daemon first if it isn't running.
export def dashboard []: nothing -> nothing {
  if not (is-alive) {
    start | ignore
    sleep 1sec
  }
  let target = (host)
  match $nu.os-info.name {
    "macos"   => { ^open $target }
    "linux"   => { ^xdg-open $target }
    "windows" => { ^cmd /c start $target }
    _         => { print $"Open ($target) in your browser." }
  }
}

# Totals (sessions, turns, tokens, cost) — all-time or for a since/until window.
export def overview [
  --since: string  # ISO timestamp
  --until: string  # ISO timestamp
]: nothing -> record {
  http get (url "/api/overview" {since: $since, until: $until})
}

# Today's totals — uses the server's canonical "today" range (default
# 4 a.m. local cutoff so late-night sessions count toward yesterday).
export def today []: nothing -> record {
  let r = (http get (url "/api/today/range"))
  http get (url "/api/overview" {since: $r.since, until: $r.until})
}

# Most expensive prompts. Sort by `tokens` (default) or `recent`.
export def prompts [
  --limit: int = 50
  --sort: string = "tokens"
]: nothing -> table {
  http get (url "/api/prompts" {limit: $limit, sort: $sort})
}

# Recent sessions, most recent first.
export def sessions [
  --limit: int = 20
  --since: string
  --until: string
]: nothing -> table {
  http get (url "/api/sessions" {limit: $limit, since: $since, until: $until})
}

# Per-project token totals.
export def projects [
  --since: string
  --until: string
]: nothing -> table {
  http get (url "/api/projects" {since: $since, until: $until})
}

# Tool usage breakdown.
export def tools [
  --since: string
  --until: string
]: nothing -> table {
  http get (url "/api/tools" {since: $since, until: $until})
}

# Daily token breakdown (one row per day).
export def daily [
  --since: string
  --until: string
]: nothing -> table {
  http get (url "/api/daily" {since: $since, until: $until})
}

# Skills invocation counts and per-call cost (where measurable).
export def skills [
  --since: string
  --until: string
]: nothing -> table {
  http get (url "/api/skills" {since: $since, until: $until})
}

# Per-model breakdown with estimated cost.
export def "by-model" [
  --since: string
  --until: string
]: nothing -> table {
  http get (url "/api/by-model" {since: $since, until: $until})
}

# Active rule-based tips.
export def tips []: nothing -> table {
  http get (url "/api/tips")
}

# Trigger an immediate scan. Returns the {files, messages, tools} counts.
export def scan []: nothing -> record {
  http get (url "/api/scan")
}
