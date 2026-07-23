from datetime import date, time

from utils.session import generate_bulk_session_starts


def test_generate_bulk_session_starts_matches_requested_weekdays():
    starts = generate_bulk_session_starts(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        days=["MONDAY", "WEDNESDAY", "FRIDAY"],
        start_time=time(19, 0),
    )

    # Aug 2026: Mondays 3/10/17/24/31 (5), Wednesdays 5/12/19/26 (4), Fridays 7/14/21/28 (4).
    assert len(starts) == 13
    weekdays = {start.astimezone().weekday() for start in starts}
    assert weekdays.issubset({0, 2, 4})


def test_generate_bulk_session_starts_is_timezone_aware_utc():
    starts = generate_bulk_session_starts(
        start_date=date(2026, 8, 3),
        end_date=date(2026, 8, 3),
        days=["MONDAY"],
        start_time=time(19, 0),
    )

    assert len(starts) == 1
    start = starts[0]
    assert start.tzinfo is not None
    # 19:00 IST (+05:30) is 13:30 UTC.
    assert start.utcoffset().total_seconds() == 0
    assert (start.hour, start.minute) == (13, 30)


def test_generate_bulk_session_starts_empty_when_no_matching_weekday():
    starts = generate_bulk_session_starts(
        start_date=date(2026, 8, 3),
        end_date=date(2026, 8, 5),
        days=["SUNDAY"],
        start_time=time(9, 0),
    )

    assert starts == []


def test_generate_bulk_session_starts_inclusive_of_end_date():
    starts = generate_bulk_session_starts(
        start_date=date(2026, 8, 3),
        end_date=date(2026, 8, 3),
        days=["MONDAY"],
        start_time=time(7, 0),
    )

    assert len(starts) == 1
