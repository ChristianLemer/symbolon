# Tech Debt

Issues found in an April 2026 code-quality review. None are blockers for personal use — the dashboard works correctly for a single user on a single tab. They matter if the tool is hardened for broader distribution or multi-user use.

## Medium — fix before wider distribution

### `sort` parameter is unvalidated in SQL ORDER BY (`server.py`, `db.py`)

`GET /api/prompts?sort=<value>` passes `sort` straight to `expensive_prompts()`, which puts it into an f-string `ORDER BY` clause. The current ternary (`"timestamp DESC" if sort == "recent" else "billable_tokens DESC"`) defaults to a safe constant for any unknown value, so there's no actual injection today. But the structural pattern is wrong — a future refactor that branches differently would be one step away from real injection. The fix is to allowlist `["recent", "tokens"]` and return a 400 on anything else.

### `do_HEAD` calls `do_GET`, violating HTTP spec (`server.py:78`)

`do_HEAD` is implemented by calling `do_GET`, which writes a response body. The HTTP spec requires HEAD to suppress the body. For the SSE endpoint (`/api/stream`) this is worse: a HEAD request will block the thread forever waiting on `EVENTS.get()`. The fix is to detect HEAD inside route handlers or override `send_response` to suppress the body.

### Single global SSE queue breaks multiple browser tabs (`server.py:27`)

There is one `queue.Queue` instance (`EVENTS`) shared by all SSE clients. With two open tabs (or a page reload before the old `EventSource` closes), both clients race on `EVENTS.get()` and each receives roughly half the scan events. The fix is a per-client queue with a fan-out dispatcher.

## Low — worth fixing eventually

### `SUM` without `COALESCE` can return NULL (`db.py:237`, `db.py:277`)

`project_summary` and `recent_sessions` compute `SUM(input_tokens)+SUM(output_tokens)+…` without wrapping each `SUM` in `COALESCE(…, 0)`. If any token column is NULL for a row (possible on rows ingested before the column had a `DEFAULT 0`), the whole expression returns NULL. `overview_totals` already does this correctly — apply the same pattern.

### `_range_clause` interpolates `col` directly into SQL (`db.py:127`)

The helper builds `f"{col} >= ?"` where `col` is a caller-supplied string. All current callers pass the string literal `"timestamp"`, so there's no actual injection path, but the function signature accepts arbitrary strings. Either assert against an allowlist inside the function or inline the column name at the call sites.

### `v.tier` and model key `k` are unescaped in settings HTML (`settings.js:27`)

The Settings route injects `v.tier` into a CSS class attribute and `k` (the model key from `pricing.json`) into element text without passing through `fmt.htmlSafe`. The data comes from the local `pricing.json`, so the attack surface is minimal, but it's inconsistent with how every other route handles data. Apply `fmt.htmlSafe` uniformly.

### Opus/Sonnet rates hardcoded in `right_size_tips` (`tips.py:124–125`)

The tip engine computes savings estimates using hardcoded model prices instead of reading from `pricing.json`. If `pricing.json` is updated (e.g. after an Anthropic price change), the tip calculations silently stay at old rates. Pass the loaded pricing dict into the function instead.

### N+1 CWD queries in `project_summary` and `recent_sessions` (`db.py:247`, `db.py:287`)

For each project/session in the result, a follow-up query fetches distinct `cwd` values. This is one extra round trip per project slug — unnoticeable at 10 projects, potentially slow at 50+. A single CTE or `GROUP_CONCAT` in the main query would eliminate it.

### SSE `onmessage` doesn't await `render()` (`app.js:133`)

The event handler fires `render()` without awaiting it. If two scan events arrive in quick succession, two `render()` calls run concurrently and both write to `$('#app').innerHTML` — the second can overwrite the first mid-paint. Serialize with a flag or a queue.

## Test gaps

- No test passes `sort=<unknown>` to `/api/prompts` and asserts a 400.
- No test exercises a project with NULL token columns to catch the `SUM` + NULL issue.
- No test for multiple SSE clients (the fan-out bug is entirely uncovered).
- `tips.py` hardcoded rates are never compared against `pricing.json` in tests.
- `test_cli.py` never exercises the `dashboard` command (server startup path).
