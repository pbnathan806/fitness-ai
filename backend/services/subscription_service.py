import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from core.constants import RoleName
from models.subscription import Subscription, SubscriptionPaymentStatus, SubscriptionStatus
from repositories.assignment_repository import AssignmentRepository
from repositories.client_repository import ClientRepository
from repositories.subscription_plan_repository import SubscriptionPlanRepository
from repositories.subscription_repository import SubscriptionRepository
from utils.subscription import can_schedule_sessions, current_india_date

# Snapshot/identity fields fixed at creation time; update payloads must not
# change them (Task-16.3.1).
_IMMUTABLE_SUBSCRIPTION_FIELDS = (
    "client_id",
    "subscription_plan_id",
    "plan_name",
    "plan_price",
    "plan_currency",
    "plan_duration_days",
    "start_date",
)


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class ClientNotFoundError(Exception):
    """Raised when no client profile exists for the requested identifier."""


class SubscriptionPlanNotFoundError(Exception):
    """Raised when no subscription plan exists for the requested identifier."""


class SubscriptionNotFoundError(Exception):
    """Raised when no subscription exists for the requested identifier."""


class ActiveSubscriptionExistsError(Exception):
    """Raised when a client already has an ACTIVE subscription."""


class TrainerNotAssignedError(Exception):
    """Raised when a trainer requests eligibility for a client they are not assigned to."""


class ImmutableFieldError(Exception):
    """Raised when an update payload attempts to change an immutable field."""


@dataclass(frozen=True)
class SubscriptionDetail:
    id: uuid.UUID
    client_id: uuid.UUID
    subscription_plan_id: uuid.UUID
    plan_name: str
    plan_price: float
    plan_currency: str
    plan_duration_days: int
    start_date: date
    end_date: date
    status: SubscriptionStatus
    payment_status: SubscriptionPaymentStatus
    auto_renew: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PaginatedSubscriptions:
    items: list[SubscriptionDetail]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True)
class ClientSubscriptionSummary:
    id: uuid.UUID
    plan_name: str
    plan_price: float
    plan_currency: str
    payment_status: SubscriptionPaymentStatus
    status: SubscriptionStatus
    start_date: date
    end_date: date


@dataclass(frozen=True)
class SubscriptionEligibility:
    """Eligibility view for TRAINER/SUPER_ADMIN. Deliberately excludes plan_price,
    plan_currency, payment_status, notes, auto_renew, and subscription ids -
    trainers must never receive financial or historical subscription data.
    """

    client_id: uuid.UUID
    plan_name: str
    status: SubscriptionStatus
    end_date: date
    can_schedule_sessions: bool


