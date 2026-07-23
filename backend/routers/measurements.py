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
from repositories.measurement_repository import (
    MeasurementRepository,
    SQLAlchemyMeasurementRepository,
)
from schemas.measurement import (
    LatestMeasurementResponse,
    MeasurementCreateRequest,
    MeasurementResponse,
    PaginatedMeasurementsResponse,
)
from services.measurement_service import (
    ClientNotFoundError,
    ForbiddenError,
    MeasurementDetail,
    MeasurementFieldsRequiredError,
    MeasurementNotFoundError,
    MeasurementService,
    TrainerNotAssignedError,
    TrainerNotFoundError,
)

router = APIRouter(prefix="/api/v1/measurements", tags=["measurements"])


def get_measurement_repository(
    session: AsyncSession = Depends(get_db),
) -> MeasurementRepository:
    return SQLAlchemyMeasurementRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_repository(
    session: AsyncSession = Depends(get_db),
) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_measurement_service(
    measurement_repository: MeasurementRepository = Depends(get_measurement_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
) -> MeasurementService:
    return MeasurementService(measurement_repository, client_repository, assignment_repository)


def _to_response(detail: MeasurementDetail) -> MeasurementResponse:
    return MeasurementResponse(
        id=detail.id,
        client_id=detail.client_id,
        weight_kg=detail.weight_kg,
        body_fat_percentage=detail.body_fat_percentage,
        chest_cm=detail.chest_cm,
        waist_cm=detail.waist_cm,
        hips_cm=detail.hips_cm,
        left_arm_cm=detail.left_arm_cm,
        right_arm_cm=detail.right_arm_cm,
        left_thigh_cm=detail.left_thigh_cm,
        right_thigh_cm=detail.right_thigh_cm,
        resting_heart_rate=detail.resting_heart_rate,
        recorded_by=detail.recorded_by,
        recorded_at=detail.recorded_at,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


@router.post("", response_model=MeasurementResponse, status_code=status.HTTP_201_CREATED)
async def create_measurement(
    payload: MeasurementCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    measurement_service: MeasurementService = Depends(get_measurement_service),
) -> MeasurementResponse:
    try:
        detail = await measurement_service.create_measurement(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=payload.client_id,
            recorded_at=payload.recorded_at,
            weight_kg=payload.weight_kg,
            body_fat_percentage=payload.body_fat_percentage,
            chest_cm=payload.chest_cm,
            waist_cm=payload.waist_cm,
            hips_cm=payload.hips_cm,
            left_arm_cm=payload.left_arm_cm,
            right_arm_cm=payload.right_arm_cm,
            left_thigh_cm=payload.left_thigh_cm,
            right_thigh_cm=payload.right_thigh_cm,
            resting_heart_rate=payload.resting_heart_rate,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except MeasurementFieldsRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _to_response(detail)


@router.get("", response_model=PaginatedMeasurementsResponse, status_code=status.HTTP_200_OK)
async def list_measurements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    measurement_service: MeasurementService = Depends(get_measurement_service),
) -> PaginatedMeasurementsResponse:
    try:
        result = await measurement_service.list_measurements(
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
    return PaginatedMeasurementsResponse(
        items=[_to_response(detail) for detail in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )


@router.get(
    "/client/{client_id}/latest",
    response_model=LatestMeasurementResponse,
    status_code=status.HTTP_200_OK,
)
async def get_latest_measurement(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    measurement_service: MeasurementService = Depends(get_measurement_service),
) -> LatestMeasurementResponse:
    try:
        detail = await measurement_service.get_latest_measurement(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, MeasurementNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return LatestMeasurementResponse(**detail.__dict__)


@router.get(
    "/client/{client_id}",
    response_model=list[MeasurementResponse],
    status_code=status.HTTP_200_OK,
)
async def get_client_measurements(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    measurement_service: MeasurementService = Depends(get_measurement_service),
) -> list[MeasurementResponse]:
    try:
        items = await measurement_service.get_client_measurements(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_response(item) for item in items]


@router.get("/{measurement_id}", response_model=MeasurementResponse, status_code=status.HTTP_200_OK)
async def get_measurement(
    measurement_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    measurement_service: MeasurementService = Depends(get_measurement_service),
) -> MeasurementResponse:
    try:
        detail = await measurement_service.get_measurement(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            measurement_id=measurement_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except MeasurementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)
