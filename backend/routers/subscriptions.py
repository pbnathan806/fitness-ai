import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import CurrentUser, get_current_user
from database.session import get_db
from repositories.assignment_repository import (
    AssignmentRepository,
    SQLAlchemyAssignmentRepository,
)
from repositories.client_repository import ClientRepository, SQLAlchemyClientRepository
from repositories.subscription_plan_repository import (
    SQLAlchemySubscriptionPlanRepository,
    SubscriptionPlanRepository,
)
from repositories.subscription_repository import (
    SQLAlchemySubscriptionRepository,
    SubscriptionRepository,
)
from schemas.subscription import (
    ClientSubscriptionResponse,
    PaginatedSubscriptionsResponse,
    SubscriptionCreateRequest,
    SubscriptionEligibilityResponse,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)
from services.subscription_service import (
    ActiveSubscriptionExistsError,
    ClientNotFoundError,
    ClientSubscriptionSummary,
    ForbiddenError,
    SubscriptionDetail,
    SubscriptionEligibility,
    SubscriptionNotFoundError,
    SubscriptionPlanNotFoundError,
    SubscriptionService,
    TrainerNotAssignedError,
)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


def get_subscription_repository(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionRepository:
    return SQLAlchemySubscriptionRepository(session)


def get_subscription_plan_repository(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionPlanRepository:
    return SQLAlchemySubscriptionPlanRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_repository(
    session: AsyncSession = Depends(get_db),
) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_subscription_service(
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository),
    subscription_plan_repository: SubscriptionPlanRepository = Depends(
        get_subscription_plan_repository
    ),
    client_repository: ClientRepository = Depends(get_client_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
) -> SubscriptionService:
    return SubscriptionService(
        subscription_repository,
        subscription_plan_repository,
        client_repository,
        assignment_repository,
    )


def _to_response(detail: SubscriptionDetail) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=detail.id,
        client_id=detail.client_id,
        subscription_plan_id=detail.subscription_plan_id,
        plan_name=detail.plan_name,
        plan_price=detail.plan_price,
        plan_currency=detail.plan_currency,
        plan_duration_days=detail.plan_duration_days,
        start_date=detail.start_date,
        end_date=detail.end_date,
        status=detail.status,
        payment_status=detail.payment_status,
        auto_renew=detail.auto_renew,
        notes=detail.notes,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


def _to_client_response(item: ClientSubscriptionSummary) -> ClientSubscriptionResponse:
    return ClientSubscriptionResponse(
        id=item.id,
        plan_name=item.plan_name,
        plan_price=item.plan_price,
        plan_currency=item.plan_currency,
        payment_status=item.payment_status,
        status=item.status,
        start_date=item.start_date,
        end_date=item.end_date,
    )


def _to_eligibility_response(item: SubscriptionEligibility) -> SubscriptionEligibilityResponse:
    return SubscriptionEligibilityResponse(
        client_id=item.client_id,
        plan_name=item.plan_name,
        status=item.status,
        end_date=item.end_date,
        can_schedule_sessions=item.can_schedule_sessions,
    )


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    try:
        detail = await subscription_service.create_subscription(
            actor_role=current_user.active_role,
            client_id=payload.client_id,
            subscription_plan_id=payload.subscription_plan_id,
            start_date=payload.start_date,
            auto_renew=payload.auto_renew,
            notes=payload.notes,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, SubscriptionPlanNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ActiveSubscriptionExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(detail)


@router.get("", response_model=PaginatedSubscriptionsResponse, status_code=status.HTTP_200_OK)
async def list_subscriptions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> PaginatedSubscriptionsResponse:
    try:
        result = await subscription_service.list_subscriptions(
            actor_role=current_user.active_role,
            page=page,
            page_size=page_size,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    total_pages = (result.total + page_size - 1) // page_size if result.total else 0
    return PaginatedSubscriptionsResponse(
        items=[_to_response(detail) for detail in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )


@router.get(
    "/my-subscriptions",
    response_model=list[ClientSubscriptionResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_subscriptions(
    current_user: CurrentUser = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> list[ClientSubscriptionResponse]:
    try:
        items = await subscription_service.list_my_subscriptions(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_client_response(item) for item in items]


@router.get(
    "/client/{client_id}/eligibility",
    response_model=SubscriptionEligibilityResponse,
    status_code=status.HTTP_200_OK,
)
async def get_client_eligibility(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionEligibilityResponse:
    try:
        item = await subscription_service.get_eligibility(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, SubscriptionNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_eligibility_response(item)


@router.get(
    "/{subscription_id}", response_model=SubscriptionResponse, status_code=status.HTTP_200_OK
)
async def get_subscription(
    subscription_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    try:
        detail = await subscription_service.get_subscription(
            actor_role=current_user.active_role,
            subscription_id=subscription_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.patch(
    "/{subscription_id}", response_model=SubscriptionResponse, status_code=status.HTTP_200_OK
)
async def update_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    values = payload.model_dump(exclude_unset=True)
    try:
        detail = await subscription_service.update_subscription(
            actor_role=current_user.active_role,
            subscription_id=subscription_id,
            values=values,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SubscriptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)
