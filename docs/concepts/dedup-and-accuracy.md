# Dedup and accuracy

If you compare this dashboard's numbers to another tool that reads the same JSONL files, ours will be **lower**. That's not a bug — the other tool is over-counting.

## Why JSONL totals are tricky

When Claude Code generates a response, it doesn't write a single line to the JSONL file at the end. It writes a *new line every time the response grows*, with the entire current state of the message. By the time the response finishes, the same API message has been written 2–3 times to disk, each time with a slightly larger token count.

This is great for crash recovery: if Claude Code dies mid-response, the latest snapshot in the file is the most complete one. But it means a naive tool that sums every JSONL row will count the same response multiple times.

## What this dashboard does

The dashboard's scanner uses `(session_id, message_id)` as a deduplication key. When it sees a row that updates a previous snapshot, it evicts the older snapshot from its accounting. The final tally is one row per actual API message — exactly what was billed.

You can see this in `symbolon/scanner.py` (look for `_evict_prior_snapshots`).

## What this means in practice

- The dashboard's totals **match the Anthropic Console's** totals for the same time period (within rounding).
- Tools that sum JSONL rows naively report higher numbers — sometimes 2–3× higher.
- If you're cross-checking with another tool and the numbers disagree by a large factor, this is almost always why.

## Why we don't trust "just take the latest snapshot"

You might think "just take the last snapshot per message and skip the math." We do — but the dedup key is `(session_id, message_id)`, not file order. Two factors complicate "just take the last":

1. **Partial flushes** — a snapshot can be flushed to disk with token counts from an intermediate state. Subsequent snapshots correct it. We need the latest *complete* one.
2. **Re-scans** — when a session is rescanned (e.g., after the file's mtime changes), the scanner needs to evict any prior accounting for that message before re-counting. The eviction is what makes incremental scanning safe.

## Where the limitations are

The dedup is robust for the formats Claude Code currently writes. If Anthropic changes the JSONL schema or the streaming behavior, the scanner may need to adjust. The relevant code is small and tested — see `tests/test_scanner.py` for the dedup test cases.

For surfaces this dashboard *can't* see at all (Claude Desktop, claude.ai web, direct API calls), see [Known limitations](../KNOWN_LIMITATIONS.md).
