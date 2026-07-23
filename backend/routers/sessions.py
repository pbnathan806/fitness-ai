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
from repositories.session_repository import SessionRepository, SQLAlchemySessionRepository
from repositories.subscription_plan_repository import (
    SQLAlchemySubscriptionPlanRepository,
    SubscriptionPlanRepository,
)
from repositories.subscription_repository import (
    SQLAlchemySubscriptionRepository,
    SubscriptionRepository,
)
from schemas.session import (
    PaginatedSessionsResponse,
    SessionBulkCreateRequest,
    SessionBulkCreateResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionUpdateRequest,
)
from services.session_service import (
    ClientNotFoundError,
    ClientOverlapError,
    ForbiddenError,
    SessionDetail,
    SessionInPastError,
    SessionLimitReachedError,
    SessionNotFoundError,
    SessionService,
    SubscriptionNotEligibleError,
    TrainerNotAssignedError,
    TrainerNotFoundError,
    TrainerOverlapError,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


def get_session_repository(session: AsyncSession = Depends(get_db)) -> SessionRepository:
    return SQLAlchemySessionRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_repository(
    session: AsyncSession = Depends(get_db),
) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_subscription_repository(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionRepository:
    return SQLAlchemySubscriptionRepository(session)


def get_subscription_plan_repository(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionPlanRepository:
    return SQLAlchemySubscriptionPlanRepository(session)


def get_session_service(
    session_repository: SessionRepository = Depends(get_session_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository),
    subscription_plan_repository: SubscriptionPlanRepository = Depends(
        get_subscription_plan_repository
    ),
) -> SessionService:
    return SessionService(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        subscription_plan_repository,
    )


def _to_response(detail: SessionDetail) -> SessionResponse:
    return SessionResponse(
        id=detail.id,
        client_id=detail.client_id,
        trainer_id=detail.trainer_id,
        scheduled_start=detail.scheduled_start,
        scheduled_end=detail.scheduled_end,
        duration_minutes=detail.duration_minutes,
        status=detail.status,
        meeting_type=detail.meeting_type,
        meeting_link=detail.meeting_link,
        trainer_notes=detail.trainer_notes,
        client_notes=detail.client_notes,
        attendance_status=detail.attendance_status,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        detail = await session_service.create_session(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=payload.client_id,
            trainer_id=payload.trainer_id,
            scheduled_start=payload.scheduled_start,
            duration_minutes=payload.duration_minutes,
            meeting_type=payload.meeting_type,
            meeting_link=payload.meeting_link,
            trainer_notes=payload.trainer_notes,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, TrainerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SessionInPastError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (
        SubscriptionNotEligibleError,
        ClientOverlapError,
        TrainerOverlapError,
        SessionLimitReachedError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(detail)


@router.post(
    "/bulk", response_model=SessionBulkCreateResponse, status_code=status.HTTP_201_CREATED
)
async def bulk_create_sessions(
    payload: SessionBulkCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
) -> SessionBulkCreateResponse:
    try:
        result = await session_service.bulk_create_sessions(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=payload.client_id,
            trainer_id=payload.trainer_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            days=payload.days,
            start_time=payload.start_time,
            duration_minutes=payload.duration_minutes,
            meeting_type=payload.meeting_type,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, TrainerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SubscriptionNotEligibleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return SessionBulkCreateResponse(
        sessions_created=result.sessions_created,
        sessions_skipped=result.sessions_skipped,
        skipped_reasons=result.skipped_reasons,
    )


@router.get("", response_model=PaginatedSessionsResponse, status_code=status.HTTP_200_OK)
async def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
) -> PaginatedSessionsResponse:
    try:
        result = await session_service.list_sessions(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            page=page,
            page_size=page_size,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, TrainerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    total_pages = (result.total + page_size - 1) // page_size if result.total else 0
    return PaginatedSessionsResponse(
        items=[_to_response(detail) for detail in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )


@router.get(
    "/my-sessions", response_model=list[SessionResponse], status_code=status.HTTP_200_OK
)
async def get_my_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
) -> list[SessionResponse]:
    try:
        items = await session_service.list_my_sessions(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_response(item) for item in items]


@router.get("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def get_session(
    session_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        detail = await session_service.get_session(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            session_id=session_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.patch("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def update_session(
    session_id: uuid.UUID,
    payload: SessionUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    values = payload.model_dump(exclude_unset=True)
    try:
        detail = await session_service.update_session(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            session_id=session_id,
            values=values,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)
