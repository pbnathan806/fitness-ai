import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from core.constants import RoleName
from models.client_trainer_assignment import ClientTrainerAssignment
from models.subscription import Subscription, SubscriptionPaymentStatus, SubscriptionStatus
from repositories.subscription_repository import SubscriptionRepository
from services.subscription_service import (
    ActiveSubscriptionExistsError,
    ClientNotFoundError,
    ForbiddenError,
    ImmutableFieldError,
    SubscriptionNotFoundError,
    SubscriptionPlanNotFoundError,
    SubscriptionService,
    TrainerNotAssignedError,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_subscription_plan_service import FakeSubscriptionPlanRepository, _make_plan


class FakeSubscriptionRepository(SubscriptionRepository):
    def __init__(self) -> None:
        self._subscriptions: dict[uuid.UUID, Subscription] = {}

    def seed(self, subscription: Subscription) -> None:
        self._subscriptions[subscription.id] = subscription

    async def create(self, subscription: Subscription) -> Subscription:
        now = datetime.now(timezone.utc)
        subscription.id = subscription.id or uuid.uuid4()
        subscription.created_at = now
        subscription.updated_at = now
        self._subscriptions[subscription.id] = subscription
        return subscription

    async def get_by_id(self, subscription_id: uuid.UUID) -> Subscription | None:
        return self._subscriptions.get(subscription_id)

    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[list[Subscription], int]:
        ordered = sorted(
            self._subscriptions.values(), key=lambda s: s.created_at, reverse=True
        )
        page = ordered[offset : offset + limit]
        return page, len(ordered)

    async def list_for_client(self, client_id: uuid.UUID) -> list[Subscription]:
        return sorted(
            (s for s in self._subscriptions.values() if s.client_id == client_id),
            key=lambda s: s.start_date,
            reverse=True,
        )

    async def get_active_for_client(self, client_id: uuid.UUID) -> Subscription | None:
        for subscription in self._subscriptions.values():
            if (
                subscription.client_id == client_id
                and subscription.status == SubscriptionStatus.ACTIVE
            ):
                return subscription
        return None

    async def get_latest_for_client(self, client_id: uuid.UUID) -> Subscription | None:
        matches = sorted(
            (s for s in self._subscriptions.values() if s.client_id == client_id),
            key=lambda s: (s.start_date, s.created_at),
            reverse=True,
        )
        return matches[0] if matches else None

    async def update(self, subscription_id: uuid.UUID, values: dict) -> Subscription | None:
        subscription = self._subscriptions.get(subscription_id)
        if subscription is None:
            return None
        for key, value in values.items():
            setattr(subscription, key, value)
        subscription.updated_at = datetime.now(timezone.utc)
        return subscription

    async def get_latest_end_dates_for_clients(
        self, client_ids: list[uuid.UUID] | None = None
    ) -> dict[uuid.UUID, date]:
        by_client: dict[uuid.UUID, list[Subscription]] = {}
        for subscription in self._subscriptions.values():
            if client_ids is not None and subscription.client_id not in client_ids:
                continue
            by_client.setdefault(subscription.client_id, []).append(subscription)

        latest_end_dates: dict[uuid.UUID, date] = {}
        for client_id, subscriptions in by_client.items():
            latest = sorted(subscriptions, key=lambda s: (s.start_date, s.created_at))[-1]
            latest_end_dates[client_id] = latest.end_date
        return latest_end_dates


def _make_subscription(client_id: uuid.UUID, plan_id: uuid.UUID, **overrides) -> Subscription:
    today = date.today()
    defaults = dict(
        id=uuid.uuid4(),
        client_id=client_id,
        subscription_plan_id=plan_id,
        plan_name="Premium",
        plan_price=99.99,
        plan_currency="USD",
        plan_duration_days=30,
        start_date=today,
        end_date=today + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        payment_status=SubscriptionPaymentStatus.PENDING,
        auto_renew=False,
        notes=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Subscription(**defaults)


def _make_service() -> tuple[
    SubscriptionService,
    FakeSubscriptionRepository,
    FakeSubscriptionPlanRepository,
    FakeClientRepository,
    FakeAssignmentRepository,
]:
    subscription_repository = FakeSubscriptionRepository()
    subscription_plan_repository = FakeSubscriptionPlanRepository()
    client_repository = FakeClientRepository()
    assignment_repository = FakeAssignmentRepository()
    service = SubscriptionService(
        subscription_repository,
        subscription_plan_repository,
        client_repository,
        assignment_repository,
    )
    return (
        service,
        subscription_repository,
        subscription_plan_repository,
        client_repository,
        assignment_repository,
    )


def test_create_subscription_succeeds_for_super_admin():
    service, _, plan_repository, client_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    plan = _make_plan(duration_days=30)
    client_repository.seed(client, "client@example.com")
    plan_repository.seed(plan)

    detail = asyncio.run(
        service.create_subscription(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            subscription_plan_id=plan.id,
            start_date=date(2026, 1, 1),
            auto_renew=False,
            notes=None,
        )
    )

    assert detail.client_id == client.id
    assert detail.plan_name == plan.name
    assert detail.plan_price == plan.price
    assert detail.plan_currency == plan.currency
    assert detail.plan_duration_days == plan.duration_days
    assert detail.start_date == date(2026, 1, 1)
    assert detail.end_date == date(2026, 1, 31)
    assert detail.status == SubscriptionStatus.ACTIVE
    assert detail.payment_status == SubscriptionPaymentStatus.PENDING


def test_create_subscription_rejects_non_super_admin():
    service, _, plan_repository, client_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    plan = _make_plan()
    client_repository.seed(client, "client@example.com")
    plan_repository.seed(plan)

    for role in (RoleName.TRAINER, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(
                service.create_subscription(
                    actor_role=role,
                    client_id=client.id,
                    subscription_plan_id=plan.id,
                    start_date=None,
                    auto_renew=False,
                    notes=None,
                )
            )


def test_create_subscription_raises_when_client_missing():
    service, _, plan_repository, _, _ = _make_service()
    plan = _make_plan()
    plan_repository.seed(plan)

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.create_subscription(
                actor_role=RoleName.SUPER_ADMIN,
                client_id=uuid.uuid4(),
                subscription_plan_id=plan.id,
                start_date=None,
                auto_renew=False,
                notes=None,
            )
        )


def test_create_subscription_raises_when_plan_missing():
    service, _, _, client_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    with pytest.raises(SubscriptionPlanNotFoundError):
        asyncio.run(
            service.create_subscription(
                actor_role=RoleName.SUPER_ADMIN,
                client_id=client.id,
                subscription_plan_id=uuid.uuid4(),
                start_date=None,
                auto_renew=False,
                notes=None,
            )
        )


def test_create_subscription_rejects_duplicate_active_subscription():
    service, _, plan_repository, client_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    plan = _make_plan()
    client_repository.seed(client, "client@example.com")
    plan_repository.seed(plan)
    asyncio.run(
        service.create_subscription(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            subscription_plan_id=plan.id,
            start_date=None,
            auto_renew=False,
            notes=None,
        )
    )

    with pytest.raises(ActiveSubscriptionExistsError):
        asyncio.run(
            service.create_subscription(
                actor_role=RoleName.SUPER_ADMIN,
                client_id=client.id,
                subscription_plan_id=plan.id,
                start_date=None,
                auto_renew=False,
                notes=None,
            )
        )


def test_get_subscription_succeeds_for_super_admin():
    service, subscription_repository, _, _, _ = _make_service()
    subscription = _make_subscription(uuid.uuid4(), uuid.uuid4())
    subscription_repository.seed(subscription)

    detail = asyncio.run(
        service.get_subscription(actor_role=RoleName.SUPER_ADMIN, subscription_id=subscription.id)
    )

    assert detail.id == subscription.id


def test_get_subscription_rejects_non_super_admin():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_subscription(actor_role=RoleName.CLIENT, subscription_id=uuid.uuid4())
        )


def test_get_subscription_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(SubscriptionNotFoundError):
        asyncio.run(
            service.get_subscription(
                actor_role=RoleName.SUPER_ADMIN, subscription_id=uuid.uuid4()
            )
        )


def test_list_subscriptions_succeeds_for_super_admin_with_pagination():
    service, subscription_repository, _, _, _ = _make_service()
    for _ in range(3):
        subscription_repository.seed(_make_subscription(uuid.uuid4(), uuid.uuid4()))

    result = asyncio.run(
        service.list_subscriptions(actor_role=RoleName.SUPER_ADMIN, page=1, page_size=2)
    )

    assert result.total == 3
    assert len(result.items) == 2


def test_list_subscriptions_rejects_non_super_admin():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(service.list_subscriptions(actor_role=RoleName.TRAINER, page=1, page_size=20))


def test_list_my_subscriptions_returns_only_own_subscriptions_for_client():
    service, subscription_repository, _, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    subscription_repository.seed(_make_subscription(client.id, uuid.uuid4(), plan_name="Mine"))
    subscription_repository.seed(
        _make_subscription(other_client.id, uuid.uuid4(), plan_name="Not Mine")
    )

    items = asyncio.run(
        service.list_my_subscriptions(actor_role=RoleName.CLIENT, actor_id=client_user_id)
    )

    assert len(items) == 1
    assert items[0].plan_name == "Mine"


def test_list_my_subscriptions_rejects_non_client():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.list_my_subscriptions(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4())
        )


