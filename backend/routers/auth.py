from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from repositories.role_repository import RoleRepository, SQLAlchemyRoleRepository
from repositories.user_repository import SQLAlchemyUserRepository, UserRepository
from schemas.auth import LoginRequest, LoginResponse
from services.auth_service import AuthService, InvalidCredentialsError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_role_repository(session: AsyncSession = Depends(get_db)) -> RoleRepository:
    return SQLAlchemyRoleRepository(session)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
) -> AuthService:
    return AuthService(user_repository, role_repository)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    try:
        session = await auth_service.login(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return LoginResponse(
        access_token=session.access_token,
        token_type=session.token_type,
        expires_in=session.expires_in,
        user_id=session.user_id,
        roles=session.roles,
    )
