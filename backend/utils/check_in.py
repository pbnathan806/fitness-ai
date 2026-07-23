from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

CHECK_IN_FIELDS = (
    "sleep_hours",
    "water_intake_liters",
    "energy_level",
    "mood",
    "workout_completed",
    "diet_followed",
    "notes",
)


def at_least_one_checkin_field_required(values: dict) -> bool:
    """True if at least one check-in field in `values` is populated."""
    return any(values.get(field) is not None for field in CHECK_IN_FIELDS)


def check_in_day_range_utc(local_date: date, client_timezone: str) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of `local_date` in the client's timezone.

    Used to look up whether a check-in already exists for that calendar day.
    """
    tz = ZoneInfo(client_timezone)
    start_local = datetime.combine(local_date, time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def one_check_in_per_client_per_day(existing_check_in) -> bool:
    """True if no check-in already exists for the target calendar day."""
    return existing_check_in is None