def _to_detail(subscription: Subscription) -> SubscriptionDetail:
    return SubscriptionDetail(
        id=subscription.id,
        client_id=subscription.client_id,
        subscription_plan_id=subscription.subscription_plan_id,
        plan_name=subscription.plan_name,
        plan_price=float(subscription.plan_price),
        plan_currency=subscription.plan_currency,
        plan_duration_days=subscription.plan_duration_days,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        status=subscription.status,
        payment_status=subscription.payment_status,
        auto_renew=subscription.auto_renew,
        notes=subscription.notes,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


def _to_summary(subscription: Subscription) -> ClientSubscriptionSummary:
    return ClientSubscriptionSummary(
        id=subscription.id,
        plan_name=subscription.plan_name,
        plan_price=float(subscription.plan_price),
        plan_currency=subscription.plan_currency,
        payment_status=subscription.payment_status,
        status=subscription.status,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
    )


class SubscriptionService:
    """Business logic for client subscriptions and their Version-1 RBAC rules (Task-16.3).

    SUPER_ADMIN has full access to create, read, list, and update
    subscriptions. CLIENT may only list their own subscriptions. TRAINER and
    SUPER_ADMIN may check a client's coaching eligibility, a deliberately
    narrow view that never exposes financial fields, notes, auto-renew, or
    subscription identifiers.
    """

    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        subscription_plan_repository: SubscriptionPlanRepository,
        client_repository: ClientRepository,
        assignment_repository: AssignmentRepository,
    ) -> None:
        self._subscription_repository = subscription_repository
        self._subscription_plan_repository = subscription_plan_repository
        self._client_repository = client_repository
        self._assignment_repository = assignment_repository

    async def create_subscription(
        self,
        actor_role: str | None,
        client_id: uuid.UUID,
        subscription_plan_id: uuid.UUID,
        start_date: date | None,
        auto_renew: bool,
        notes: str | None,
    ) -> SubscriptionDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may create subscriptions.")

        if await self._client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        plan = await self._subscription_plan_repository.get_by_id(subscription_plan_id)
        if plan is None:
            raise SubscriptionPlanNotFoundError(
                f"Subscription plan '{subscription_plan_id}' was not found."
            )

        if await self._subscription_repository.get_active_for_client(client_id) is not None:
            raise ActiveSubscriptionExistsError(
                f"Client '{client_id}' already has an ACTIVE subscription."
            )

        effective_start_date = start_date or current_india_date()
        subscription = await self._subscription_repository.create(
            Subscription(
                client_id=client_id,
                subscription_plan_id=subscription_plan_id,
                plan_name=plan.name,
                plan_price=plan.price,
                plan_currency=plan.currency,
                plan_duration_days=plan.duration_days,
                start_date=effective_start_date,
                end_date=effective_start_date + timedelta(days=plan.duration_days),
                status=SubscriptionStatus.ACTIVE,
                payment_status=SubscriptionPaymentStatus.PENDING,
                auto_renew=auto_renew,
                notes=notes,
            )
        )
        return _to_detail(subscription)

    async def get_subscription(
        self, actor_role: str | None, subscription_id: uuid.UUID
    ) -> SubscriptionDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may view subscriptions.")

        subscription = await self._subscription_repository.get_by_id(subscription_id)
        if subscription is None:
            raise SubscriptionNotFoundError(f"Subscription '{subscription_id}' was not found.")
        return _to_detail(subscription)

    async def list_subscriptions(
        self, actor_role: str | None, page: int, page_size: int
    ) -> PaginatedSubscriptions:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may list subscriptions.")

        offset = (page - 1) * page_size
        subscriptions, total = await self._subscription_repository.list_paginated(
            offset, page_size
        )
        return PaginatedSubscriptions(
            items=[_to_detail(subscription) for subscription in subscriptions],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def list_my_subscriptions(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> list[ClientSubscriptionSummary]:
        if actor_role != RoleName.CLIENT:
            raise ForbiddenError("Only Clients may view their own subscriptions.")

        client_record = await self._client_repository.get_by_user_id(actor_id)
        if client_record is None:
            raise ClientNotFoundError("No client profile exists for the current user.")

        subscriptions = await self._subscription_repository.list_for_client(
            client_record.client.id
        )
        return [_to_summary(subscription) for subscription in subscriptions]

    async def get_eligibility(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> SubscriptionEligibility:
        if actor_role not in (RoleName.TRAINER, RoleName.SUPER_ADMIN):
            raise ForbiddenError(
                "Only Trainers and Super Admins may check subscription eligibility."
            )

        if await self._client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        if actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None or not await self._assignment_repository.exists_for_pair(
                client_id, trainer_id
            ):
                raise TrainerNotAssignedError(f"Trainer is not assigned to client '{client_id}'.")

        subscription = await self._subscription_repository.get_latest_for_client(client_id)
        if subscription is None:
            raise SubscriptionNotFoundError(f"Client '{client_id}' has no subscriptions.")

        return SubscriptionEligibility(
            client_id=client_id,
            plan_name=subscription.plan_name,
            status=subscription.status,
            end_date=subscription.end_date,
            can_schedule_sessions=can_schedule_sessions(subscription),
        )

    async def update_subscription(
        self, actor_role: str | None, subscription_id: uuid.UUID, values: dict
    ) -> SubscriptionDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may update subscriptions.")

        for field in _IMMUTABLE_SUBSCRIPTION_FIELDS:
            if field in values:
                raise ImmutableFieldError(f"{field} is immutable and cannot be updated.")

        if await self._subscription_repository.get_by_id(subscription_id) is None:
            raise SubscriptionNotFoundError(f"Subscription '{subscription_id}' was not found.")

        subscription = await self._subscription_repository.update(subscription_id, values)
        return _to_detail(subscription)
