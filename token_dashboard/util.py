"""Small shared helpers used by both the CLI and the HTTP server."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

# A 4 a.m. day boundary matches habit-tracking conventions: a 1 a.m.
# coding session counts toward yesterday, not today. Adjust if a future
# settings UI exposes this preference.
DEFAULT_DAY_STARTS_AT_HOUR = 4


def today_range_local(
    day_starts_at_hour: int = DEFAULT_DAY_STARTS_AT_HOUR,
    *,
    offset_days: int = 0,
    now: datetime | None = None,
) -> tuple[str, str, str]:
    """Return a 24-hour window aligned to the user's local cutoff hour.

    The day starts at `day_starts_at_hour` local time, runs for 24 h, and
    is returned as UTC ISO timestamps so the server's string comparison
    against stored UTC timestamps is unambiguous. `offset_days=0` is
    today, `1` is yesterday, etc.

    `now` is overridable for tests; it must carry tzinfo if provided.

    Returns:
        (since_iso_utc, until_iso_utc, day_label_local)
    """
    base = now if now is not None else datetime.now(UTC).astimezone()
    cutoff_today = base.replace(
        hour=day_starts_at_hour, minute=0, second=0, microsecond=0
    )
    start_today = cutoff_today if base >= cutoff_today else cutoff_today - timedelta(days=1)
    start = start_today - timedelta(days=offset_days)
    end = start + timedelta(days=1)
    return (
        start.astimezone(UTC).isoformat(),
        end.astimezone(UTC).isoformat(),
        start.strftime("%Y-%m-%d"),
    )
