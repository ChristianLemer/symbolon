# Tokens

A "token" is roughly a chunk of text — about three-quarters of a word, on average. When you send Claude a prompt and Claude responds, both directions are measured in tokens, and you pay (or your subscription consumes credit) per token.

The dashboard splits tokens into three buckets, because they're priced differently and they tell you different things.

## Input tokens

Everything that goes *into* Claude: your prompt, the conversation history, the contents of any files you've shared, the results of tool calls. Input is the cheapest of the three.

If your input tokens are large, it usually means the conversation has accumulated a lot of context — long history, many files in scope, or a tool that returned a big result.

## Output tokens

Everything Claude produces in its reply: the prose, the code, the tool calls Claude decides to make. Output is more expensive than input — typically about 5× the per-token rate, depending on the model.

This is why prompts that ask for a long answer cost more than prompts that ask for a short one, and why "summarize this file" can be cheaper than "rewrite this file."

## Cache tokens

Claude Code reuses recent context cheaply by caching it on Anthropic's side. There are two flavors:

- **Cache creation** — the first time a chunk of input is added to the cache. Slightly more expensive than regular input.
- **Cache read** — every subsequent time that chunk is reused. About 10% the price of regular input.

The Overview tab shows both numbers separately. A high **cache read** count is good — it means Claude is reusing context efficiently and you're paying near-pennies for what would otherwise be expensive input.

A low cache hit rate, on the other hand, is one of the things the [Tips](../getting-started.md#tips--what-to-change) tab will flag. It usually means your context is churning more than it needs to: maybe a tool result that changes every turn is invalidating the cache, or you're starting too many fresh sessions.

## Why this matters for cost

Each tab in the dashboard adds these three together to give you a single "billable tokens" number per prompt or per session. But it's worth knowing the split:

- **Mostly cache reads?** You're using Claude efficiently.
- **Mostly fresh input?** Either the conversation is genuinely new each turn, or something is breaking your cache.
- **Mostly output?** You're asking Claude to produce a lot. Sometimes that's the whole point; sometimes it's a sign you could ask for a shorter answer.

## Where to look in the dashboard

- **Overview** has a "What do these numbers mean?" panel that links here on the surface.
- **Prompts** ranks individual prompts by total billable tokens — click in to see how the three buckets contributed.
- **Tips** highlights cache anomalies as actionable suggestions.
