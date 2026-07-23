import uuid
from datetime import timedelta

import pytest

from models.subscription import Subscription, SubscriptionPaymentStatus, SubscriptionStatus
from utils.subscription import can_schedule_sessions, current_india_date


def _make_subscription(status: SubscriptionStatus, end_date) -> Subscription:
    today = current_india_date()
    return Subscription(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        plan_name="Premium",
        plan_price=99.99,
        plan_currency="USD",
        plan_duration_days=30,
        start_date=today - timedelta(days=30),
        end_date=end_date,
        status=status,
        payment_status=SubscriptionPaymentStatus.PENDING,
        auto_renew=False,
        notes=None,
    )


def test_can_schedule_sessions_true_for_active_with_future_end_date():
    today = current_india_date()
    subscription = _make_subscription(SubscriptionStatus.ACTIVE, today + timedelta(days=10))

    assert can_schedule_sessions(subscription) is True


def test_can_schedule_sessions_true_for_active_with_end_date_today():
    today = current_india_date()
    subscription = _make_subscription(SubscriptionStatus.ACTIVE, today)

    assert can_schedule_sessions(subscription) is True


@pytest.mark.parametrize(
    "status",
    [SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED, SubscriptionStatus.PAUSED],
)
def test_can_schedule_sessions_false_for_non_active_status(status):
    today = current_india_date()
    subscription = _make_subscription(status, today + timedelta(days=10))

    assert can_schedule_sessions(subscription) is False


def test_can_schedule_sessions_false_for_active_with_past_end_date():
    today = current_india_date()
    subscription = _make_subscription(SubscriptionStatus.ACTIVE, today - timedelta(days=1))

    assert can_schedule_sessions(subscription) is False
