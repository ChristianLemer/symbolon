# GitHub Project (Projects v2) commands.
#
# Idempotent — safe to re-run.

const PROJECT_TITLE = "Symbolon"

def info [text: string] { print $"(ansi yellow)($text)(ansi reset)" }
def ok   [text: string] { print $"(ansi green)($text)(ansi reset)" }

def current-login []: nothing -> string {
  let r = (gh api user --jq .login | complete)
  if $r.exit_code != 0 {
    error make {
      msg: $"gh api user failed: ($r.stderr | str trim)",
      label: {text: "external command failed", span: (metadata $r).span}
    }
  }
  $r.stdout | str trim
}

def current-repo [login: string]: nothing -> string {
  let r = (git remote -v | complete)
  if $r.exit_code != 0 {
    error make {
      msg: $"git remote -v failed: ($r.stderr | str trim)",
      label: {text: "external command failed", span: (metadata $r).span}
    }
  }
  let mine = (
    $r.stdout
    | lines
    | parse --regex 'github\.com[:/](?P<owner>[^/]+)/(?P<name>\S+)'
    | update name {|row| $row.name | str replace --regex `\.git$` "" }
    | where owner == $login
    | get --optional 0
  )
  if $mine != null { return $"($mine.owner)/($mine.name)" }
  let r2 = (gh repo view --json nameWithOwner | complete)
  if $r2.exit_code != 0 {
    error make {
      msg: $"gh repo view failed: ($r2.stderr | str trim)",
      label: {text: "external command failed", span: (metadata $r2).span}
    }
  }
  try {
    $r2.stdout | from json | get nameWithOwner
  } catch {|e|
    error make {
      msg: $"gh repo view: failed to parse JSON: ($e.msg)",
      label: {text: "json parse failed", span: (metadata $r2).span}
    }
  }
}

def link-repo [target: record<number: int, owner: string, repo: string>]: nothing -> nothing {
  info $"Linking to ($target.repo)…"
  let r = (gh project link $target.number --owner $target.owner --repo $target.repo | complete)
  if $r.exit_code != 0 {
    error make {
      msg: $"gh project link failed: ($r.stderr | str trim)",
      label: {text: "external command failed", span: (metadata $r).span}
    }
  }
  ok Linked
}

def find [owner: string]: nothing -> any {
  let r = (gh project list --owner $owner --format json | complete)
  if $r.exit_code != 0 {
    error make {
      msg: $"gh project list failed: ($r.stderr | str trim)",
      label: {text: "external command failed", span: (metadata $r).span}
    }
  }
  try {
    $r.stdout | from json | get projects | where title == $PROJECT_TITLE | get --optional 0
  } catch {|e|
    error make {
      msg: $"gh project list: failed to parse JSON: ($e.msg)",
      label: {text: "json parse failed", span: (metadata $r).span}
    }
  }
}

# Create the GitHub Project and link it to this repo.
# Idempotent: returns the existing project if one with the same title exists.
export def create []: nothing -> record {
  let owner = (current-login)
  let repo = (current-repo $owner)
  let existing = (find $owner)
  if $existing != null {
    ok $"Project '($PROJECT_TITLE)' already exists: ($existing.url)"
    link-repo {number: $existing.number, owner: $owner, repo: $repo}
    return $existing
  }

  info $"Creating project '($PROJECT_TITLE)'…"
  let r = (gh project create --owner $owner --title $PROJECT_TITLE --format json | complete)
  if $r.exit_code != 0 {
    error make {
      msg: $"gh project create failed: ($r.stderr | str trim)",
      label: {text: "external command failed", span: (metadata $r).span}
    }
  }
  let created = (try {
    $r.stdout | from json
  } catch {|e|
    error make {
      msg: $"gh project create: failed to parse JSON: ($e.msg)",
      label: {text: "json parse failed", span: (metadata $r).span}
    }
  })
  ok $"Created: ($created.url)"

  link-repo {number: $created.number, owner: $owner, repo: $repo}

  $created
}

# Open the GitHub Project in a web browser.
export def open []: nothing -> nothing {
  let owner = (current-login)
  let existing = (find $owner)
  if $existing == null {
    error make {
      msg: $"No project named '($PROJECT_TITLE)' found for ($owner). Run `admin gh project create` first.",
      label: {text: "project lookup returned null", span: (metadata $existing).span}
    }
  }
  let r = (gh project view $existing.number --owner $owner --web | complete)
  if $r.exit_code != 0 {
    error make {
      msg: $"gh project view failed: ($r.stderr | str trim)",
      label: {text: "external command failed", span: (metadata $r).span}
    }
  }
}
