# Getting started

You've installed the dashboard and run `symbolon dashboard`. Your browser opened to <http://127.0.0.1:8080>. Now what?

This page walks you through the seven tabs and tells you what to look at first.

## Three things to check, in order

1. **The Today total** at the top of the **Overview** tab. That's what Claude Code has cost you so far today, on whichever pricing plan you've selected.
2. **The "Top tools" panel** lower on the same tab. The tool at the top is most likely where your tokens are going.
3. **The Tips tab.** If anything's worth changing about how you use Claude Code, it'll show up here.

That's the 60-second tour. The rest of the tabs reward exploration but aren't required for daily use.

## The seven tabs

### Overview — the landing tab

What you spent today (or yesterday, or in the last week, etc.), how it broke down, and which projects, models, and tools used the most.

The range bar at the top picks the time window: **Today** (default), **Yesterday**, the five preceding weekdays, **7d**, **30d**, **90d**, **All**.

Look for: the daily chart (helps you spot anomalies), the per-model split (are you on a more expensive model than you thought?), and the top tools list (most tokens come from one or two tools returning a lot of data).

The Overview also has a built-in **What do these numbers mean?** panel that explains input / output / cache tokens in plain English. Click to expand it; if you want to dig deeper, see [Concepts → Tokens](concepts/tokens.md).

### Prompts — the expensive ones

Your most expensive user prompts ranked by token count. Click any row to see the assistant response, the tool calls Claude made, and how big each tool result was.

This is the tab where the answer to "why was *that one* so expensive?" usually lives.

### Sessions — turn by turn

A session is a single conversation. This tab shows the turns of any one session — useful when something specific went off the rails and you want to retrace.

### Projects — across your codebases

Per-project totals: tokens, sessions, top files. Helps you answer "which project costs me the most" and "which files am I touching the most."

### Skills — what gets invoked

Which skills Claude Code reaches for, how often, and (where measurable) how many tokens each invocation costs. See [Known limitations → Skills token counts](KNOWN_LIMITATIONS.md#skills-token-counts-are-partial) for what's complete and what's partial.

### Tips — what to change

Rule-based suggestions. The engine looks for things like:

- The same file read many times in one session (drop a snippet in your CLAUDE.md so Claude doesn't have to re-read it)
- A tool consistently returning huge results (right-size or filter)
- A low cache-hit rate (your context might be churning more than it needs to)
- An outlier session that ate disproportionate tokens

Tips you don't care about can be dismissed.

### Settings — your pricing plan

Switch between **API** (pay-per-token), **Pro**, **Max**, and **Max 20×** so cost figures everywhere else reflect your actual plan.

## Stopping the dashboard

Three options, all equivalent:

- Click the **⏻** button in the top bar
- Press **Ctrl+C** in the terminal where it's running
- Just close the browser tab — the server shuts itself down 30 seconds after the last tab disconnects

## Where to next

- [Raycast integration](raycast.md) — see today's spend with a hotkey, no browser
- [nushell integration](nushell.md) — query usage from the shell
- [Concepts](concepts/) — what tokens are, why caching matters, how the dashboard makes its numbers accurate
