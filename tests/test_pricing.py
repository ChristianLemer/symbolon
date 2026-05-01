import unittest
from pathlib import Path

import token_dashboard
from token_dashboard.pricing import cost_for, format_for_user, load_pricing

PRICING = Path(token_dashboard.__file__).resolve().parent / "pricing.json"


class CostTests(unittest.TestCase):
    def setUp(self):
        self.p = load_pricing(PRICING)

    def _u(self, **kw):
        base = {
            "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0,
            "cache_create_5m_tokens": 0, "cache_create_1h_tokens": 0,
        }
        base.update(kw)
        return base

    def test_known_opus_input_cost(self):
        # Opus 4.5+ pricing — $5/MTok input. (Pre-Nov-2025 rate was $15;
        # if this assertion regresses to $15, pricing.json is back to the
        # legacy Opus 4 / 4.1 / 3 schedule and Opus costs are 3× too high.)
        c = cost_for("claude-opus-4-7", self._u(input_tokens=1_000_000), self.p)
        self.assertAlmostEqual(c["usd"], 5.00, places=4)
        self.assertFalse(c["estimated"])

    def test_known_sonnet_output_cost(self):
        c = cost_for("claude-sonnet-4-6", self._u(output_tokens=1_000_000), self.p)
        self.assertAlmostEqual(c["usd"], 15.00, places=4)

    def test_known_haiku_input_cost(self):
        c = cost_for("claude-haiku-4-5", self._u(input_tokens=1_000_000), self.p)
        self.assertAlmostEqual(c["usd"], 1.00, places=4)

    def test_unknown_opus_falls_back_to_current_tier(self):
        # An unknown future Opus name must NOT inherit legacy rates. The
        # tier_fallback for opus is the cheapest current Opus (4.5+ = $5).
        c = cost_for("claude-opus-9-9-experimental", self._u(input_tokens=1_000_000), self.p)
        self.assertAlmostEqual(c["usd"], 5.00, places=4)
        self.assertTrue(c["estimated"])

    def test_tier_fallback_opus_matches_current_rates(self):
        # Direct fixture pin: tier_fallback.opus must be the post-Nov-2025
        # rate, not the legacy schedule.
        opus_fb = self.p["tier_fallback"]["opus"]
        self.assertEqual(opus_fb["input"], 5.0)
        self.assertEqual(opus_fb["output"], 25.0)
        self.assertEqual(opus_fb["cache_read"], 0.5)
        self.assertEqual(opus_fb["cache_create_5m"], 6.25)
        self.assertEqual(opus_fb["cache_create_1h"], 10.0)

    def test_unknown_unparseable_returns_none(self):
        c = cost_for("custom-local-model", self._u(input_tokens=9999), self.p)
        self.assertIsNone(c["usd"])

    def test_cache_read_cheaper_than_input(self):
        c_in = cost_for("claude-opus-4-7", self._u(input_tokens=1_000_000), self.p)
        c_cr = cost_for("claude-opus-4-7", self._u(cache_read_tokens=1_000_000), self.p)
        self.assertLess(c_cr["usd"], c_in["usd"])


class PlanFormatTests(unittest.TestCase):
    def setUp(self):
        self.p = load_pricing(PRICING)

    def test_api_plan_returns_raw(self):
        out = format_for_user(12.34, "api", self.p)
        self.assertEqual(out["display_usd"], 12.34)
        self.assertIsNone(out["subscription_usd"])

    def test_pro_plan_returns_subscription_subtitle(self):
        out = format_for_user(12.34, "pro", self.p)
        self.assertEqual(out["subscription_usd"], 20)
        self.assertIn("Pro", out["subtitle"])


if __name__ == "__main__":
    unittest.main()
