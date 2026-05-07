# Known Limitations

None of these are blockers — the dashboard still gives you useful information. They're the rough edges you'll notice if you look hard.

## Claude Desktop, claude.ai web, and direct API calls are invisible

This dashboard reads only what Claude Code writes to `~/.claude/projects/<project>/<session>.jsonl`. Three other surfaces stay untracked:

- **Claude Desktop** — stores conversations locally in IndexedDB but does **not** expose token counts in the local store (verified April 2026: model identifiers are present, no `input_tokens` / `output_tokens` / `usage` keys anywhere). Anthropic counts them server-side and the desktop client doesn't need them client-side.
- **claude.ai web** — pure server-side, nothing local to read.
- **Direct API usage** (`anthropic-py` SDK, etc.) — the SDK doesn't log usage by default. Tools like Langfuse or Helicone exist for that lineage.

For a complete picture across surfaces, cross-check with the Anthropic Console (console.anthropic.com → Settings → Usage). It shows aggregated totals only — no per-session breakdown — but it is the only source of truth for non-Code consumption.

For long Desktop sessions especially, expect the totals here to **understate your real usage**. The dashboard's brand carries a "Claude Code only" badge in the topbar to keep that scope visible at a glance.

## Skills token counts are partial

The Skills route shows every skill Claude Code invoked, how many times, across how many sessions, and when. The **tokens-per-call** column is populated only for skills whose `SKILL.md` lives under `~/.claude/skills/`, `~/.claude/scheduled-tasks/`, or `~/.claude/plugins/`. Skills registered elsewhere (project-local `.claude/skills/`, or invocations that go through the `Task` tool with a skill-shaped `subagent_type`) show invocation counts but leave the token column blank.

It's still a useful view — you can see which skills dominate your session time — just don't expect a complete per-skill token cost. PRs to broaden the catalog scan welcome.

## Cost for Pro / Max / Max-20x users is shown as API-equivalent, not subscription value

The Settings route lets you select your pricing plan, but the Overview cost number is always the API-equivalent (what the same usage would have cost on pay-per-token rates). If you're on Pro you pay a flat $20/month regardless of how much of that API-equivalent number you rack up. We don't do "subscription ROI" math yet — Anthropic doesn't publish per-plan rate limits as public JSON, and faking it would be worse than not doing it.

## Cowork sessions are invisible

If you use Claude's Cowork mode (server-side sessions, not local `claude` CLI), those sessions don't write JSONL to `~/.claude/projects/` and the dashboard can't see them.

## Non-standard model names get tier-fallback pricing

If a transcript references a model ID not in `pricing.json` (e.g. a future snapshot that isn't in our table yet), cost is estimated from the tier substring (`opus` / `sonnet` / `haiku`) in the name. The UI marks these as `estimated: true`. If the model name contains none of those substrings, cost is reported as null.

## First scan can be slow

The first `python3 cli.py scan` on a heavy user's machine can read tens of MB across hundreds of JSONLs. Subsequent scans are incremental (mtime + byte-offset tracking in the `files` table), so they're fast.

## Running two dashboards against the same DB

Both will fight over the SQLite file and you'll see inconsistent numbers and occasional `database is locked` errors. Only run one at a time. If you want to view the dashboard from a second device, use `HOST=0.0.0.0` on the one running machine and point the second device's browser at it.
