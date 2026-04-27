"""Unit tests for token_dashboard.util.today_range_local."""
from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta, timezone

from token_dashboard.util import today_range_local


class TodayRangeLocalTests(unittest.TestCase):
    def test_after_cutoff_returns_today_at_cutoff(self):
        # 10:00 local in UTC+2 — well past the default 4 a.m. cutoff.
        tz = timezone(timedelta(hours=2))
        now = datetime(2026, 4, 25, 10, 0, 0, tzinfo=tz)
        since, until, day = today_range_local(now=now)
        # 4 a.m. local 2026-04-25 in UTC+2 = 2 a.m. UTC same day
        self.assertEqual(since, "2026-04-25T02:00:00+00:00")
        self.assertEqual(until, "2026-04-26T02:00:00+00:00")
        self.assertEqual(day, "2026-04-25")

    def test_before_cutoff_returns_yesterday_at_cutoff(self):
        # 02:00 local in UTC+2 — before the 4 a.m. cutoff so still
        # yesterday's day from a tracking perspective.
        tz = timezone(timedelta(hours=2))
        now = datetime(2026, 4, 25, 2, 0, 0, tzinfo=tz)
        since, until, day = today_range_local(now=now)
        # The "today" started at 4 a.m. local on 2026-04-24
        # = 2 a.m. UTC on 2026-04-24
        self.assertEqual(since, "2026-04-24T02:00:00+00:00")
        self.assertEqual(until, "2026-04-25T02:00:00+00:00")
        self.assertEqual(day, "2026-04-24")

    def test_custom_cutoff_hour(self):
        # Some users prefer a midnight cutoff
        tz = timezone(timedelta(hours=2))
        now = datetime(2026, 4, 25, 1, 0, 0, tzinfo=tz)
        since, _, day = today_range_local(0, now=now)
        # 1 a.m. local is past midnight, so today is 2026-04-25 local
        # = midnight local in UTC+2 = 22:00 UTC on 2026-04-24
        self.assertEqual(since, "2026-04-24T22:00:00+00:00")
        self.assertEqual(day, "2026-04-25")

    def test_utc_timezone(self):
        # User in UTC, 10:00 local = 10:00 UTC, well past 4 a.m.
        now = datetime(2026, 4, 25, 10, 0, 0, tzinfo=UTC)
        since, until, day = today_range_local(now=now)
        self.assertEqual(since, "2026-04-25T04:00:00+00:00")
        self.assertEqual(until, "2026-04-26T04:00:00+00:00")
        self.assertEqual(day, "2026-04-25")

    def test_window_is_exactly_24h(self):
        now = datetime(2026, 4, 25, 15, 0, 0, tzinfo=UTC)
        since, until, _ = today_range_local(now=now)
        s = datetime.fromisoformat(since)
        u = datetime.fromisoformat(until)
        self.assertEqual(u - s, timedelta(days=1))

    def test_offset_days_yesterday(self):
        # 10:00 local UTC+2 on Apr 25 — offset_days=1 should return Apr 24's
        # cutoff window.
        tz = timezone(timedelta(hours=2))
        now = datetime(2026, 4, 25, 10, 0, 0, tzinfo=tz)
        since, until, day = today_range_local(offset_days=1, now=now)
        self.assertEqual(since, "2026-04-24T02:00:00+00:00")
        self.assertEqual(until, "2026-04-25T02:00:00+00:00")
        self.assertEqual(day, "2026-04-24")

    def test_offset_days_before_cutoff(self):
        # 02:00 local UTC+2 — before cutoff, so today's day-label is Apr 24.
        # offset_days=1 should walk back one more cutoff window to Apr 23.
        tz = timezone(timedelta(hours=2))
        now = datetime(2026, 4, 25, 2, 0, 0, tzinfo=tz)
        _, _, day = today_range_local(offset_days=1, now=now)
        self.assertEqual(day, "2026-04-23")

    def test_offset_days_six_back(self):
        now = datetime(2026, 4, 25, 12, 0, 0, tzinfo=UTC)
        _, _, day = today_range_local(offset_days=6, now=now)
        self.assertEqual(day, "2026-04-19")


if __name__ == "__main__":
    unittest.main()
