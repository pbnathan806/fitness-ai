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
from schemas.assignment import (
    AssignedClientResponse,
    AssignedTrainerResponse,
    AssignmentCreateRequest,
    AssignmentResponse,
    PaginatedAssignmentsResponse,
)
from services.assignment_service import (
    AssignedClient,
    AssignedTrainer,
    AssignmentDetail,
    AssignmentNotFoundError,
    AssignmentService,
    ClientNotFoundError,
    DuplicateAssignmentError,
    ForbiddenError,
    PrimaryTrainerExistsError,
    TrainerNotFoundError,
)

router = APIRouter(prefix="/api/v1/assignments", tags=["assignments"])


def get_assignment_repository(
    session: AsyncSession = Depends(get_db),
) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_service(
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
) -> AssignmentService:
    return AssignmentService(assignment_repository, client_repository)


def _to_response(detail: AssignmentDetail) -> AssignmentResponse:
    return AssignmentResponse(
        id=detail.id,
        client_id=detail.client_id,
        trainer_id=detail.trainer_id,
        is_primary=detail.is_primary,
        assigned_at=detail.assigned_at,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


def _to_client_response(item: AssignedClient) -> AssignedClientResponse:
    return AssignedClientResponse(
        assignment_id=item.assignment_id,
        client_id=item.client_id,
        first_name=item.first_name,
        last_name=item.last_name,
        email=item.email,
        phone_number=item.phone_number,
        timezone=item.timezone,
        is_primary=item.is_primary,
    )


def _to_trainer_response(item: AssignedTrainer) -> AssignedTrainerResponse:
    return AssignedTrainerResponse(
        assignment_id=item.assignment_id,
        trainer_id=item.trainer_id,
        specialization=item.specialization,
        experience_years=item.experience_years,
        bio=item.bio,
        timezone=item.timezone,
        country=item.country,
        email=item.email,
        is_primary=item.is_primary,
    )


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: AssignmentCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponse:
    try:
        detail = await assignment_service.create_assignment(
            actor_role=current_user.active_role,
            client_id=payload.client_id,
            trainer_id=payload.trainer_id,
            is_primary=payload.is_primary,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, TrainerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (DuplicateAssignmentError, PrimaryTrainerExistsError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(detail)


@router.get("", response_model=PaginatedAssignmentsResponse, status_code=status.HTTP_200_OK)
async def list_assignments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> PaginatedAssignmentsResponse:
    try:
        result = await assignment_service.list_assignments(
            actor_role=current_user.active_role,
            page=page,
            page_size=page_size,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    total_pages = (result.total + page_size - 1) // page_size if result.total else 0
    return PaginatedAssignmentsResponse(
        items=[_to_response(detail) for detail in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )


@router.get(
    "/my-clients", response_model=list[AssignedClientResponse], status_code=status.HTTP_200_OK
)
async def get_my_clients(
    current_user: CurrentUser = Depends(get_current_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> list[AssignedClientResponse]:
    try:
        items = await assignment_service.list_my_clients(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_client_response(item) for item in items]


@router.get(
    "/my-trainers", response_model=list[AssignedTrainerResponse], status_code=status.HTTP_200_OK
)
async def get_my_trainers(
    current_user: CurrentUser = Depends(get_current_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> list[AssignedTrainerResponse]:
    try:
        items = await assignment_service.list_my_trainers(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_trainer_response(item) for item in items]


@router.get("/{assignment_id}", response_model=AssignmentResponse, status_code=status.HTTP_200_OK)
async def get_assignment(
    assignment_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponse:
    try:
        detail = await assignment_service.get_assignment(
            actor_role=current_user.active_role,
            assignment_id=assignment_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AssignmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> None:
    try:
        await assignment_service.delete_assignment(
            actor_role=current_user.active_role,
            assignment_id=assignment_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AssignmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
