from datetime import date, datetime
from zoneinfo import ZoneInfo

from models.subscription import Subscription, SubscriptionStatus

# Trainers and Super Admins operate in Asia/Kolkata per TIMEZONE_REQUIREMENTS.md;
# eligibility and default start dates are evaluated from that perspective.
_ADMIN_TIMEZONE = ZoneInfo("Asia/Kolkata")


def current_india_date() -> date:
    return datetime.now(_ADMIN_TIMEZONE).date()


def can_schedule_sessions(subscription: Subscription) -> bool:
    return (
        subscription.status == SubscriptionStatus.ACTIVE
        and subscription.end_date >= current_india_date()
    )