def test_list_my_subscriptions_raises_when_no_client_profile():
    service, *_ = _make_service()

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.list_my_subscriptions(actor_role=RoleName.CLIENT, actor_id=uuid.uuid4())
        )


def test_get_eligibility_succeeds_for_assigned_trainer():
    service, subscription_repository, _, client_repository, assignment_repository = (
        _make_service()
    )
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_trainer(trainer)
    assignment_repository.seed_assignment(
        ClientTrainerAssignment(
            id=uuid.uuid4(), client_id=client.id, trainer_id=trainer.id, is_primary=True
        )
    )
    subscription_repository.seed(
        _make_subscription(
            client.id,
            uuid.uuid4(),
            plan_name="Premium",
            status=SubscriptionStatus.ACTIVE,
            end_date=date.today() + timedelta(days=10),
        )
    )

    eligibility = asyncio.run(
        service.get_eligibility(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, client_id=client.id
        )
    )

    assert eligibility.client_id == client.id
    assert eligibility.plan_name == "Premium"
    assert eligibility.status == SubscriptionStatus.ACTIVE
    assert eligibility.can_schedule_sessions is True


def test_get_eligibility_rejects_unassigned_trainer():
    service, subscription_repository, _, client_repository, assignment_repository = (
        _make_service()
    )
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_trainer(trainer)
    subscription_repository.seed(_make_subscription(client.id, uuid.uuid4()))

    with pytest.raises(TrainerNotAssignedError):
        asyncio.run(
            service.get_eligibility(
                actor_role=RoleName.TRAINER, actor_id=trainer_user_id, client_id=client.id
            )
        )


