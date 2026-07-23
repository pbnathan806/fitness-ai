import uuid
from dataclasses import dataclass
from datetime import datetime

from core.constants import RoleName
from models.subscription_plan import SubscriptionPlan
from repositories.subscription_plan_repository import SubscriptionPlanRepository

# Fixed at creation time; update payloads must not change them (Task-16.3.1).
_IMMUTABLE_PLAN_FIELDS = ("name", "duration_days", "currency")


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class SubscriptionPlanNotFoundError(Exception):
    """Raised when no subscription plan exists for the requested identifier."""


class DuplicatePlanNameError(Exception):
    """Raised when a subscription plan with the requested name already exists."""


class ImmutableFieldError(Exception):
    """Raised when an update payload attempts to change an immutable field."""


@dataclass(frozen=True)
class SubscriptionPlanDetail:
    id: uuid.UUID
    name: str
    description: str | None
    duration_days: int
    price: float
    currency: str
    max_sessions_per_month: int | None
    sessions_per_week: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


def _to_detail(plan: SubscriptionPlan) -> SubscriptionPlanDetail:
    return SubscriptionPlanDetail(
        id=plan.id,
        name=plan.name,
        description=plan.description,
        duration_days=plan.duration_days,
        price=float(plan.price),
        currency=plan.currency,
        max_sessions_per_month=plan.max_sessions_per_month,
        sessions_per_week=plan.sessions_per_week,
        is_active=plan.is_active,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


class SubscriptionPlanService:
    """Business logic for the subscription plan catalog and its Version-1 RBAC rules (Task-16.3).

    SUPER_ADMIN may create and update plans. All authenticated users may view
    active plans and individual plan details; the router requires
    authentication but no specific role for those reads.
    """

    def __init__(self, subscription_plan_repository: SubscriptionPlanRepository) -> None:
        self._subscription_plan_repository = subscription_plan_repository

    async def create_plan(
        self,
        actor_role: str | None,
        name: str,
        description: str | None,
        duration_days: int,
        price: float,
        currency: str,
        max_sessions_per_month: int | None,
        sessions_per_week: int | None = None,
    ) -> SubscriptionPlanDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may create subscription plans.")

        if await self._subscription_plan_repository.get_by_name(name) is not None:
            raise DuplicatePlanNameError(f"A subscription plan named '{name}' already exists.")

        plan = await self._subscription_plan_repository.create(
            SubscriptionPlan(
                name=name,
                description=description,
                duration_days=duration_days,
                price=price,
                currency=currency,
                max_sessions_per_month=max_sessions_per_month,
                sessions_per_week=sessions_per_week,
            )
        )
        return _to_detail(plan)

    async def list_active_plans(self) -> list[SubscriptionPlanDetail]:
        plans = await self._subscription_plan_repository.list_active()
        return [_to_detail(plan) for plan in plans]

    async def get_plan(self, plan_id: uuid.UUID) -> SubscriptionPlanDetail:
        plan = await self._subscription_plan_repository.get_by_id(plan_id)
        if plan is None:
            raise SubscriptionPlanNotFoundError(f"Subscription plan '{plan_id}' was not found.")
        return _to_detail(plan)

    async def update_plan(
        self,
        actor_role: str | None,
        plan_id: uuid.UUID,
        values: dict,
    ) -> SubscriptionPlanDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may update subscription plans.")

        for field in _IMMUTABLE_PLAN_FIELDS:
            if field in values:
                raise ImmutableFieldError(f"{field} is immutable and cannot be updated.")

        if await self._subscription_plan_repository.get_by_id(plan_id) is None:
            raise SubscriptionPlanNotFoundError(f"Subscription plan '{plan_id}' was not found.")

        plan = await self._subscription_plan_repository.update(plan_id, values)
        return _to_detail(plan)
