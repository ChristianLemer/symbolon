"""Sync `pricing.json` from LiteLLM's community-maintained model registry.

Anthropic doesn't publish a programmatic pricing endpoint. The de facto source
of truth is LiteLLM's `model_prices_and_context_window.json`, hosted on GitHub
and updated within hours of model launches. This module fetches that file,
filters to current Claude entries, transforms to our schema, and writes
atomically.

Stdlib only — keeps the no-runtime-dependency invariant.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

LITELLM_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)
DEFAULT_TIMEOUT_S = 10
DEFAULT_STALE_AGE_S = 7 * 86400  # one week
CLAUDE_MODEL_PATTERN = re.compile(r"^claude-(opus|sonnet|haiku)-")
# A name like `claude-opus-4-7-20260416` is the dated variant of the bare
# `claude-opus-4-7`. The bare name covers the same model; keeping both bloats
# pricing.json without adding information. Dated suffix = `-YYYYMMDD`.
DATED_VARIANT_SUFFIX = re.compile(r"-\d{8}$")
# Capability ordering: more powerful first. Used to sort pricing.json so a
# human reading the file sees Opus before Sonnet before Haiku.
TIER_ORDER = {"opus": 0, "sonnet": 1, "haiku": 2}


def _fetch_litellm(url: str = LITELLM_URL, timeout_s: float = DEFAULT_TIMEOUT_S) -> dict:
    with urllib.request.urlopen(url, timeout=timeout_s) as resp:  # noqa: S310 - public CDN
        return json.loads(resp.read().decode("utf-8"))


def _model_sort_key(name: str, entry: dict) -> tuple:
    """Sort key: capability tier first (Opus → Sonnet → Haiku), then newer
    version before older within a tier."""
    tier_rank = TIER_ORDER.get(entry.get("tier", ""), 99)
    digits = [int(p) for p in re.findall(r"-(\d+)", name)]
    # Negate for descending order (4-7 before 4-1).
    return (tier_rank, tuple(-d for d in digits))


def _is_active(meta: dict, as_of: date | None = None) -> bool:
    """Return True if the LiteLLM entry isn't past its deprecation date."""
    dep = meta.get("deprecation_date")
    if not dep:
        return True
    try:
        return date.fromisoformat(dep) > (as_of or datetime.now(UTC).date())
    except (ValueError, TypeError):
        return True


def _to_per_mtok(per_token: float) -> float:
    """Convert LiteLLM's per-token rate to our per-MTok schema."""
    return round(float(per_token) * 1_000_000, 4)


def _transform_to_models(
    litellm: dict, *, as_of: date | None = None
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name, meta in litellm.items():
        if not isinstance(meta, dict):
            continue
        if meta.get("litellm_provider") != "anthropic":
            continue
        m = CLAUDE_MODEL_PATTERN.match(name)
        if not m:
            continue
        if not _is_active(meta, as_of=as_of):
            continue
        if DATED_VARIANT_SUFFIX.search(name):
            # The bare `claude-opus-4-7` covers all `claude-opus-4-7-YYYYMMDD`.
            continue
        try:
            inp = float(meta["input_cost_per_token"])
            outp = float(meta["output_cost_per_token"])
        except (KeyError, ValueError, TypeError):
            continue
        # Cache fields are sometimes absent. Anthropic's documented multipliers
        # (cache read = 0.10×, 5m create = 1.25×, 1h create = 2.00×) are the
        # safe fallback. LiteLLM has been adding the explicit fields, so this
        # path mostly handles older snapshots.
        cache_read = float(meta.get("cache_read_input_token_cost", inp * 0.10))
        cache_5m = float(meta.get("cache_creation_input_token_cost", inp * 1.25))
        cache_1h = float(
            meta.get("cache_creation_input_token_cost_above_1hr", inp * 2.00)
        )
        out[name] = {
            "tier": m.group(1),
            "input": _to_per_mtok(inp),
            "output": _to_per_mtok(outp),
            "cache_read": _to_per_mtok(cache_read),
            "cache_create_5m": _to_per_mtok(cache_5m),
            "cache_create_1h": _to_per_mtok(cache_1h),
        }
    return dict(sorted(out.items(), key=lambda kv: _model_sort_key(*kv)))


def _build_tier_fallback(models: dict[str, dict]) -> dict[str, dict]:
    """For each tier, pick the cheapest model's pricing as the fallback."""
    by_tier: dict[str, dict] = {}
    for entry in models.values():
        tier = entry["tier"]
        rates = {k: v for k, v in entry.items() if k != "tier"}
        if tier not in by_tier or rates["input"] < by_tier[tier]["input"]:
            by_tier[tier] = rates
    return dict(
        sorted(by_tier.items(), key=lambda kv: TIER_ORDER.get(kv[0], 99))
    )


def _atomic_write(dest: Path, payload: dict) -> None:
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(dest)


def sync_from_litellm(
    dest: Path,
    *,
    fetcher: Callable[[], dict] = _fetch_litellm,
) -> dict:
    """Fetch LiteLLM data and atomically refresh `pricing.json` at `dest`.

    Preserves the existing `plans` block (subscription tiers — LiteLLM doesn't
    carry these). Raises if the fetch or transform produces no Claude models,
    so the caller can fall back to the existing on-disk file.
    """
    litellm = fetcher()
    new_models = _transform_to_models(litellm)
    if not new_models:
        raise RuntimeError("LiteLLM returned no Claude models matching our filter")
    plans: dict[str, dict] = {}
    if dest.is_file():
        try:
            plans = json.loads(dest.read_text()).get("plans", {})
        except (OSError, json.JSONDecodeError):
            plans = {}
    payload = {
        "models": new_models,
        "tier_fallback": _build_tier_fallback(new_models),
        "plans": plans,
    }
    _atomic_write(dest, payload)
    return payload


def is_stale(path: Path, max_age_s: float = DEFAULT_STALE_AGE_S) -> bool:
    """Return True if `path` is older than `max_age_s` (or doesn't exist)."""
    try:
        return (time.time() - path.stat().st_mtime) > max_age_s
    except OSError:
        return True
