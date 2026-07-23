from datetime import date, datetime, timedelta, timezone

from utils.dashboard import (
    classify_client_state,
    client_last_n_days_range_utc,
    client_week_range_utc,
    ist_month_range_utc,
    ist_next_days_range_utc,
    ist_today_range_utc,
    is_measurement_overdue,
)


def test_classify_client_state_active_when_end_date_today():
    assert classify_client_state(date(2026, 8, 30), date(2026, 8, 30), 30) == "ACTIVE"


def test_classify_client_state_active_when_end_date_future():
    assert classify_client_state(date(2026, 9, 15), date(2026, 8, 30), 30) == "ACTIVE"


def test_classify_client_state_expired_within_grace_window():
    assert classify_client_state(date(2026, 8, 20), date(2026, 8, 30), 30) == "EXPIRED"


def test_classify_client_state_expired_at_exact_grace_boundary():
    assert classify_client_state(date(2026, 7, 31), date(2026, 8, 30), 30) == "EXPIRED"


def test_classify_client_state_inactive_beyond_grace_window():
    assert classify_client_state(date(2026, 6, 1), date(2026, 8, 30), 30) == "INACTIVE"


def test_classify_client_state_inactive_at_one_day_past_grace_boundary():
    assert classify_client_state(date(2026, 7, 30), date(2026, 8, 30), 30) == "INACTIVE"


def test_classify_client_state_none_when_no_subscription():
    assert classify_client_state(None, date(2026, 8, 30), 30) is None


def test_is_measurement_overdue_when_no_measurement_ever():
    assert is_measurement_overdue(None, date(2026, 8, 30), 14) is True


def test_is_measurement_overdue_false_within_window():
    latest = datetime(2026, 8, 20, tzinfo=timezone.utc)
    assert is_measurement_overdue(latest, date(2026, 8, 30), 14) is False


def test_is_measurement_overdue_true_beyond_window():
    latest = datetime(2026, 8, 1, tzinfo=timezone.utc)
    assert is_measurement_overdue(latest, date(2026, 8, 30), 14) is True


def test_is_measurement_overdue_false_at_exact_boundary():
    latest = datetime(2026, 8, 16, tzinfo=timezone.utc)
    assert is_measurement_overdue(latest, date(2026, 8, 30), 14) is False


def test_ist_today_range_utc_is_24_hours():
    start, end = ist_today_range_utc()
    assert end - start == timedelta(hours=24)


def test_ist_next_days_range_utc_spans_requested_days():
    start, end = ist_next_days_range_utc(7)
    assert end - start == timedelta(hours=24 * 7)


def test_ist_month_range_utc_start_before_end():
    start, end = ist_month_range_utc()
    assert start < end


def test_client_week_range_utc_spans_seven_days():
    # Asia/Kolkata has no DST, so this stays exactly 7*24h regardless of when
    # the suite runs (unlike a DST-observing zone, which would flex by an
    # hour on the week containing a transition).
    start, end = client_week_range_utc("Asia/Kolkata")
    assert end - start == timedelta(hours=24 * 7)


def test_client_last_n_days_range_utc_spans_requested_days():
    start, end = client_last_n_days_range_utc("Asia/Kolkata", 90)
    assert end - start == timedelta(hours=24 * 90)
