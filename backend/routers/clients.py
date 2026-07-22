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
from repositories.role_repository import RoleRepository, SQLAlchemyRoleRepository
from repositories.user_repository import SQLAlchemyUserRepository, UserRepository
from schemas.client import (
    ClientCreateRequest,
    ClientResponse,
    ClientUpdateRequest,
    PaginatedClientsResponse,
)
from services.client_service import (
    ClientNotFoundError,
    ClientProfile,
    ClientService,
    EmailAlreadyExistsError,
    ForbiddenError,
)

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_role_repository(session: AsyncSession = Depends(get_db)) -> RoleRepository:
    return SQLAlchemyRoleRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_repository(session: AsyncSession = Depends(get_db)) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_client_service(
    client_repository: ClientRepository = Depends(get_client_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
) -> ClientService:
    return ClientService(
        client_repository, user_repository, role_repository, assignment_repository
    )


def _to_response(profile: ClientProfile) -> ClientResponse:
    return ClientResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=profile.email,
        first_name=profile.first_name,
        last_name=profile.last_name,
        phone_number=profile.phone_number,
        timezone=profile.timezone,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> ClientResponse:
    try:
        profile = await client_service.create_client(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            timezone=payload.timezone,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(profile)


@router.get("/me", response_model=ClientResponse, status_code=status.HTTP_200_OK)
async def get_current_client(
    current_user: CurrentUser = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> ClientResponse:
    try:
        profile = await client_service.get_current_client(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(profile)


@router.put("/me", response_model=ClientResponse, status_code=status.HTTP_200_OK)
async def update_current_client(
    payload: ClientUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> ClientResponse:
    try:
        profile = await client_service.update_current_client(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            timezone=payload.timezone,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(profile)


@router.get("/{client_id}", response_model=ClientResponse, status_code=status.HTTP_200_OK)
async def get_client(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> ClientResponse:
    try:
        profile = await client_service.get_client(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(profile)


@router.put("/{client_id}", response_model=ClientResponse, status_code=status.HTTP_200_OK)
async def update_client(
    client_id: uuid.UUID,
    payload: ClientUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> ClientResponse:
    try:
        profile = await client_service.update_client(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            timezone=payload.timezone,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(profile)


@router.get("", response_model=PaginatedClientsResponse, status_code=status.HTTP_200_OK)
async def list_clients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
) -> PaginatedClientsResponse:
    try:
        result = await client_service.list_clients(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            page=page,
            page_size=page_size,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    total_pages = (result.total + page_size - 1) // page_size if result.total else 0
    return PaginatedClientsResponse(
        items=[_to_response(profile) for profile in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )
