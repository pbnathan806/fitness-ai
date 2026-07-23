import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import CurrentUser, get_current_user
from database.session import get_db
from repositories.assignment_repository import (
    AssignmentRepository,
    SQLAlchemyAssignmentRepository,
)
from repositories.check_in_repository import CheckInRepository, SQLAlchemyCheckInRepository
from repositories.client_repository import ClientRepository, SQLAlchemyClientRepository
from schemas.check_in import (
    CheckInCreateRequest,
    CheckInResponse,
    LatestCheckInResponse,
    PaginatedCheckInsResponse,
)
from services.check_in_service import (
    CheckInDetail,
    CheckInFieldsRequiredError,
    CheckInNotFoundError,
    CheckInService,
    ClientNotFoundError,
    DuplicateCheckInError,
    ForbiddenError,
    TrainerNotAssignedError,
    TrainerNotFoundError,
)

router = APIRouter(prefix="/api/v1/check-ins", tags=["check-ins"])


def get_check_in_repository(session: AsyncSession = Depends(get_db)) -> CheckInRepository:
    return SQLAlchemyCheckInRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_repository(
    session: AsyncSession = Depends(get_db),
) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_check_in_service(
    check_in_repository: CheckInRepository = Depends(get_check_in_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
) -> CheckInService:
    return CheckInService(check_in_repository, client_repository, assignment_repository)


def _to_response(detail: CheckInDetail) -> CheckInResponse:
    return CheckInResponse(
        id=detail.id,
        client_id=detail.client_id,
        sleep_hours=detail.sleep_hours,
        water_intake_liters=detail.water_intake_liters,
        energy_level=detail.energy_level,
        mood=detail.mood,
        workout_completed=detail.workout_completed,
        diet_followed=detail.diet_followed,
        notes=detail.notes,
        submitted_by=detail.submitted_by,
        submitted_at=detail.submitted_at,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_check_in(
    payload: CheckInCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> CheckInResponse:
    try:
        detail = await check_in_service.create_check_in(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=payload.client_id,
            submitted_at=payload.submitted_at,
            sleep_hours=payload.sleep_hours,
            water_intake_liters=payload.water_intake_liters,
            energy_level=payload.energy_level,
            mood=payload.mood,
            workout_completed=payload.workout_completed,
            diet_followed=payload.diet_followed,
            notes=payload.notes,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CheckInFieldsRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DuplicateCheckInError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(detail)


@router.get("", response_model=PaginatedCheckInsResponse, status_code=status.HTTP_200_OK)
async def list_check_ins(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> PaginatedCheckInsResponse:
    try:
        result = await check_in_service.list_check_ins(
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
    return PaginatedCheckInsResponse(
        items=[_to_response(detail) for detail in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )


@router.get(
    "/client/{client_id}/latest",
    response_model=LatestCheckInResponse,
    status_code=status.HTTP_200_OK,
)
async def get_latest_check_in(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> LatestCheckInResponse:
    try:
        detail = await check_in_service.get_latest_check_in(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, CheckInNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return LatestCheckInResponse(
        sleep_hours=detail.sleep_hours,
        water_intake_liters=detail.water_intake_liters,
        energy_level=detail.energy_level,
        mood=detail.mood,
        workout_completed=detail.workout_completed,
        diet_followed=detail.diet_followed,
        submitted_at=detail.submitted_at,
    )


@router.get(
    "/client/{client_id}",
    response_model=list[CheckInResponse],
    status_code=status.HTTP_200_OK,
)
async def get_client_check_ins(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> list[CheckInResponse]:
    try:
        items = await check_in_service.get_client_check_ins(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_response(item) for item in items]


@router.get("/{check_in_id}", response_model=CheckInResponse, status_code=status.HTTP_200_OK)
async def get_check_in(
    check_in_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> CheckInResponse:
    try:
        detail = await check_in_service.get_check_in(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            check_in_id=check_in_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CheckInNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)
