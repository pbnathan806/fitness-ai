from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
    SQLAlchemyPasswordResetTokenRepository,
)
from repositories.role_repository import RoleRepository, SQLAlchemyRoleRepository
from repositories.user_repository import SQLAlchemyUserRepository, UserRepository
from schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from services.auth_service import AuthService, InvalidCredentialsError
from services.password_reset_service import (
    ConsolePasswordResetNotifier,
    InvalidResetTokenError,
    PasswordResetNotifier,
    PasswordResetService,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_role_repository(session: AsyncSession = Depends(get_db)) -> RoleRepository:
    return SQLAlchemyRoleRepository(session)


def get_password_reset_token_repository(
    session: AsyncSession = Depends(get_db),
) -> PasswordResetTokenRepository:
    return SQLAlchemyPasswordResetTokenRepository(session)


def get_password_reset_notifier() -> PasswordResetNotifier:
    return ConsolePasswordResetNotifier()


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
) -> AuthService:
    return AuthService(user_repository, role_repository)


def get_password_reset_service(
    user_repository: UserRepository = Depends(get_user_repository),
    token_repository: PasswordResetTokenRepository = Depends(
        get_password_reset_token_repository
    ),
    notifier: PasswordResetNotifier = Depends(get_password_reset_notifier),
) -> PasswordResetService:
    return PasswordResetService(user_repository, token_repository, notifier)


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


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service),
) -> ForgotPasswordResponse:
    await password_reset_service.request_password_reset(payload.email)
    return ForgotPasswordResponse()


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    payload: ResetPasswordRequest,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service),
) -> ResetPasswordResponse:
    try:
        await password_reset_service.reset_password(payload.token, payload.new_password)
    except InvalidResetTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return ResetPasswordResponse()
