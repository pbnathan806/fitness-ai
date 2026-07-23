from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

# Trainers and Super Admins operate in Asia/Kolkata per TIMEZONE_REQUIREMENTS.md;
# bulk-scheduling start times are interpreted from that perspective.
_ADMIN_TIMEZONE = ZoneInfo("Asia/Kolkata")

Weekday = Literal[
    "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"
]

_WEEKDAY_INDEX: dict[str, int] = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


def generate_bulk_session_starts(
    start_date: date, end_date: date, days: list[str], start_time: time
) -> list[datetime]:
    """Expand a bulk-scheduling request into concrete session start datetimes.

    Trainers and Super Admins operate in Asia/Kolkata per TIMEZONE_REQUIREMENTS.md,
    so start_time is interpreted in that timezone for every date between start_date
    and end_date (inclusive) that falls on one of the requested weekdays, then
    converted to UTC for storage and overlap comparisons.
    """
    weekday_numbers = {_WEEKDAY_INDEX[day] for day in days}
    starts: list[datetime] = []
    current = start_date
    while current <= end_date:
        if current.weekday() in weekday_numbers:
            local_start = datetime.combine(current, start_time, tzinfo=_ADMIN_TIMEZONE)
            starts.append(local_start.astimezone(timezone.utc))
        current += timedelta(days=1)
    return starts
