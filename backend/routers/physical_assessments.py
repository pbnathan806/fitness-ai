import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import CurrentUser, get_current_user
from database.session import get_db
from repositories.application_setting_repository import (
    ApplicationSettingRepository,
    SQLAlchemyApplicationSettingRepository,
)
from repositories.assignment_repository import (
    AssignmentRepository,
    SQLAlchemyAssignmentRepository,
)
from repositories.client_repository import ClientRepository, SQLAlchemyClientRepository
from repositories.physical_assessment_repository import (
    PhysicalAssessmentRepository,
    SQLAlchemyPhysicalAssessmentRepository,
)
from schemas.physical_assessment import (
    LatestPhysicalAssessmentResponse,
    PaginatedPhysicalAssessmentsResponse,
    PendingPhysicalAssessmentResponse,
    PendingPhysicalAssessmentsResponse,
    PhysicalAssessmentCreateRequest,
    PhysicalAssessmentResponse,
    PhysicalAssessmentUpdateRequest,
)
from services.application_setting_service import ApplicationSettingService
from services.physical_assessment_service import (
    ClientNotFoundError,
    ForbiddenError,
    PendingPhysicalAssessmentDetail,
    PendingPhysicalAssessments,
    PhysicalAssessmentDetail,
    PhysicalAssessmentEditWindowExpiredError,
    PhysicalAssessmentFieldsRequiredError,
    PhysicalAssessmentNotFoundError,
    PhysicalAssessmentService,
    TrainerNotAssignedError,
    TrainerNotFoundError,
)

router = APIRouter(prefix="/api/v1/physical-assessments", tags=["physical-assessments"])


def get_physical_assessment_repository(
    session: AsyncSession = Depends(get_db),
) -> PhysicalAssessmentRepository:
    return SQLAlchemyPhysicalAssessmentRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_repository(
    session: AsyncSession = Depends(get_db),
) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_application_setting_repository(
    session: AsyncSession = Depends(get_db),
) -> ApplicationSettingRepository:
    return SQLAlchemyApplicationSettingRepository(session)


def get_application_setting_service(
    application_setting_repository: ApplicationSettingRepository = Depends(
        get_application_setting_repository
    ),
) -> ApplicationSettingService:
    return ApplicationSettingService(application_setting_repository)


def get_physical_assessment_service(
    physical_assessment_repository: PhysicalAssessmentRepository = Depends(get_physical_assessment_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
    application_setting_service: ApplicationSettingService = Depends(
        get_application_setting_service
    ),
) -> PhysicalAssessmentService:
    return PhysicalAssessmentService(
        physical_assessment_repository,
        client_repository,
        assignment_repository,
        application_setting_service,
    )


def _to_response(detail: PhysicalAssessmentDetail) -> PhysicalAssessmentResponse:
    return PhysicalAssessmentResponse(
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
        front_photo_url=detail.front_photo_url,
        back_photo_url=detail.back_photo_url,
        side_photo_url=detail.side_photo_url,
        recorded_by=detail.recorded_by,
        recorded_at=detail.recorded_at,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


def _to_pending_response(detail: PendingPhysicalAssessmentDetail) -> PendingPhysicalAssessmentResponse:
    return PendingPhysicalAssessmentResponse(
        client_id=detail.client_id,
        client_name=detail.client_name,
        last_physical_assessment_date=detail.last_physical_assessment_date,
        days_overdue=detail.days_overdue,
    )


def _to_pending_list_response(
    result: PendingPhysicalAssessments,
) -> PendingPhysicalAssessmentsResponse:
    return PendingPhysicalAssessmentsResponse(
        items=[_to_pending_response(item) for item in result.items],
        overdue_threshold_days=result.overdue_threshold_days,
    )


@router.post("", response_model=PhysicalAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_physical_assessment(
    payload: PhysicalAssessmentCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    physical_assessment_service: PhysicalAssessmentService = Depends(get_physical_assessment_service),
) -> PhysicalAssessmentResponse:
    try:
        detail = await physical_assessment_service.create_physical_assessment(
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
    except PhysicalAssessmentFieldsRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _to_response(detail)


@router.get("", response_model=PaginatedPhysicalAssessmentsResponse, status_code=status.HTTP_200_OK)
async def list_physical_assessments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    physical_assessment_service: PhysicalAssessmentService = Depends(get_physical_assessment_service),
) -> PaginatedPhysicalAssessmentsResponse:
    try:
        result = await physical_assessment_service.list_physical_assessments(
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
    return PaginatedPhysicalAssessmentsResponse(
        items=[_to_response(detail) for detail in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )


@router.get(
    "/pending", response_model=PendingPhysicalAssessmentsResponse, status_code=status.HTTP_200_OK
)
async def list_pending_physical_assessments(
    current_user: CurrentUser = Depends(get_current_user),
    physical_assessment_service: PhysicalAssessmentService = Depends(get_physical_assessment_service),
) -> PendingPhysicalAssessmentsResponse:
    try:
        result = await physical_assessment_service.list_pending_physical_assessments(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_pending_list_response(result)


@router.get(
    "/client/{client_id}/latest",
    response_model=LatestPhysicalAssessmentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_latest_physical_assessment(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    physical_assessment_service: PhysicalAssessmentService = Depends(get_physical_assessment_service),
) -> LatestPhysicalAssessmentResponse:
    try:
        detail = await physical_assessment_service.get_latest_physical_assessment(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, PhysicalAssessmentNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return LatestPhysicalAssessmentResponse(**detail.__dict__)


@router.get(
    "/client/{client_id}",
    response_model=list[PhysicalAssessmentResponse],
    status_code=status.HTTP_200_OK,
)
async def get_client_physical_assessments(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    physical_assessment_service: PhysicalAssessmentService = Depends(get_physical_assessment_service),
) -> list[PhysicalAssessmentResponse]:
    try:
        items = await physical_assessment_service.get_client_physical_assessments(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_response(item) for item in items]


@router.get("/{physical_assessment_id}", response_model=PhysicalAssessmentResponse, status_code=status.HTTP_200_OK)
async def get_physical_assessment(
    physical_assessment_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    physical_assessment_service: PhysicalAssessmentService = Depends(get_physical_assessment_service),
) -> PhysicalAssessmentResponse:
    try:
        detail = await physical_assessment_service.get_physical_assessment(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            physical_assessment_id=physical_assessment_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PhysicalAssessmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.patch("/{physical_assessment_id}", response_model=PhysicalAssessmentResponse, status_code=status.HTTP_200_OK)
async def update_physical_assessment(
    physical_assessment_id: uuid.UUID,
    payload: PhysicalAssessmentUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    physical_assessment_service: PhysicalAssessmentService = Depends(get_physical_assessment_service),
) -> PhysicalAssessmentResponse:
    try:
        detail = await physical_assessment_service.update_physical_assessment(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            physical_assessment_id=physical_assessment_id,
            values=payload.model_dump(exclude_unset=True),
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PhysicalAssessmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PhysicalAssessmentFieldsRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PhysicalAssessmentEditWindowExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(detail)
