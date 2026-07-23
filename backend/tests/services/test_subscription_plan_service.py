import asyncio
import uuid
from datetime import datetime, timezone

import pytest

from core.constants import RoleName
from models.subscription_plan import SubscriptionPlan
from repositories.subscription_plan_repository import SubscriptionPlanRepository
from services.subscription_plan_service import (
    DuplicatePlanNameError,
    ForbiddenError,
    ImmutableFieldError,
    SubscriptionPlanNotFoundError,
    SubscriptionPlanService,
)


class FakeSubscriptionPlanRepository(SubscriptionPlanRepository):
    def __init__(self) -> None:
        self._plans: dict[uuid.UUID, SubscriptionPlan] = {}

    def seed(self, plan: SubscriptionPlan) -> None:
        self._plans[plan.id] = plan

    async def create(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        now = datetime.now(timezone.utc)
        plan.id = plan.id or uuid.uuid4()
        plan.is_active = True
        plan.created_at = now
        plan.updated_at = now
        self._plans[plan.id] = plan
        return plan

    async def get_by_id(self, plan_id: uuid.UUID) -> SubscriptionPlan | None:
        return self._plans.get(plan_id)

    async def get_by_name(self, name: str) -> SubscriptionPlan | None:
        for plan in self._plans.values():
            if plan.name == name:
                return plan
        return None

    async def list_active(self) -> list[SubscriptionPlan]:
        return [plan for plan in self._plans.values() if plan.is_active]

    async def update(self, plan_id: uuid.UUID, values: dict) -> SubscriptionPlan | None:
        plan = self._plans.get(plan_id)
        if plan is None:
            return None
        for key, value in values.items():
            setattr(plan, key, value)
        plan.updated_at = datetime.now(timezone.utc)
        return plan


def _make_plan(**overrides) -> SubscriptionPlan:
    defaults = dict(
        id=uuid.uuid4(),
        name="Premium",
        description="Premium coaching plan.",
        duration_days=30,
        price=99.99,
        currency="USD",
        max_sessions_per_month=8,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SubscriptionPlan(**defaults)


def _make_service() -> tuple[SubscriptionPlanService, FakeSubscriptionPlanRepository]:
    repository = FakeSubscriptionPlanRepository()
    service = SubscriptionPlanService(repository)
    return service, repository


def test_create_plan_succeeds_for_super_admin():
    service, _ = _make_service()

    detail = asyncio.run(
        service.create_plan(
            actor_role=RoleName.SUPER_ADMIN,
            name="Premium",
            description="Premium coaching plan.",
            duration_days=30,
            price=99.99,
            currency="USD",
            max_sessions_per_month=8,
        )
    )

    assert detail.name == "Premium"
    assert detail.is_active is True
    assert detail.duration_days == 30


def test_create_plan_rejects_non_super_admin():
    service, _ = _make_service()

    for role in (RoleName.TRAINER, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(
                service.create_plan(
                    actor_role=role,
                    name="Premium",
                    description=None,
                    duration_days=30,
                    price=99.99,
                    currency="USD",
                    max_sessions_per_month=None,
                )
            )


def test_create_plan_rejects_duplicate_name():
    service, repository = _make_service()
    repository.seed(_make_plan(name="Premium"))

    with pytest.raises(DuplicatePlanNameError):
        asyncio.run(
            service.create_plan(
                actor_role=RoleName.SUPER_ADMIN,
                name="Premium",
                description=None,
                duration_days=30,
                price=49.99,
                currency="USD",
                max_sessions_per_month=None,
            )
        )


def test_list_active_plans_excludes_inactive():
    service, repository = _make_service()
    repository.seed(_make_plan(name="Active Plan", is_active=True))
    repository.seed(_make_plan(name="Inactive Plan", is_active=False))

    plans = asyncio.run(service.list_active_plans())

    assert len(plans) == 1
    assert plans[0].name == "Active Plan"


def test_get_plan_succeeds():
    service, repository = _make_service()
    plan = _make_plan()
    repository.seed(plan)

    detail = asyncio.run(service.get_plan(plan.id))

    assert detail.id == plan.id


def test_get_plan_raises_not_found():
    service, _ = _make_service()

    with pytest.raises(SubscriptionPlanNotFoundError):
        asyncio.run(service.get_plan(uuid.uuid4()))


def test_update_plan_succeeds_for_super_admin():
    service, repository = _make_service()
    plan = _make_plan()
    repository.seed(plan)

    detail = asyncio.run(
        service.update_plan(
            actor_role=RoleName.SUPER_ADMIN,
            plan_id=plan.id,
            values={"price": 149.99, "is_active": False},
        )
    )

    assert detail.price == 149.99
    assert detail.is_active is False


def test_update_plan_does_not_change_immutable_fields_when_not_supplied():
    service, repository = _make_service()
    plan = _make_plan(name="Premium", duration_days=30, currency="USD")
    repository.seed(plan)

    detail = asyncio.run(
        service.update_plan(
            actor_role=RoleName.SUPER_ADMIN,
            plan_id=plan.id,
            values={"description": "Updated description."},
        )
    )

    assert detail.name == "Premium"
    assert detail.duration_days == 30
    assert detail.currency == "USD"
    assert detail.description == "Updated description."


@pytest.mark.parametrize(
    "field, value",
    [("name", "Elite"), ("duration_days", 90), ("currency", "EUR")],
)
def test_update_plan_rejects_immutable_fields(field, value):
    service, repository = _make_service()
    plan = _make_plan(name="Premium", duration_days=30, currency="USD")
    repository.seed(plan)

    with pytest.raises(ImmutableFieldError):
        asyncio.run(
            service.update_plan(
                actor_role=RoleName.SUPER_ADMIN,
                plan_id=plan.id,
                values={field: value},
            )
        )


def test_update_plan_rejects_non_super_admin():
    service, repository = _make_service()
    plan = _make_plan()
    repository.seed(plan)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_plan(
                actor_role=RoleName.TRAINER,
                plan_id=plan.id,
                values={"price": 10.0},
            )
        )


def test_update_plan_raises_not_found():
    service, _ = _make_service()

    with pytest.raises(SubscriptionPlanNotFoundError):
        asyncio.run(
            service.update_plan(
                actor_role=RoleName.SUPER_ADMIN,
                plan_id=uuid.uuid4(),
                values={"price": 10.0},
            )
        )
