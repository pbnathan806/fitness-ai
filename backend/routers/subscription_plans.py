import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import CurrentUser, get_current_user
from database.session import get_db
from repositories.subscription_plan_repository import (
    SQLAlchemySubscriptionPlanRepository,
    SubscriptionPlanRepository,
)
from schemas.subscription_plan import (
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdateRequest,
)
from services.subscription_plan_service import (
    DuplicatePlanNameError,
    ForbiddenError,
    ImmutableFieldError,
    SubscriptionPlanDetail,
    SubscriptionPlanNotFoundError,
    SubscriptionPlanService,
)

router = APIRouter(prefix="/api/v1/subscription-plans", tags=["subscription-plans"])


def get_subscription_plan_repository(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionPlanRepository:
    return SQLAlchemySubscriptionPlanRepository(session)


def get_subscription_plan_service(
    subscription_plan_repository: SubscriptionPlanRepository = Depends(
        get_subscription_plan_repository
    ),
) -> SubscriptionPlanService:
    return SubscriptionPlanService(subscription_plan_repository)


def _to_response(detail: SubscriptionPlanDetail) -> SubscriptionPlanResponse:
    return SubscriptionPlanResponse(
        id=detail.id,
        name=detail.name,
        description=detail.description,
        duration_days=detail.duration_days,
        price=detail.price,
        currency=detail.currency,
        max_sessions_per_month=detail.max_sessions_per_month,
        sessions_per_week=detail.sessions_per_week,
        is_active=detail.is_active,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


@router.post("", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription_plan(
    payload: SubscriptionPlanCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    subscription_plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service),
) -> SubscriptionPlanResponse:
    try:
        detail = await subscription_plan_service.create_plan(
            actor_role=current_user.active_role,
            name=payload.name,
            description=payload.description,
            duration_days=payload.duration_days,
            price=payload.price,
            currency=payload.currency,
            max_sessions_per_month=payload.max_sessions_per_month,
            sessions_per_week=payload.sessions_per_week,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except DuplicatePlanNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(detail)


@router.get("", response_model=list[SubscriptionPlanResponse], status_code=status.HTTP_200_OK)
async def list_subscription_plans(
    current_user: CurrentUser = Depends(get_current_user),
    subscription_plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service),
) -> list[SubscriptionPlanResponse]:
    items = await subscription_plan_service.list_active_plans()
    return [_to_response(item) for item in items]


@router.get("/{plan_id}", response_model=SubscriptionPlanResponse, status_code=status.HTTP_200_OK)
async def get_subscription_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    subscription_plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service),
) -> SubscriptionPlanResponse:
    try:
        detail = await subscription_plan_service.get_plan(plan_id)
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.put("/{plan_id}", response_model=SubscriptionPlanResponse, status_code=status.HTTP_200_OK)
async def update_subscription_plan(
    plan_id: uuid.UUID,
    payload: SubscriptionPlanUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    subscription_plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service),
) -> SubscriptionPlanResponse:
    values = payload.model_dump(exclude_unset=True)
    try:
        detail = await subscription_plan_service.update_plan(
            actor_role=current_user.active_role,
            plan_id=plan_id,
            values=values,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ImmutableFieldError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SubscriptionPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)
