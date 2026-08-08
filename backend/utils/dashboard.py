from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from utils.check_in import check_in_day_range_utc
from utils.subscription import current_india_date

# Trainer and Super Admin dashboards are always framed in Asia/Kolkata per
# TIMEZONE_REQUIREMENTS.md; "today"/"this week"/"this month" for those roles
# means the IST calendar day/week/month, not each client's own timezone.
_ADMIN_TIMEZONE = ZoneInfo("Asia/Kolkata")


def ist_today_range_utc() -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of "today" in Asia/Kolkata."""
    return check_in_day_range_utc(current_india_date(), "Asia/Kolkata")


def ist_next_days_range_utc(days: int) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of the `days`-day window starting today (IST), inclusive of today."""
    start, _ = ist_today_range_utc()
    return start, start + timedelta(days=days)


def ist_month_range_utc() -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of the current calendar month in Asia/Kolkata."""
    today_local = current_india_date()
    month_start_local = today_local.replace(day=1)
    if month_start_local.month == 12:
        next_month_start_local = month_start_local.replace(year=month_start_local.year + 1, month=1)
    else:
        next_month_start_local = month_start_local.replace(month=month_start_local.month + 1)

    start_local = datetime.combine(month_start_local, time.min, tzinfo=_ADMIN_TIMEZONE)
    end_local = datetime.combine(next_month_start_local, time.min, tzinfo=_ADMIN_TIMEZONE)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def client_local_today(client_timezone: str) -> date:
    return datetime.now(ZoneInfo(client_timezone)).date()


def client_week_range_utc(client_timezone: str) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of the current Monday-Sunday week in the client's timezone."""
    today_local = client_local_today(client_timezone)
    monday_local = today_local - timedelta(days=today_local.weekday())
    start, _ = check_in_day_range_utc(monday_local, client_timezone)
    _, end = check_in_day_range_utc(monday_local + timedelta(days=6), client_timezone)
    return start, end


def client_last_n_days_range_utc(client_timezone: str, days: int) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of the trailing `days`-day window ending today (inclusive), in the client's timezone."""
    today_local = client_local_today(client_timezone)
    start, _ = check_in_day_range_utc(today_local - timedelta(days=days - 1), client_timezone)
    _, end = check_in_day_range_utc(today_local, client_timezone)
    return start, end


def trainer_today_and_tomorrow_range_utc(trainer_timezone: str) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds spanning today and tomorrow, in the trainer's own
    profile timezone."""
    today_local = client_local_today(trainer_timezone)
    start, _ = check_in_day_range_utc(today_local, trainer_timezone)
    _, end = check_in_day_range_utc(today_local + timedelta(days=1), trainer_timezone)
    return start, end


def trainer_today_range_utc(trainer_timezone: str) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of "today" in the trainer's own profile timezone."""
    return check_in_day_range_utc(client_local_today(trainer_timezone), trainer_timezone)


def trainer_next_days_range_utc(trainer_timezone: str, days: int) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of the `days`-day window starting today (trainer's
    own timezone), inclusive of today."""
    start, _ = trainer_today_range_utc(trainer_timezone)
    return start, start + timedelta(days=days)


def trainer_last_n_days_range_utc(trainer_timezone: str, days: int) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of the trailing `days`-day window ending today
    (inclusive), in the trainer's own profile timezone."""
    today_start, today_end = trainer_today_range_utc(trainer_timezone)
    return today_start - timedelta(days=days - 1), today_end


def trainer_month_range_utc(trainer_timezone: str) -> tuple[datetime, datetime]:
    """UTC [start, end) bounds of the current calendar month in the trainer's
    own profile timezone."""
    today_local = client_local_today(trainer_timezone)
    month_start_local = today_local.replace(day=1)
    if month_start_local.month == 12:
        next_month_start_local = month_start_local.replace(year=month_start_local.year + 1, month=1)
    else:
        next_month_start_local = month_start_local.replace(month=month_start_local.month + 1)

    tz = ZoneInfo(trainer_timezone)
    start_local = datetime.combine(month_start_local, time.min, tzinfo=tz)
    end_local = datetime.combine(next_month_start_local, time.min, tzinfo=tz)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def classify_client_state(
    end_date: date | None, today: date, subscription_expired_days: int
) -> str | None:
    """Classify a client's latest subscription as ACTIVE/EXPIRED/INACTIVE per Task-20.

    Returns None if the client has no subscription at all (end_date is None) -
    such clients are excluded from all three dashboard buckets rather than
    forced into one.
    """
    if end_date is None:
        return None
    if today <= end_date:
        return "ACTIVE"
    if (today - end_date).days <= subscription_expired_days:
        return "EXPIRED"
    return "INACTIVE"


def is_physical_assessment_overdue(
    latest_recorded_at: datetime | None,
    today: date,
    physical_assessment_overdue_days: int,
    tz: str = "Asia/Kolkata",
) -> bool:
    """True if a client has no physical assessment, or their latest one is older
    than physical_assessment_overdue_days. `tz` must match whatever timezone
    `today` was computed in - callers using a non-IST framing (e.g. a
    trainer's own profile timezone) must pass that same tz here."""
    if latest_recorded_at is None:
        return True
    latest_local_date = latest_recorded_at.astimezone(ZoneInfo(tz)).date()
    return (today - latest_local_date).days > physical_assessment_overdue_days