def test_get_eligibility_rejects_client_role():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_eligibility(
                actor_role=RoleName.CLIENT, actor_id=uuid.uuid4(), client_id=uuid.uuid4()
            )
        )


def test_get_eligibility_succeeds_for_super_admin_without_assignment_check():
    service, subscription_repository, _, client_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    subscription_repository.seed(
        _make_subscription(
            client.id, uuid.uuid4(), status=SubscriptionStatus.EXPIRED, end_date=date.today()
        )
    )

    eligibility = asyncio.run(
        service.get_eligibility(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
        )
    )

    assert eligibility.can_schedule_sessions is False


def test_get_eligibility_excludes_financial_fields():
    service, subscription_repository, _, client_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    subscription_repository.seed(_make_subscription(client.id, uuid.uuid4()))

    eligibility = asyncio.run(
        service.get_eligibility(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
        )
    )

    eligibility_fields = set(eligibility.__dataclass_fields__.keys())
    assert eligibility_fields == {"client_id", "plan_name", "status", "end_date", "can_schedule_sessions"}


def test_get_eligibility_raises_when_client_missing():
    service, *_ = _make_service()

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.get_eligibility(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=uuid.uuid4()
            )
        )


def test_get_eligibility_raises_when_no_subscription_exists():
    service, _, _, client_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    with pytest.raises(SubscriptionNotFoundError):
        asyncio.run(
            service.get_eligibility(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
            )
        )


