"""Tests for token_dashboard.pricing_sync.

The fetcher is injected so tests run without network and pin behavior against
known LiteLLM-shaped fixtures.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from token_dashboard.pricing_sync import (
    _build_tier_fallback,
    _transform_to_models,
    is_stale,
    sync_from_litellm,
)

# Minimal LiteLLM-shaped fixture covering the three current Claude tiers
# at their post-Opus-4.5-launch (Nov 2025) per-token rates.
LITELLM_FIXTURE = {
    "claude-opus-4-7": {
        "litellm_provider": "anthropic",
        "input_cost_per_token": 0.000005,
        "output_cost_per_token": 0.000025,
        "cache_read_input_token_cost": 0.0000005,
        "cache_creation_input_token_cost": 0.00000625,
        "cache_creation_input_token_cost_above_1hr": 0.00001,
    },
    "claude-sonnet-4-6": {
        "litellm_provider": "anthropic",
        "input_cost_per_token": 0.000003,
        "output_cost_per_token": 0.000015,
        "cache_read_input_token_cost": 0.0000003,
        "cache_creation_input_token_cost": 0.00000375,
        "cache_creation_input_token_cost_above_1hr": 0.000006,
    },
    "claude-haiku-4-5": {
        "litellm_provider": "anthropic",
        "input_cost_per_token": 0.000001,
        "output_cost_per_token": 0.000005,
        "cache_read_input_token_cost": 0.0000001,
        "cache_creation_input_token_cost": 0.00000125,
        "cache_creation_input_token_cost_above_1hr": 0.000002,
    },
    # Excluded: non-Anthropic provider
    "gpt-4o": {
        "litellm_provider": "openai",
        "input_cost_per_token": 0.0000025,
    },
    # Excluded: Anthropic but not a Claude model
    "anthropic-bedrock-claude-instant": {
        "litellm_provider": "anthropic",
        "input_cost_per_token": 0.0000008,
    },
}


class TransformTests(unittest.TestCase):
    def test_filters_to_anthropic_claude_only(self):
        models = _transform_to_models(LITELLM_FIXTURE)
        self.assertEqual(
            sorted(models.keys()),
            ["claude-haiku-4-5", "claude-opus-4-7", "claude-sonnet-4-6"],
        )

    def test_opus_rates_are_post_launch(self):
        # The bug we're fixing: legacy pricing.json had $15/$75. Post-Nov-2025
        # Opus 4.5+ is $5/$25.
        models = _transform_to_models(LITELLM_FIXTURE)
        self.assertEqual(models["claude-opus-4-7"]["input"], 5.0)
        self.assertEqual(models["claude-opus-4-7"]["output"], 25.0)
        self.assertEqual(models["claude-opus-4-7"]["cache_read"], 0.5)
        self.assertEqual(models["claude-opus-4-7"]["cache_create_5m"], 6.25)
        self.assertEqual(models["claude-opus-4-7"]["cache_create_1h"], 10.0)

    def test_sonnet_rates_unchanged(self):
        models = _transform_to_models(LITELLM_FIXTURE)
        self.assertEqual(models["claude-sonnet-4-6"]["input"], 3.0)
        self.assertEqual(models["claude-sonnet-4-6"]["output"], 15.0)

    def test_haiku_rates_unchanged(self):
        models = _transform_to_models(LITELLM_FIXTURE)
        self.assertEqual(models["claude-haiku-4-5"]["input"], 1.0)
        self.assertEqual(models["claude-haiku-4-5"]["output"], 5.0)

    def test_tier_field_is_set(self):
        models = _transform_to_models(LITELLM_FIXTURE)
        self.assertEqual(models["claude-opus-4-7"]["tier"], "opus")
        self.assertEqual(models["claude-sonnet-4-6"]["tier"], "sonnet")
        self.assertEqual(models["claude-haiku-4-5"]["tier"], "haiku")

    def test_skips_deprecated_models(self):
        from datetime import date
        fixture = {
            "claude-opus-3": {
                "litellm_provider": "anthropic",
                "input_cost_per_token": 0.000015,
                "output_cost_per_token": 0.000075,
                "deprecation_date": "2020-01-01",
            },
            "claude-opus-4-7": LITELLM_FIXTURE["claude-opus-4-7"],
        }
        models = _transform_to_models(fixture, as_of=date(2026, 5, 2))
        self.assertNotIn("claude-opus-3", models)
        self.assertIn("claude-opus-4-7", models)

    def test_keeps_models_with_future_deprecation(self):
        from datetime import date
        fixture = {
            "claude-opus-4-9": {
                "litellm_provider": "anthropic",
                "input_cost_per_token": 0.000005,
                "output_cost_per_token": 0.000025,
                "deprecation_date": "2099-01-01",
            },
        }
        models = _transform_to_models(fixture, as_of=date(2026, 5, 2))
        self.assertIn("claude-opus-4-9", models)

    def test_models_are_sorted_by_tier_then_version_desc(self):
        # Opus before Sonnet before Haiku; newer version before older.
        fixture = {
            "claude-haiku-4-5": LITELLM_FIXTURE["claude-haiku-4-5"],
            "claude-opus-4-5": LITELLM_FIXTURE["claude-opus-4-7"],
            "claude-opus-4-7": LITELLM_FIXTURE["claude-opus-4-7"],
            "claude-sonnet-4-6": LITELLM_FIXTURE["claude-sonnet-4-6"],
            "claude-sonnet-4-5": LITELLM_FIXTURE["claude-sonnet-4-6"],
        }
        models = _transform_to_models(fixture)
        self.assertEqual(
            list(models.keys()),
            [
                "claude-opus-4-7",
                "claude-opus-4-5",
                "claude-sonnet-4-6",
                "claude-sonnet-4-5",
                "claude-haiku-4-5",
            ],
        )

    def test_skips_dated_variants(self):
        # `claude-opus-4-7-20260416` is the dated variant of `claude-opus-4-7`.
        # Keeping only the bare name avoids two entries pointing at the same
        # underlying model.
        fixture = {
            "claude-opus-4-7-20260416": LITELLM_FIXTURE["claude-opus-4-7"],
            "claude-opus-4-7": LITELLM_FIXTURE["claude-opus-4-7"],
        }
        models = _transform_to_models(fixture)
        self.assertNotIn("claude-opus-4-7-20260416", models)
        self.assertIn("claude-opus-4-7", models)

    def test_skips_entries_missing_required_fields(self):
        bad = {
            "claude-opus-broken": {
                "litellm_provider": "anthropic",
                # No input_cost_per_token
            }
        }
        self.assertEqual(_transform_to_models(bad), {})


class TierFallbackTests(unittest.TestCase):
    def test_picks_cheapest_per_tier(self):
        cheap = {
            "tier": "opus", "input": 5.0, "output": 25.0,
            "cache_read": 0.5, "cache_create_5m": 6.25, "cache_create_1h": 10.0,
        }
        expensive = {
            "tier": "opus", "input": 15.0, "output": 75.0,
            "cache_read": 1.5, "cache_create_5m": 18.75, "cache_create_1h": 30.0,
        }
        fb = _build_tier_fallback({"cheap": cheap, "expensive": expensive})
        self.assertEqual(fb["opus"]["input"], 5.0)
        self.assertEqual(fb["opus"]["output"], 25.0)
        self.assertNotIn("tier", fb["opus"])  # Tier name is the key, not a field


class SyncTests(unittest.TestCase):
    def test_writes_atomically_and_preserves_plans(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "pricing.json"
            existing = {
                "models": {},
                "tier_fallback": {},
                "plans": {
                    "api": {"monthly": 0, "label": "API"},
                    "max": {"monthly": 100, "label": "Max"},
                },
            }
            dest.write_text(json.dumps(existing))

            sync_from_litellm(dest, fetcher=lambda: LITELLM_FIXTURE)

            data = json.loads(dest.read_text())
            self.assertEqual(data["plans"], existing["plans"])
            self.assertIn("claude-opus-4-7", data["models"])
            self.assertEqual(data["tier_fallback"]["opus"]["input"], 5.0)
            # No leftover .tmp file
            self.assertFalse((dest.parent / "pricing.json.tmp").exists())

    def test_handles_missing_existing_file(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "pricing.json"
            sync_from_litellm(dest, fetcher=lambda: LITELLM_FIXTURE)
            data = json.loads(dest.read_text())
            self.assertEqual(data["plans"], {})
            self.assertIn("claude-opus-4-7", data["models"])

    def test_empty_litellm_response_raises(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "pricing.json"
            with self.assertRaises(RuntimeError):
                sync_from_litellm(dest, fetcher=lambda: {})


class StalenessTests(unittest.TestCase):
    def test_missing_file_is_stale(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertTrue(is_stale(Path(td) / "absent.json"))

    def test_fresh_file_not_stale(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "fresh.json"
            f.write_text("{}")
            self.assertFalse(is_stale(f, max_age_s=3600))

    def test_old_file_is_stale(self):
        import os
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "old.json"
            f.write_text("{}")
            old = f.stat().st_mtime - 10 * 86400
            os.utime(f, (old, old))
            self.assertTrue(is_stale(f, max_age_s=7 * 86400))


if __name__ == "__main__":
    unittest.main()