def test_update_subscription_succeeds_for_super_admin():
    service, subscription_repository, _, _, _ = _make_service()
    subscription = _make_subscription(uuid.uuid4(), uuid.uuid4())
    subscription_repository.seed(subscription)

    detail = asyncio.run(
        service.update_subscription(
            actor_role=RoleName.SUPER_ADMIN,
            subscription_id=subscription.id,
            values={
                "status": SubscriptionStatus.CANCELLED,
                "payment_status": SubscriptionPaymentStatus.PAID,
                "notes": "Cancelled by request.",
            },
        )
    )

    assert detail.status == SubscriptionStatus.CANCELLED
    assert detail.payment_status == SubscriptionPaymentStatus.PAID
    assert detail.notes == "Cancelled by request."


def test_update_subscription_does_not_change_immutable_fields_when_not_supplied():
    service, subscription_repository, _, _, _ = _make_service()
    client_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    subscription = _make_subscription(client_id, plan_id, plan_name="Premium")
    subscription_repository.seed(subscription)

    detail = asyncio.run(
        service.update_subscription(
            actor_role=RoleName.SUPER_ADMIN,
            subscription_id=subscription.id,
            values={"auto_renew": True},
        )
    )

    assert detail.client_id == client_id
    assert detail.subscription_plan_id == plan_id
    assert detail.plan_name == "Premium"
    assert detail.auto_renew is True


@pytest.mark.parametrize(
    "field, value",
    [
        ("client_id", str(uuid.uuid4())),
        ("subscription_plan_id", str(uuid.uuid4())),
        ("plan_name", "Elite"),
        ("plan_price", 199.99),
        ("plan_currency", "EUR"),
        ("plan_duration_days", 90),
        ("start_date", date(2026, 1, 1)),
    ],
)
def test_update_subscription_rejects_immutable_fields(field, value):
    service, subscription_repository, _, _, _ = _make_service()
    subscription = _make_subscription(uuid.uuid4(), uuid.uuid4())
    subscription_repository.seed(subscription)

    with pytest.raises(ImmutableFieldError):
        asyncio.run(
            service.update_subscription(
                actor_role=RoleName.SUPER_ADMIN,
                subscription_id=subscription.id,
                values={field: value},
            )
        )


def test_update_subscription_rejects_non_super_admin():
    service, subscription_repository, _, _, _ = _make_service()
    subscription = _make_subscription(uuid.uuid4(), uuid.uuid4())
    subscription_repository.seed(subscription)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_subscription(
                actor_role=RoleName.TRAINER,
                subscription_id=subscription.id,
                values={"status": SubscriptionStatus.CANCELLED},
            )
        )


def test_update_subscription_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(SubscriptionNotFoundError):
        asyncio.run(
            service.update_subscription(
                actor_role=RoleName.SUPER_ADMIN,
                subscription_id=uuid.uuid4(),
                values={"status": SubscriptionStatus.CANCELLED},
            )
        )
